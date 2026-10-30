
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
INDEX_DIR = BASE_DIR / "knowledge_base" / "index"

COLLECTION_NAME = "student_support_knowledge"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_model = None
_collection = None


# --------------------------------------------------
# LOAD THE EXISTING INDEX
# --------------------------------------------------

def get_collection():
    """Open the existing local knowledge index."""

    global _collection

    if _collection is None:
        client = chromadb.PersistentClient(path=str(INDEX_DIR))

        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    return _collection


def get_model():
    """Load the embedding model only once."""

    global _model

    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)

    return _model


# --------------------------------------------------
# SEARCH KNOWLEDGE BASE
# --------------------------------------------------

def search_knowledge(question, top_k=5):
    """
    Search indexed documents and return relevant passages.

    Returns an empty list if no useful indexed data exists.
    """

    question = str(question).strip()

    if not question:
        return []

    collection = get_collection()

    if collection.count() == 0:
        return []

    model = get_model()

    query_embedding = model.encode(
        question,
        normalize_embeddings=True,
    ).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    passages = []

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for document, metadata, distance in zip(
        documents, metadatas, distances
    ):
        passages.append({
            "text": document,
            "source": metadata.get("source", "Unknown source"),
            "page": metadata.get("page"),
            "row": metadata.get("row"),
            "sheet": metadata.get("sheet"),
            "distance": float(distance),
        })

    return passages


# --------------------------------------------------
# FORMAT SEARCH RESULTS
# --------------------------------------------------

def format_context(passages):
    """Format retrieved passages for the AI agent."""

    if not passages:
        return "No relevant information was found in the local knowledge base."

    sections = []

    for index, passage in enumerate(passages, start=1):
        source = passage["source"]

        location = []

        if passage.get("page") is not None:
            location.append(f"page {passage['page']}")

        if passage.get("sheet"):
            location.append(f"sheet {passage['sheet']}")

        if passage.get("row") is not None:
            location.append(f"row {passage['row']}")

        if location:
            source += " (" + ", ".join(location) + ")"

        sections.append(
            f"[Source {index}: {source}]\n{passage['text']}"
        )

    return "\n\n".join(sections)


# --------------------------------------------------
# QUICK TEST
# --------------------------------------------------

if __name__ == "__main__":
    print("Student Support Knowledge Search")
    print("-" * 40)

    question = input("Enter a question to search your data: ").strip()

    try:
        passages = search_knowledge(question, top_k=5)

        if not passages:
            print("\nNo indexed information was found.")
        else:
            print(f"\nFound {len(passages)} passages:\n")
            print(format_context(passages))

    except Exception as error:
        print(f"\nSearch failed: {error}")
