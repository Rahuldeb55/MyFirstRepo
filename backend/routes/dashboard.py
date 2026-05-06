"""
Dashboard Routes — Admin/Warden endpoints for live monitoring.
Provides: campus census, late alerts, dashboard stats, recent scans, analytics.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from database import get_db
from models import Student, MovementLog, Direction
from services.predictor import get_all_late_students
from services.cache import cache_get, cache_set

router = APIRouter(prefix="/api/admin", tags=["Dashboard"])


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get high-level dashboard statistics."""
    # Try cache first
    cached = cache_get("dashboard:stats")
    if cached:
        return cached

    total = db.query(Student).count()
    off_campus = db.query(Student).filter(Student.last_direction == Direction.OUT).count()
    on_campus = total - off_campus

    # Today's scans
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    scans_today = db.query(MovementLog).filter(
        MovementLog.timestamp >= today_start
    ).count()

    curfew_today = db.query(MovementLog).filter(
        MovementLog.timestamp >= today_start,
        MovementLog.is_curfew_violation == True
    ).count()

    late_alerts = len(get_all_late_students(db))

    result = {
        "total_students": total,
        "on_campus": on_campus,
        "off_campus": off_campus,
        "late_alerts": late_alerts,
        "scans_today": scans_today,
        "curfew_violations_today": curfew_today,
    }

    cache_set("dashboard:stats", result, ttl=15)
    return result


@router.get("/census")
def get_campus_census(db: Session = Depends(get_db)):
    """
    Live census: list of all students currently off-campus.
    Cached for performance with 30-second TTL.
    """
    cached = cache_get("census:live")
    if cached:
        return cached

    students_out = db.query(Student).filter(
        Student.last_direction == Direction.OUT
    ).all()

    total = db.query(Student).count()

    student_list = []
    for s in students_out:
        last_exit = db.query(MovementLog).filter(
            MovementLog.roll_no == s.roll_no,
            MovementLog.direction == Direction.OUT
        ).order_by(MovementLog.timestamp.desc()).first()

        exit_time = last_exit.timestamp if last_exit else None
        hours_out = None
        if exit_time:
            hours_out = round((datetime.utcnow() - exit_time).total_seconds() / 3600, 1)

        student_list.append({
            "roll_no": s.roll_no,
            "name": s.name,
            "course": s.course,
            "department": s.department,
            "hostel": s.hostel_name,
            "room": s.room_no,
            "exit_time": exit_time.isoformat() if exit_time else None,
            "hours_out": hours_out,
        })

    # Sort: longest out first
    student_list.sort(key=lambda x: -(x["hours_out"] or 0))

    result = {
        "total_students": total,
        "total_on_campus": total - len(students_out),
        "total_off_campus": len(students_out),
        "students_out": student_list,
    }

    cache_set("census:live", result, ttl=30)
    return result


@router.get("/late-alerts")
def get_late_alerts(db: Session = Depends(get_db)):
    """
    Get all students flagged as late returns.
    Uses ML prediction: T_pred = μ(T_history) + σ(T_history)
    Also unconditionally flags students out > 24 hours.
    """
    alerts = get_all_late_students(db)
    return {
        "count": len(alerts),
        "alerts": alerts,
    }


@router.get("/recent-scans")
def get_recent_scans(
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    """Get the most recent scan events for the activity feed."""
    logs = db.query(MovementLog).order_by(
        MovementLog.timestamp.desc()
    ).limit(limit).all()

    result = []
    for log in logs:
        student = db.query(Student).filter(Student.roll_no == log.roll_no).first()
        result.append({
            "roll_no": log.roll_no,
            "name": student.name if student else "Unknown",
            "course": student.course if student else "",
            "direction": log.direction.value if log.direction else "IN",
            "timestamp": log.timestamp.isoformat(),
            "is_late": log.is_late_return,
            "is_curfew_violation": log.is_curfew_violation,
            "guard_id": log.guard_id,
            "is_manual": log.is_manual_override,
        })

    return {"scans": result}


@router.get("/analytics/hourly")
def get_hourly_analytics(
    days: int = Query(default=7, le=30),
    db: Session = Depends(get_db),
):
    """Get hourly distribution of scans for chart visualization."""
    since = datetime.utcnow() - timedelta(days=days)

    logs = db.query(MovementLog).filter(
        MovementLog.timestamp >= since
    ).all()

    # Build hourly distribution
    hourly_in = [0] * 24
    hourly_out = [0] * 24
    for log in logs:
        hour = log.timestamp.hour
        if log.direction == Direction.IN:
            hourly_in[hour] += 1
        else:
            hourly_out[hour] += 1

    return {
        "period_days": days,
        "hours": list(range(24)),
        "entries": hourly_in,
        "exits": hourly_out,
    }


@router.get("/student/{roll_no}/history")
def get_student_history(
    roll_no: str,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    """Get a specific student's movement history."""
    student = db.query(Student).filter(Student.roll_no == roll_no.upper()).first()
    if not student:
        return {"error": "Student not found"}

    logs = db.query(MovementLog).filter(
        MovementLog.roll_no == roll_no.upper()
    ).order_by(MovementLog.timestamp.desc()).limit(limit).all()

    return {
        "student": {
            "roll_no": student.roll_no,
            "name": student.name,
            "course": student.course,
            "department": student.department,
            "hostel": student.hostel_name,
            "room": student.room_no,
            "current_status": student.last_direction.value,
            "avg_outing_hours": student.avg_outing_hours,
            "total_outings": student.total_outings,
        },
        "history": [
            {
                "direction": log.direction.value,
                "timestamp": log.timestamp.isoformat(),
                "guard_id": log.guard_id,
                "is_late": log.is_late_return,
                "is_curfew_violation": log.is_curfew_violation,
            }
            for log in logs
        ],
    }
