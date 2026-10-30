
import json
import uuid
from pathlib import Path
from datetime import datetime

from audit import record_audit


APPROVAL_FILE = (
    Path(__file__).parent / "logs" / "pending_approvals.jsonl"
)


def create_approval_request(student_id, action, details):
    """Create a pending sensitive-action request."""

    if not isinstance(student_id, str) or not student_id.strip():
        return {
            "success": False,
            "error": "Student authentication is required."
        }

    if action != "course_change":
        return {
            "success": False,
            "error": "This sensitive action is not supported."
        }

    if not isinstance(details, str) or not details.strip():
        return {
            "success": False,
            "error": "Please describe the requested course change."
        }

    request = {
        "request_id": str(uuid.uuid4()),
        "student_id": student_id.strip().upper(),
        "action": action,
        "details": details.strip()[:300],
        "status": "pending",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "decided_at": None,
        "reviewer_id": None,
    }

    APPROVAL_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(APPROVAL_FILE, "a", encoding="utf-8") as file:
        file.write(json.dumps(request) + "\n")

    record_audit(
        student_id=request["student_id"],
        action="course_change",
        requested_action="Request course change",
        permission="pending_review",
        approval_status="pending",
        result="not_executed",
    )

    return {
        "success": True,
        "message": "Request submitted and awaiting admin review.",
        "request_id": request["request_id"],
        "status": "pending",
    }


def decide_approval(
    request_id,
    approved,
    reviewer_id=None,
    reviewer_role=None,
):
    """Allow an authenticated admin to decide a pending request."""

    # Check reviewer authorization before reading or changing requests.
    if reviewer_role != "admin" or not isinstance(reviewer_id, str) or not reviewer_id.strip():
        record_audit(
            student_id=None,
            action="review_course_change",
            requested_action="Attempt to review a course-change request",
            permission="denied",
            approval_status="not_authorized",
            result="review_denied",
        )

        return {
            "success": False,
            "error": "Only an authenticated admin can review requests."
        }

    if not isinstance(request_id, str) or not request_id.strip():
        return {
            "success": False,
            "error": "A valid request ID is required."
        }

    if not isinstance(approved, bool):
        return {
            "success": False,
            "error": "Approval decision must be True or False."
        }

    if not APPROVAL_FILE.exists():
        return {
            "success": False,
            "error": "No approval requests were found."
        }

    requests = []

    with open(APPROVAL_FILE, "r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                requests.append(json.loads(line))

    target = next(
        (
            item for item in requests
            if item["request_id"] == request_id
        ),
        None,
    )

    if target is None:
        return {
            "success": False,
            "error": "Approval request not found."
        }

    if target["status"] != "pending":
        return {
            "success": False,
            "error": "This request has already been decided."
        }

    target["status"] = "approved" if approved else "rejected"
    target["decided_at"] = datetime.now().isoformat(timespec="seconds")
    target["reviewer_id"] = reviewer_id.strip()

    with open(APPROVAL_FILE, "w", encoding="utf-8") as file:
        for item in requests:
            file.write(json.dumps(item) + "\n")

    record_audit(
        student_id=target["student_id"],
        action="course_change",
        requested_action=(
            f"Review course-change request by admin {reviewer_id.strip()}"
        ),
        permission="allowed",
        approval_status=target["status"],
        result=(
            "approved_for_authorized_processing"
            if approved
            else "rejected_not_executed"
        ),
    )

    return {
        "success": True,
        "status": target["status"],
        "reviewer_id": reviewer_id.strip(),
        "executed": False,
        "message": (
            "Request approved for authorized processing. "
            "The course record has not been changed."
            if approved
            else "Request rejected. No change was executed."
        ),
    }
