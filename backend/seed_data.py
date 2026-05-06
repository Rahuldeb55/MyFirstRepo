"""
Database Seeder — NIT Jalandhar student data.
Roll No format: 8-digit (YY-Branch-Serial), e.g., 23102060
Barcode: Code 39 encoding (*23102060*)
Run: python seed_data.py
"""
import sys
import os
import random
from datetime import datetime, timedelta, date

sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, engine, Base
from models import Student, MovementLog, Guard, Direction
from routes.auth import hash_password

# NIT Jalandhar branch codes and course mapping
COURSES = {
    "10": ("B.Tech (CE)", "Civil Engineering"),
    "11": ("B.Tech (CSE)", "Computer Science & Engineering"),
    "12": ("B.Tech (ECE)", "Electronics & Communication Engineering"),
    "13": ("B.Tech (EE)", "Electrical Engineering"),
    "14": ("B.Tech (ICE)", "Instrumentation & Control Engineering"),
    "15": ("B.Tech (IPE)", "Industrial & Production Engineering"),
    "16": ("B.Tech (IT)", "Information Technology"),
    "17": ("B.Tech (ME)", "Mechanical Engineering"),
    "18": ("B.Tech (TT)", "Textile Technology"),
    "19": ("B.Tech (BT)", "Biotechnology"),
}

HOSTELS = [
    ("Mega Hostel", "Dr. Anil Sharma", "9876543210"),
    ("Hostel No. 7", "Dr. Priya Singh", "9876543211"),
    ("Hostel No. 5", "Dr. Rajesh Verma", "9876543212"),
    ("Hostel No. 3", "Dr. Amit Gupta", "9876543213"),
    ("Girls Hostel", "Dr. Meera Nair", "9876543214"),
    ("PG Hostel", "Dr. Sunil Kumar", "9876543215"),
]

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

# Realistic NIT Jalandhar students
STUDENTS = [
    # (roll_no, name, father_name, branch_code, year, dob, phone, blood, hostel_idx, address)
    ("23102060", "Ravishankar Kumar Sharma", "Gupteshwar Sharma", "10", 1, "2005-02-09", "8226875441", "O+", 0, "Agiaon, Distt. Bhojpur, Bihar - 802201"),
    ("23112045", "Aarav Malhotra", "Suresh Malhotra", "11", 1, "2005-06-15", "9876501234", "B+", 0, "Sector 22, Chandigarh - 160022"),
    ("23122031", "Priya Kaur", "Harpreet Singh", "12", 1, "2005-03-22", "9876502345", "A+", 4, "Model Town, Jalandhar - 144003"),
    ("23112078", "Vikram Patel", "Dinesh Patel", "11", 1, "2004-11-08", "9876503456", "AB+", 1, "Vastrapur, Ahmedabad, Gujarat - 380015"),
    ("23172055", "Ananya Reddy", "Krishna Reddy", "17", 1, "2005-01-30", "9876504567", "O-", 4, "Banjara Hills, Hyderabad - 500034"),
    ("22112034", "Rohit Kumar", "Manoj Kumar", "11", 2, "2004-07-19", "9876505678", "B-", 2, "Rajouri Garden, New Delhi - 110027"),
    ("22132019", "Sneha Gupta", "Ramesh Gupta", "13", 2, "2004-04-12", "9876506789", "A-", 4, "Gomti Nagar, Lucknow - 226010"),
    ("22162042", "Arjun Thakur", "Vijay Thakur", "16", 2, "2003-12-25", "9876507890", "O+", 3, "Mall Road, Shimla - 171001"),
    ("22142063", "Deepika Joshi", "Prakash Joshi", "14", 2, "2004-08-05", "9876508901", "B+", 4, "Civil Lines, Jaipur - 302006"),
    ("21112015", "Karthik Nair", "Rajesh Nair", "11", 3, "2003-05-17", "9876509012", "A+", 1, "Ernakulam, Kochi, Kerala - 682011"),
    ("21172028", "Rahul Deshmukh", "Sunil Deshmukh", "17", 3, "2003-09-03", "9876510123", "AB-", 2, "Kothrud, Pune - 411038"),
    ("21122041", "Ishita Singh", "Arun Singh", "12", 3, "2003-02-14", "9876511234", "O+", 4, "Hazratganj, Lucknow - 226001"),
    ("21162057", "Neha Kapoor", "Mohan Kapoor", "16", 3, "2002-11-28", "9876512345", "B+", 5, "Sector 17, Chandigarh - 160017"),
    ("21182033", "Siddharth Rao", "Venkat Rao", "18", 3, "2003-06-21", "9876513456", "A-", 3, "Jubilee Hills, Hyderabad - 500033"),
    ("21192046", "Kavya Sharma", "Anil Sharma", "19", 3, "2003-01-10", "9876514567", "O-", 4, "Aundh, Pune - 411007"),
]


def seed():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # --- Guards ---
        guards = [
            Guard(id="GUARD001", name="Ramesh Kumar", password_hash=hash_password("guard123"), gate_assigned="Main Gate", is_active=True),
            Guard(id="GUARD002", name="Suresh Patel", password_hash=hash_password("guard123"), gate_assigned="Back Gate", is_active=True),
        ]
        for g in guards:
            db.add(g)

        # --- Students ---
        for i, (roll, name, father, branch, year, dob, phone, blood, hostel_idx, addr) in enumerate(STUDENTS):
            course, dept = COURSES[branch]
            hostel_name, warden_name, warden_contact = HOSTELS[hostel_idx]
            room = f"{'ABCDE'[random.randint(0,4)]}-{random.randint(100, 450)}"

            student = Student(
                roll_no=roll,
                name=name,
                father_name=father,
                course=course,
                department=dept,
                date_of_birth=date.fromisoformat(dob),
                phone=phone,
                blood_group=blood,
                year=year,
                hostel_name=hostel_name,
                room_no=room,
                address=addr,
                valid_upto="June 2027",
                is_blacklisted=(roll == "22132019"),  # Sneha Gupta blacklisted
                blacklist_reason="Disciplinary action - repeated curfew violations" if roll == "22132019" else "",
                last_direction=Direction.IN,
                parent_contact=phone,  # Father's phone same as emergency
                warden_name=warden_name,
                warden_contact=warden_contact,
                avg_outing_hours=round(random.uniform(2.0, 8.0), 1),
                std_outing_hours=round(random.uniform(0.5, 3.0), 1),
                total_outings=random.randint(5, 50),
            )
            db.add(student)

        db.commit()
        print("Students seeded: 15 NIT Jalandhar students")

        # --- Movement Logs ---
        students = db.query(Student).all()
        now = datetime.utcnow()

        for student in students:
            num_logs = random.randint(10, 30)
            current_time = now - timedelta(days=30)
            current_dir = Direction.OUT

            for _ in range(num_logs):
                gap = timedelta(hours=random.uniform(1, 48))
                current_time += gap
                if current_time > now:
                    break

                log = MovementLog(
                    roll_no=student.roll_no,
                    direction=current_dir,
                    timestamp=current_time,
                    guard_id=random.choice(["GUARD001", "GUARD002"]),
                    is_manual_override=random.random() < 0.05,
                    is_late_return=random.random() < 0.1 if current_dir == Direction.IN else False,
                )
                db.add(log)
                current_dir = Direction.IN if current_dir == Direction.OUT else Direction.OUT

            # Set ~30% students as currently OUT
            if random.random() < 0.3:
                student.last_direction = Direction.OUT
                student.last_scan_time = now - timedelta(hours=random.uniform(0.5, 8))
                exit_log = MovementLog(
                    roll_no=student.roll_no, direction=Direction.OUT,
                    timestamp=student.last_scan_time, guard_id="GUARD001",
                )
                db.add(exit_log)

        db.commit()
        print("Movement logs seeded")

        # Summary
        total_s = db.query(Student).count()
        total_l = db.query(MovementLog).count()
        out_c = db.query(Student).filter(Student.last_direction == Direction.OUT).count()
        print(f"\nDatabase Summary:")
        print(f"  Students: {total_s}")
        print(f"  Movement Logs: {total_l}")
        print(f"  Currently Out: {out_c}")
        print(f"\nGuard Login: GUARD001 / guard123")
        print(f"Test barcode: *23102060* (Ravishankar Kumar Sharma)")

    except Exception as e:
        print(f"Error seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
