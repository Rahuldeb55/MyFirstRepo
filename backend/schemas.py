"""
Pydantic Schemas — Aligned with NIT Jalandhar ID Card format.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from enum import Enum


class DirectionEnum(str, Enum):
    IN = "IN"
    OUT = "OUT"


# --- Request Schemas ---

class ScanRequest(BaseModel):
    roll_no: str
    guard_id: Optional[str] = None
    manual_direction: Optional[DirectionEnum] = None


class GuardLogin(BaseModel):
    guard_id: str
    password: str


class StudentCreate(BaseModel):
    roll_no: str
    name: str
    father_name: str = ""
    course: str             # e.g. "B.Tech (CE)"
    department: str         # e.g. "Civil Engineering"
    date_of_birth: Optional[date] = None
    phone: str = ""
    blood_group: str = ""
    year: int = 1
    hostel_name: str
    room_no: str
    address: str = ""
    photo_url: str = ""
    valid_upto: str = ""
    parent_contact: str = ""
    warden_name: str = ""
    warden_contact: str = ""


# --- Response Schemas ---

class EmergencyContacts(BaseModel):
    father_name: str
    parent_contact: str
    warden_name: str
    warden_contact: str


class StudentProfile(BaseModel):
    roll_no: str
    name: str
    father_name: str
    course: str
    department: str
    year: int
    hostel: str
    room: str
    phone: str
    blood_group: str
    date_of_birth: Optional[str] = None
    photo_url: str
    valid_upto: str
    emergency: EmergencyContacts


class ScanResponse(BaseModel):
    status: str  # "SUCCESS", "DENIED", "ERROR"
    direction: Optional[str] = None
    reason: Optional[str] = None
    is_late_alert: bool = False
    is_curfew_violation: bool = False
    predicted_return_hours: Optional[float] = None
    student: Optional[StudentProfile] = None
    timestamp: Optional[str] = None


class CensusStudent(BaseModel):
    roll_no: str
    name: str
    course: str
    department: str
    hostel: str
    room: str
    exit_time: Optional[str] = None
    hours_out: Optional[float] = None


class CensusResponse(BaseModel):
    total_on_campus: int
    total_off_campus: int
    total_students: int
    students_out: list[CensusStudent]


class LateAlert(BaseModel):
    roll_no: str
    name: str
    hostel: str
    course: str
    hours_overdue: float
    exit_time: str
    predicted_return: Optional[float] = None
    warden_contact: str


class LateAlertResponse(BaseModel):
    count: int
    alerts: list[LateAlert]


class GuardTokenResponse(BaseModel):
    access_token: str
    guard_name: str
    gate: str


class DashboardStats(BaseModel):
    total_students: int
    on_campus: int
    off_campus: int
    late_alerts: int
    scans_today: int
    curfew_violations_today: int


class RecentScan(BaseModel):
    roll_no: str
    name: str
    direction: str
    timestamp: str
    is_late: bool
    is_curfew_violation: bool
