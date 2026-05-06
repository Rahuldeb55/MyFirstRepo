"""
Scanner Routes — Core barcode scan endpoint.
Handles: Barcode → Decode → Validate → Direction → Log → Response
Target latency: < 1.5 seconds scan-to-display.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import Student, MovementLog, Direction
from schemas import ScanRequest, ScanResponse, StudentProfile, EmergencyContacts
from services.direction import determine_direction
from services.validation import validate_scan
from services.predictor import (
    calculate_predicted_return,
    update_student_stats,
    check_late_return,
)
from services.cache import add_student_out, remove_student_out, invalidate_census

router = APIRouter(prefix="/api", tags=["Scanner"])


@router.post("/scan", response_model=ScanResponse)
def process_scan(request: ScanRequest, db: Session = Depends(get_db)):
    """
    Core scanning endpoint.
    Flow: Barcode Scan → Extract String → API Lookup → Profile Display
    """
    roll_no = request.roll_no.strip().upper()

    # Step 1: Lookup student in database (Source of Truth)
    student = db.query(Student).filter(Student.roll_no == roll_no).first()
    if not student:
        return ScanResponse(
            status="ERROR",
            reason=f"Student with Roll No '{roll_no}' not found in database.",
        )

    # Step 2: Determine direction (auto-toggle or manual override)
    new_direction = determine_direction(
        student.last_direction,
        request.manual_direction,
    )

    # Step 3: Validate (blacklist, curfew)
    validation = validate_scan(student, new_direction.value)
    if not validation["allowed"]:
        # Log the denied attempt
        log = MovementLog(
            roll_no=roll_no,
            direction=new_direction,
            guard_id=request.guard_id,
            is_manual_override=request.manual_direction is not None,
            is_curfew_violation=validation["is_curfew_violation"],
            notes=f"DENIED: {validation['reason']}",
        )
        db.add(log)
        db.commit()

        return ScanResponse(
            status="DENIED",
            direction=new_direction.value,
            reason=validation["reason"],
            is_curfew_violation=validation["is_curfew_violation"],
            student=_build_student_profile(student),
        )

    # Step 4: Check for late return (if coming back IN)
    is_late = False
    predicted_return = None
    if new_direction == Direction.IN and student.last_direction == Direction.OUT:
        last_exit = db.query(MovementLog).filter(
            MovementLog.roll_no == roll_no,
            MovementLog.direction == Direction.OUT,
        ).order_by(MovementLog.timestamp.desc()).first()

        if last_exit:
            late_info = check_late_return(student, last_exit.timestamp)
            is_late = late_info["is_late"]
            predicted_return = late_info["predicted_hours"]

            # Update ML stats with actual outing duration
            outing_hours = late_info["actual_hours"]
            update_student_stats(db, student, outing_hours)

    # Step 5: Create movement log
    log = MovementLog(
        roll_no=roll_no,
        direction=new_direction,
        guard_id=request.guard_id,
        is_manual_override=request.manual_direction is not None,
        is_curfew_violation=False,
        is_late_return=is_late,
    )
    db.add(log)

    # Step 6: Update student's last direction
    student.last_direction = new_direction
    student.last_scan_time = datetime.utcnow()
    db.add(student)
    db.commit()

    # Step 7: Update Redis cache
    if new_direction == Direction.OUT:
        predicted_return = calculate_predicted_return(student)
        add_student_out(roll_no, {
            "name": student.name,
            "hostel": student.hostel_name,
            "exit_time": datetime.utcnow().isoformat(),
        })
    else:
        remove_student_out(roll_no)

    invalidate_census()

    return ScanResponse(
        status="SUCCESS",
        direction=new_direction.value,
        is_late_alert=is_late,
        is_curfew_violation=False,
        predicted_return_hours=predicted_return,
        student=_build_student_profile(student),
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/check-status/{roll_no}")
def check_status(roll_no: str, db: Session = Depends(get_db)):
    """
    Check a student's current status without creating a scan event.
    Used for quick lookups.
    """
    student = db.query(Student).filter(Student.roll_no == roll_no.upper()).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    last_log = db.query(MovementLog).filter(
        MovementLog.roll_no == student.roll_no,
    ).order_by(MovementLog.timestamp.desc()).first()

    return {
        "roll_no": student.roll_no,
        "name": student.name,
        "current_status": student.last_direction.value if student.last_direction else "IN",
        "last_scan": last_log.timestamp.isoformat() if last_log else None,
        "is_blacklisted": student.is_blacklisted,
        "hostel": student.hostel_name,
        "room": student.room_no,
    }


def _build_student_profile(student: Student) -> StudentProfile:
    """Helper to build a StudentProfile response from ORM model."""
    return StudentProfile(
        roll_no=student.roll_no,
        name=student.name,
        father_name=student.father_name or "",
        course=student.course or "",
        department=student.department,
        year=student.year,
        hostel=student.hostel_name,
        room=student.room_no,
        phone=student.phone or "",
        blood_group=student.blood_group or "",
        date_of_birth=student.date_of_birth.isoformat() if student.date_of_birth else None,
        photo_url=student.photo_url or "",
        valid_upto=student.valid_upto or "",
        emergency=EmergencyContacts(
            father_name=student.father_name or "",
            parent_contact=student.parent_contact or student.phone or "",
            warden_name=student.warden_name or "",
            warden_contact=student.warden_contact or "",
        ),
    )

