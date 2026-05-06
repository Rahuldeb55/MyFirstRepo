"""
ML Predictor Service — Smart Security Layer
Predicts a student's expected return time using their historical outing data.

Formula: T_pred = μ(T_history) + σ(T_history)

If the current time exceeds T_pred, generate a "Soft Alert" for the warden.
"""
import math
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import Student, MovementLog, Direction


def calculate_predicted_return(student: Student) -> float:
    """
    Calculate predicted return time in hours from exit.
    Uses: T_pred = μ(T_history) + σ(T_history)
    
    Returns hours expected for return (from exit time).
    """
    avg = student.avg_outing_hours or 4.0
    std = student.std_outing_hours or 2.0
    return round(avg + std, 2)


def update_student_stats(db: Session, student: Student, outing_hours: float):
    """
    Update student's running mean and std deviation after a completed outing.
    Uses Welford's online algorithm for numerical stability.
    """
    n = student.total_outings + 1
    old_avg = student.avg_outing_hours or 4.0
    old_std = student.std_outing_hours or 2.0

    # Running mean
    new_avg = old_avg + (outing_hours - old_avg) / n

    # Running variance (simplified Welford)
    if n > 1:
        old_variance = old_std ** 2
        new_variance = old_variance + ((outing_hours - old_avg) * (outing_hours - new_avg) - old_variance) / n
        new_std = math.sqrt(max(new_variance, 0.1))  # Floor at 0.1
    else:
        new_std = 2.0  # Default for first outing

    student.avg_outing_hours = round(new_avg, 2)
    student.std_outing_hours = round(new_std, 2)
    student.total_outings = n
    db.add(student)


def check_late_return(student: Student, last_exit_time: datetime) -> dict:
    """
    Check if a student has been out longer than predicted.
    
    Returns:
        dict with is_late (bool), hours_overdue (float), predicted_hours (float)
    """
    if not last_exit_time:
        return {"is_late": False, "hours_overdue": 0, "predicted_hours": 0}

    predicted_hours = calculate_predicted_return(student)
    actual_hours = (datetime.utcnow() - last_exit_time).total_seconds() / 3600.0

    is_late = actual_hours > predicted_hours
    hours_overdue = max(0, round(actual_hours - predicted_hours, 1))

    return {
        "is_late": is_late,
        "hours_overdue": hours_overdue,
        "predicted_hours": predicted_hours,
        "actual_hours": round(actual_hours, 1),
    }


def get_all_late_students(db: Session) -> list:
    """
    Scan all students currently OUT and flag those exceeding their predicted return.
    Also flags anyone out > 24 hours unconditionally.
    """
    students_out = db.query(Student).filter(Student.last_direction == Direction.OUT).all()
    late_list = []

    for student in students_out:
        last_exit = db.query(MovementLog).filter(
            MovementLog.roll_no == student.roll_no,
            MovementLog.direction == Direction.OUT
        ).order_by(MovementLog.timestamp.desc()).first()

        if not last_exit:
            continue

        result = check_late_return(student, last_exit.timestamp)

        # Flag if: ML prediction exceeded OR > 24 hours out
        hours_out = result["actual_hours"]
        if result["is_late"] or hours_out > 24:
            late_list.append({
                "roll_no": student.roll_no,
                "name": student.name,
                "hostel": student.hostel_name,
                "course": student.course,
                "department": student.department,
                "hours_overdue": result["hours_overdue"],
                "hours_out": hours_out,
                "exit_time": last_exit.timestamp.isoformat(),
                "predicted_return": result["predicted_hours"],
                "warden_contact": student.warden_contact or "N/A",
                "severity": "CRITICAL" if hours_out > 24 else "WARNING",
            })

    # Sort by severity (CRITICAL first) then by hours overdue
    late_list.sort(key=lambda x: (-1 if x["severity"] == "CRITICAL" else 0, -x["hours_overdue"]))
    return late_list
