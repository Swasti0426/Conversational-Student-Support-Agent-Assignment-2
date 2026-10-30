
import json
from pathlib import Path


# Find the data folder relative to this Python file.
DATA_FILE = Path(__file__).parent / "data" / "students.json"


def load_students():
    """Load fictional student records from the JSON file."""

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        students = data.get("students", [])

        if not isinstance(students, list):
            raise ValueError("The students field must be a list.")

        return students

    except FileNotFoundError as error:
        raise RuntimeError(
            f"Student data file not found: {DATA_FILE}"
        ) from error

    except json.JSONDecodeError as error:
        raise RuntimeError(
            "students.json contains invalid JSON."
        ) from error


def find_student(student_id):
    """Find a student using their student ID."""

    if not isinstance(student_id, str) or not student_id.strip():
        return None

    student_id = student_id.strip().upper()

    students = load_students()

    for student in students:
        if student.get("student_id", "").upper() == student_id:
            return student

    return None


def get_fee_status(student_id):
    """Return the fee details for a student."""

    student = find_student(student_id)

    if student is None:
        return {
            "success": False,
            "error": "Student not found. Please check the student ID."
        }

    try:
        total_fee = float(student["total_fee"])
        paid_amount = float(student["paid_amount"])

        if total_fee < 0 or paid_amount < 0 or paid_amount > total_fee:
            raise ValueError("Invalid fee amounts.")

    except (KeyError, TypeError, ValueError):
        return {
            "success": False,
            "error": "The student's fee record is invalid."
        }

    return {
        "success": True,
        "student_id": student["student_id"],
        "name": student["name"],
        "fee_status": student["fee_status"],
        "total_fee": total_fee,
        "paid_amount": paid_amount,
        "remaining_fee": total_fee - paid_amount
    }


def check_scholarship_status(student_id):
    """Return the scholarship status for a student."""

    student = find_student(student_id)

    if student is None:
        return {
            "success": False,
            "error": "Student not found. Please check the student ID."
        }

    if not student.get("scholarship_status"):
        return {
            "success": False,
            "error": "Scholarship status is missing from the student record."
        }

    return {
        "success": True,
        "student_id": student["student_id"],
        "name": student["name"],
        "scholarship_status": student["scholarship_status"]
    }
