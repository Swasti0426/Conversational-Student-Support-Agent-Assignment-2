
from pathlib import Path
import hashlib
import json
import pymupdf

import fitz  # PyMuPDF
import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

DOCUMENTS_DIR = BASE_DIR / "knowledge_base" / "documents"
TABLES_DIR = BASE_DIR / "knowledge_base" / "tables"
INDEX_DIR = BASE_DIR / "knowledge_base" / "index"

MANIFEST_FILE = INDEX_DIR / "manifest.json"
COLLECTION_NAME = "student_support_knowledge"

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
BATCH_SIZE = 64

# Local embedding model. Downloads on first use.
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


# --------------------------------------------------
# CREATE FOLDERS
# --------------------------------------------------

for folder in (DOCUMENTS_DIR, TABLES_DIR, INDEX_DIR):
    folder.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# LOAD LOCAL EMBEDDING MODEL
# --------------------------------------------------

def load_embedding_model():
    print("Loading the local embedding model...")
    return SentenceTransformer(EMBEDDING_MODEL)


# --------------------------------------------------
# TEXT CHUNKING
# --------------------------------------------------

def split_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks for retrieval."""

    text = " ".join(str(text).split())

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap

    return chunks


# --------------------------------------------------
# READ PDF FILES
# --------------------------------------------------


def read_pdf(path):
    """Extract text page by page from a PDF."""

    documents = []

    try:
        with pymupdf.open(path) as pdf:
            for page_number, page in enumerate(pdf, start=1):
                text = page.get_text("text").strip()

                if text:
                    documents.append({
                        "text": text,
                        "source": str(path.relative_to(BASE_DIR)),
                        "file_name": path.name,
                        "file_type": "pdf",
                        "page": page_number,
                    })

    except Exception as error:
        print(f"Could not read PDF {path.name}: {error}")

    return documents



# --------------------------------------------------
# READ CSV FILES
# --------------------------------------------------

def read_csv(path):
    """Convert CSV rows into searchable text."""

    documents = []

    try:
        # Read in chunks so large CSVs do not need to load at once.
        for frame in pd.read_csv(
            path,
            dtype=str,
            keep_default_na=False,
            chunksize=5000,
            encoding="utf-8",
            encoding_errors="replace",
        ):
            for row_number, row in enumerate(
                frame.to_dict(orient="records"), start=1
            ):
                content = " | ".join(
                    f"{key}: {value}"
                    for key, value in row.items()
                    if str(value).strip()
                )

                if content.strip():
                    documents.append({
                        "text": content,
                        "source": str(path.relative_to(BASE_DIR)),
                        "file_name": path.name,
                        "file_type": "csv",
                        "row": row_number,
                    })

    except Exception as error:
        print(f"Could not read CSV {path.name}: {error}")

    return documents


# --------------------------------------------------
# READ EXCEL FILES
# --------------------------------------------------


def read_excel(path):
    """Read all sheets in an Excel workbook."""

    documents = []

    try:
        workbook = pd.ExcelFile(path, engine="openpyxl")

        for sheet_name in workbook.sheet_names:
            dataframe = pd.read_excel(
                workbook,
                sheet_name=sheet_name,
                dtype=str,
                keep_default_na=False,
                engine="openpyxl",
            )

            for row_number, row in enumerate(
                dataframe.to_dict(orient="records"),
                start=2,
            ):
                content = " | ".join(
                    f"{key}: {value}"
                    for key, value in row.items()
                    if str(value).strip()
                )

                if content.strip():
                    documents.append({
                        "text": content,
                        "source": str(path.relative_to(BASE_DIR)),
                        "file_name": path.name,
                        "file_type": "excel",
                        "sheet": sheet_name,
                        "row": row_number,
                    })

    except Exception as error:
        print(f"Could not read Excel file {path.name}: {error}")

    return documents



# --------------------------------------------------
# COLLECT DATA FILES
# --------------------------------------------------

def discover_files():
    files = []

    for folder in (DOCUMENTS_DIR, TABLES_DIR):
        for path in folder.rglob("*"):
            if not path.is_file():
                continue

            if path.name.startswith("~$"):
                continue

            if path.suffix.lower() in {
                ".pdf", ".csv", ".xlsx", ".xlsm"
            }:
                files.append(path)

    return sorted(files)


# --------------------------------------------------
# FILE HASHING
# --------------------------------------------------

def file_hash(path):
    """Identify whether a file has changed."""

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()


# --------------------------------------------------
# BUILD CHUNKS AND METADATA
# --------------------------------------------------

def prepare_chunks(path, records):
    """Attach source information to every text chunk."""

    prepared = []

    for record in records:
        for chunk_number, chunk in enumerate(
            split_text(record["text"])
        ):
            metadata = {
                key: str(value)
                for key, value in record.items()
                if key != "text"
            }

            metadata["chunk"] = str(chunk_number)

            chunk_id = hashlib.sha256(
                (
                    metadata["source"]
                    + "|"
                    + str(metadata.get("page", ""))
                    + "|"
                    + str(metadata.get("row", ""))
                    + "|"
                    + str(metadata.get("sheet", ""))
                    + "|"
                    + str(chunk_number)
                    + "|"
                    + chunk
                ).encode("utf-8")
            ).hexdigest()

            prepared.append({
                "id": chunk_id,
                "text": chunk,
                "metadata": metadata,
            })

    return prepared


# --------------------------------------------------
# MAIN INGESTION PIPELINE
# --------------------------------------------------

def main():
    client = chromadb.PersistentClient(path=str(INDEX_DIR))

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    if MANIFEST_FILE.exists():
        try:
            manifest = json.loads(
                MANIFEST_FILE.read_text(encoding="utf-8")
            )
        except (json.JSONDecodeError, OSError):
            manifest = {}
    else:
        manifest = {}

    files = discover_files()

    print(f"\nFound {len(files)} supported files.")

    if not files:
        print("Add PDFs to documents/ and CSV or Excel files to tables/.")
        return

    model = load_embedding_model()
    current_paths = set()

    for file_number, path in enumerate(files, start=1):
        relative_path = str(path.relative_to(BASE_DIR))
        current_paths.add(relative_path)

        print(f"\n[{file_number}/{len(files)}] Processing {path.name}")

        try:
            digest = file_hash(path)
        except OSError as error:
            print(f"Could not hash {path.name}: {error}")
            continue

        old_entry = manifest.get(relative_path)

        # Skip unchanged files.
        if (
            old_entry
            and old_entry.get("hash") == digest
            and old_entry.get("status") == "indexed"
        ):
            print("Unchanged - skipping.")
            continue

        suffix = path.suffix.lower()

        if suffix == ".pdf":
            records = read_pdf(path)
        elif suffix == ".csv":
            records = read_csv(path)
        else:
            records = read_excel(path)

        prepared = prepare_chunks(path, records)

        # Delete the old version only after the replacement is prepared.
        old_ids = (
            old_entry.get("ids", [])
            if old_entry
            else []
        )

        if not prepared:
            print("No readable text found.")
            continue

        ids = [item["id"] for item in prepared]
        texts = [item["text"] for item in prepared]
        metadatas = [item["metadata"] for item in prepared]

        try:
            for start in range(0, len(prepared), BATCH_SIZE):
                end = start + BATCH_SIZE

                batch_ids = ids[start:end]
                batch_texts = texts[start:end]
                batch_metadata = metadatas[start:end]

                embeddings = model.encode(
                    batch_texts,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                ).tolist()

                collection.upsert(
                    ids=batch_ids,
                    documents=batch_texts,
                    metadatas=batch_metadata,
                    embeddings=embeddings,
                )

            # Remove chunks that no longer belong to this file.
            obsolete_ids = sorted(set(old_ids) - set(ids))

            if obsolete_ids:
                for start in range(0, len(obsolete_ids), BATCH_SIZE):
                    collection.delete(
                        ids=obsolete_ids[start:start + BATCH_SIZE]
                    )

            manifest[relative_path] = {
                "hash": digest,
                "status": "indexed",
                "ids": ids,
            }

            MANIFEST_FILE.write_text(
                json.dumps(manifest, indent=2),
                encoding="utf-8",
            )

            print(f"Indexed {len(prepared)} chunks.")

        except Exception as error:
            print(f"Indexing failed for {path.name}: {error}")
            print("You can rerun the script after resolving the issue.")

    # Remove indexed files that have been deleted from the input folders.
    deleted_paths = set(manifest) - current_paths

    for relative_path in deleted_paths:
        old_entry = manifest.pop(relative_path, {})

        old_ids = old_entry.get("ids", [])

        for start in range(0, len(old_ids), BATCH_SIZE):
            collection.delete(
                ids=old_ids[start:start + BATCH_SIZE]
            )

        print(f"Removed deleted file from index: {relative_path}")

    MANIFEST_FILE.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    print("\nIngestion finished.")
    print(f"Total indexed chunks: {collection.count()}")
    print(f"Local index: {INDEX_DIR}")


if __name__ == "__main__":
    main()
