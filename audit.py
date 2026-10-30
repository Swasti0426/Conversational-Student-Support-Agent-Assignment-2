
import json
from pathlib import Path
from datetime import datetime

AUDIT_FILE = Path(__file__).parent / "logs" / "audit_log.jsonl"


def record_audit(
    student_id,
    action,
    requested_action,
    permission,
    approval_status,
    result,
):
    """Record important actions for auditing."""

    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "student_id": student_id or "UNAUTHENTICATED",
        "action": action,
        "requested_action": requested_action,
        "permission": permission,
        "approval_status": approval_status,
        "result": result,
    }

    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(AUDIT_FILE, "a", encoding="utf-8") as file:
        file.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return entry
