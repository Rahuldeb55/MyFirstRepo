"""
Student CRUD Routes — Admin endpoints for managing student records.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models import Student, Direction
from schemas import StudentCreate

router = APIRouter(prefix="/api/students", tags=["Students"])


@router.get("/")
def list_students(
    search: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    hostel: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
):
    """List students with optional filtering and pagination."""
    query = db.query(Student)

    if search:
        search_term = f"%{search.upper()}%"
        query = query.filter(
            (Student.roll_no.ilike(search_term)) |
            (Student.name.ilike(f"%{search}%"))
        )

    if department:
        query = query.filter(Student.department == department)

    if hostel:
        query = query.filter(Student.hostel_name == hostel)

    if status:
        direction = Direction.IN if status.upper() == "IN" else Direction.OUT
        query = query.filter(Student.last_direction == direction)

    total = query.count()
    students = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "students": [
            {
                "roll_no": s.roll_no,
                "name": s.name,
                "course": s.course,
                "department": s.department,
                "year": s.year,
                "hostel": s.hostel_name,
                "room": s.room_no,
                "status": s.last_direction.value if s.last_direction else "IN",
                "is_blacklisted": s.is_blacklisted,
            }
            for s in students
        ],
    }


@router.post("/")
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    """Add a new student to the database."""
    existing = db.query(Student).filter(Student.roll_no == student.roll_no.upper()).first()
    if existing:
        raise HTTPException(status_code=409, detail="Student with this Roll No already exists")

    new_student = Student(
        roll_no=student.roll_no.upper(),
        name=student.name,
        father_name=student.father_name,
        course=student.course,
        department=student.department,
        date_of_birth=student.date_of_birth,
        phone=student.phone,
        blood_group=student.blood_group,
        year=student.year,
        hostel_name=student.hostel_name,
        room_no=student.room_no,
        address=student.address,
        photo_url=student.photo_url,
        valid_upto=student.valid_upto,
        parent_contact=student.parent_contact,
        warden_name=student.warden_name,
        warden_contact=student.warden_contact,
    )
    db.add(new_student)
    db.commit()
    return {"message": "Student created", "roll_no": new_student.roll_no}


@router.put("/{roll_no}/blacklist")
def toggle_blacklist(
    roll_no: str,
    blacklist: bool = True,
    reason: str = "",
    db: Session = Depends(get_db),
):
    """Blacklist or un-blacklist a student."""
    student = db.query(Student).filter(Student.roll_no == roll_no.upper()).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student.is_blacklisted = blacklist
    student.blacklist_reason = reason if blacklist else ""
    db.commit()

    status = "blacklisted" if blacklist else "un-blacklisted"
    return {"message": f"Student {roll_no} has been {status}", "roll_no": roll_no}
