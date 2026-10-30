
import json
from pathlib import Path

MEMORY_FILE = Path(__file__).parent / "data" / "student_memory.json"

# Only these non-sensitive memory categories are allowed.
ALLOWED_MEMORY_KEYS = {
    "preferred_language",
    "preferred_response_style",
    "programme",
    "academic_interest",
}

MAX_VALUE_LENGTH = 150


def _normalise_student_id(student_id):
    """Validate and normalise a student's ID."""
    if not isinstance(student_id, str) or not student_id.strip():
        raise ValueError("A valid authenticated student ID is required.")

    return student_id.strip().upper()


def _load_all_memory():
    """Load the memory store safely."""
    if not MEMORY_FILE.exists():
        return {}

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data if isinstance(data, dict) else {}

    except (OSError, json.JSONDecodeError):
        return {}


def load_student_memory(student_id):
    """Return saved memories for one student only."""
    student_id = _normalise_student_id(student_id)
    all_memory = _load_all_memory()

    student_memory = all_memory.get(student_id, {})
    if not isinstance(student_memory, dict):
        return {}

    # Ignore any unsupported categories in an existing memory file.
    return {
        key: value
        for key, value in student_memory.items()
        if key in ALLOWED_MEMORY_KEYS and isinstance(value, str)
    }


def save_student_memory(student_id, key, value):
    """Save one explicitly requested, non-sensitive preference."""
    student_id = _normalise_student_id(student_id)

    if key not in ALLOWED_MEMORY_KEYS:
        return {
            "success": False,
            "message": "This type of information cannot be saved to memory.",
        }

    if not isinstance(value, str):
        return {
            "success": False,
            "message": "Memory value must be text.",
        }

    value = value.strip()

    if not value or len(value) > MAX_VALUE_LENGTH:
        return {
            "success": False,
            "message": "Please provide a short, valid preference.",
        }

    all_memory = _load_all_memory()

    student_memory = all_memory.get(student_id, {})
    if not isinstance(student_memory, dict):
        student_memory = {}

    student_memory[key] = value
    all_memory[student_id] = student_memory

    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump(all_memory, file, indent=4, ensure_ascii=False)

    return {
        "success": True,
        "message": "Your preference has been saved for future conversations.",
    }


def clear_student_memory(student_id):
    """Clear only the selected student's saved memories."""
    student_id = _normalise_student_id(student_id)
    all_memory = _load_all_memory()

    all_memory.pop(student_id, None)

    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump(all_memory, file, indent=4, ensure_ascii=False)

    return True


if __name__ == "__main__":
    # Basic local test using fictional student IDs.
    test_id = "STU_TEST_001"

    print(save_student_memory(
        test_id,
        "preferred_response_style",
        "simple explanations",
    ))

    print("Saved memory:", load_student_memory(test_id))

    clear_student_memory(test_id)
    print("After clearing:", load_student_memory(test_id))
