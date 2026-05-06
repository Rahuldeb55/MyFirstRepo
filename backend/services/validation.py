"""
Validation Service
Handles blacklist checks and curfew enforcement.
"""
from datetime import datetime, time
from models import Student


# Curfew window: 9 PM to 6 AM — students cannot EXIT during this window
CURFEW_START = time(21, 0)  # 9:00 PM
CURFEW_END = time(6, 0)     # 6:00 AM


def is_curfew_active(current_time: datetime = None) -> bool:
    """Check if curfew is currently in effect."""
    if current_time is None:
        current_time = datetime.now()
    t = current_time.time()
    # Curfew spans midnight: 9 PM → 6 AM
    return t >= CURFEW_START or t < CURFEW_END


def validate_scan(student: Student, direction: str, current_time: datetime = None) -> dict:
    """
    Validate whether a student is allowed to proceed with the scan.
    
    Returns:
        dict with keys:
            - allowed (bool): Whether the scan is permitted
            - reason (str): Denial reason if not allowed
            - is_curfew_violation (bool): Whether this is a curfew violation
    """
    # Check 1: Blacklist
    if student.is_blacklisted:
        return {
            "allowed": False,
            "reason": f"ACCESS DENIED: Student is blacklisted. Reason: {student.blacklist_reason or 'Contact admin.'}",
            "is_curfew_violation": False,
        }

    # Check 2: Curfew (only blocks EXIT, not re-entry)
    if direction == "OUT" and is_curfew_active(current_time):
        return {
            "allowed": False,
            "reason": "CURFEW ACTIVE: Exit is not permitted between 9:00 PM and 6:00 AM.",
            "is_curfew_violation": True,
        }

    return {
        "allowed": True,
        "reason": None,
        "is_curfew_violation": False,
    }
