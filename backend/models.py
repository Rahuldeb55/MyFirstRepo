"""
ORM Models — Aligned with NIT Jalandhar Student ID Card format.
Tables: Students, MovementLogs, Guards
"""
import enum
import datetime
from sqlalchemy import (
    Column, String, DateTime, Enum, Boolean, Integer, Float, ForeignKey, Text, Date
)
from sqlalchemy.orm import relationship
from database import Base


class Direction(str, enum.Enum):
    IN = "IN"
    OUT = "OUT"


class Student(Base):
    """
    Students table — keyed by roll_no (the Code 39 barcode on NIT Jalandhar ID cards).
    Fields match the physical ID card layout.
    
    ID Card Fields:
      Roll No, Name, Father's Name, Course, Date of Birth, Phone, Blood Group
    Barcode: Code 39 encoding of Roll No (e.g., *23102060*)
    """
    __tablename__ = "students"

    # --- Fields from the ID Card ---
    roll_no = Column(String(20), primary_key=True, index=True)  # e.g., "23102060"
    name = Column(String(100), nullable=False)
    father_name = Column(String(100), default="")
    course = Column(String(50), nullable=False)       # e.g., "B.Tech (CE)"
    department = Column(String(100), nullable=False)   # e.g., "Civil Engineering"
    date_of_birth = Column(Date, nullable=True)
    phone = Column(String(20), default="")             # Student's own phone
    blood_group = Column(String(5), default="")        # e.g., "O+", "B+", "AB-"

    # --- Hostel & Address ---
    year = Column(Integer, nullable=False, default=1)
    hostel_name = Column(String(50), nullable=False)
    room_no = Column(String(20), nullable=False)
    address = Column(String(255), default="")          # Home address from back of card
    photo_url = Column(String(500), default="")

    # --- Card Validity ---
    valid_upto = Column(String(20), default="")        # e.g., "June 2027"

    # --- Access Control ---
    is_blacklisted = Column(Boolean, default=False)
    blacklist_reason = Column(String(255), default="")
    last_direction = Column(Enum(Direction), default=Direction.IN)
    last_scan_time = Column(DateTime, nullable=True)

    # --- Emergency Contacts ---
    parent_contact = Column(String(20), default="")    # Father's phone (from card)
    warden_name = Column(String(100), default="")
    warden_contact = Column(String(20), default="")

    # --- ML Features ---
    avg_outing_hours = Column(Float, default=4.0)
    std_outing_hours = Column(Float, default=2.0)
    total_outings = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    movement_logs = relationship("MovementLog", back_populates="student", lazy="dynamic")


class MovementLog(Base):
    """
    MovementLogs table — immutable audit trail of every scan event.
    Non-editable server-side timestamps ensure integrity.
    """
    __tablename__ = "movement_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    roll_no = Column(String(20), ForeignKey("students.roll_no"), nullable=False, index=True)
    direction = Column(Enum(Direction), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    guard_id = Column(String(50), nullable=True)
    is_manual_override = Column(Boolean, default=False)
    is_curfew_violation = Column(Boolean, default=False)
    is_late_return = Column(Boolean, default=False)
    notes = Column(Text, default="")

    # Relationships
    student = relationship("Student", back_populates="movement_logs")


class Guard(Base):
    """
    Guards table — authentication and access control for gate operators.
    """
    __tablename__ = "guards"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    gate_assigned = Column(String(50), default="Main Gate")
    is_active = Column(Boolean, default=True)
    mac_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
