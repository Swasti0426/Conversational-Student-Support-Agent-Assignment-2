
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

POLICY_FILE = Path(__file__).parent / "data" / "student_policy.md"


def load_policy_sections():
    """Read the policy handbook and split it into sections."""
    if not POLICY_FILE.exists():
        raise FileNotFoundError("Student policy handbook was not found.")

    text = POLICY_FILE.read_text(encoding="utf-8")
    sections = []
    current_title = "General Policy"
    current_content = []

    for line in text.splitlines():
        if line.startswith("## "):
            if current_content:
                sections.append({
                    "title": current_title,
                    "content": "\n".join(current_content).strip()
                })

            current_title = line.replace("## ", "", 1).strip()
            current_content = []
        else:
            current_content.append(line)

    if current_content:
        sections.append({
            "title": current_title,
            "content": "\n".join(current_content).strip()
        })

    return [
        section for section in sections
        if section["content"]
    ]


def search_policy(question, top_k=2):
    """Find the policy sections most relevant to a question."""
    sections = load_policy_sections()

    if not question or not question.strip():
        return []

    documents = [
        section["title"] + " " + section["content"]
        for section in sections
    ]

    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2)
    )

    try:
        document_vectors = vectorizer.fit_transform(documents)
        question_vector = vectorizer.transform([question])
    except ValueError:
        return []

    scores = cosine_similarity(
        question_vector,
        document_vectors
    ).flatten()

    ranked_indices = scores.argsort()[::-1]
    results = []

    for index in ranked_indices[:top_k]:
        if scores[index] > 0:
            results.append({
                "title": sections[index]["title"],
                "content": sections[index]["content"],
                "score": round(float(scores[index]), 3)
            })

    return results


if __name__ == "__main__":
    question = "What should I do if my fee payment portal fails?"
    results = search_policy(question)

    print("Question:", question)

    if results:
        for result in results:
            print("\nPolicy section:", result["title"])
            print("Relevance score:", result["score"])
            print(result["content"])
    else:
        print("No relevant policy information was found.")
