from datetime import date, datetime, time, timedelta

from .extensions import db
from .models import (
    Assignment,
    Attendance,
    Department,
    Grade,
    GradeLevel,
    LeaveRequest,
    Message,
    Notice,
    Parent,
    SchoolClass,
    Student,
    SystemSetting,
    Teacher,
    Timetable,
    User,
    letter_for_mark,
)


def make_user(email, role, password="Password123"):
    user = User(email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    return user


def make_teacher(email, role, full_name, department, staff_code, position):
    user = make_user(email, role)
    teacher = Teacher(user=user, full_name=full_name, department=department, staff_code=staff_code, position=position)
    db.session.add(teacher)
    return teacher


def seed_demo_data():
    db.session.add(SystemSetting(id=1))
    GradeLevel.ensure_defaults()
    Department.ensure_defaults()
    grade_8 = GradeLevel.query.filter_by(name="Grade 8").one()
    grade_10 = GradeLevel.query.filter_by(name="Grade 10").one()
    admin = make_user("admin@sms.example.com", "admin")
    headmaster = make_teacher("headmaster@sms.example.com", "headmaster", "Dr. Hla Min", "Leadership", "HM-001", "headmaster")
    dean = make_teacher("dean@sms.example.com", "dean", "Daw Thiri Win", "Academic Affairs", "D-001", "dean")
    teacher = make_teacher("teacher@sms.example.com", "teacher", "Daw May Hnin", "Science", "T-1001", "teacher")
    second_teacher = make_teacher("teacher2@sms.example.com", "teacher", "U Zaw Lin", "English", "T-1002", "teacher")
    headmaster.grade_levels.extend([grade_8, grade_10])
    dean.grade_levels.extend([grade_8, grade_10])
    teacher.grade_levels.append(grade_10)
    second_teacher.grade_levels.append(grade_8)

    parent_user = make_user("parent@sms.example.com", "parent")
    parent = Parent(
        user=parent_user,
        full_name="U Aung Ko",
        phone="+959123456789",
        address="No. 18, Inya Road, Yangon",
        relationship="Father",
        emergency_contact="+959987654321",
    )
    db.session.add(parent)

    second_parent_user = make_user("parent2@sms.example.com", "parent")
    second_parent = Parent(
        user=second_parent_user,
        full_name="Daw Ei Mon",
        phone="+959111222333",
        address="No. 7, Pyay Road, Yangon",
        relationship="Mother",
        emergency_contact="+959444555666",
    )
    db.session.add(second_parent)

    student_user = make_user("student@sms.example.com", "student")
    student = Student(
        user=student_user,
        full_name="Min Thu",
        year_group="Grade 10",
        date_of_birth=date(2010, 5, 14),
        student_code="S-1001",
        address="No. 18, Inya Road, Yangon",
        emergency_contact_name="U Aung Ko",
        emergency_contact_phone="+959987654321",
        medical_notes="No known allergies",
    )
    sibling_user = make_user("student2@sms.example.com", "student")
    sibling = Student(
        user=sibling_user,
        full_name="Hnin Thu",
        year_group="Grade 10",
        date_of_birth=date(2011, 2, 8),
        student_code="S-1002",
        address="No. 18, Inya Road, Yangon",
        emergency_contact_name="U Aung Ko",
        emergency_contact_phone="+959987654321",
        medical_notes="Asthma inhaler kept at office",
    )
    other_student_user = make_user("student3@sms.example.com", "student")
    other_student = Student(
        user=other_student_user,
        full_name="Aye Chan",
        year_group="Grade 8",
        date_of_birth=date(2012, 9, 20),
        student_code="S-2001",
        address="No. 7, Pyay Road, Yangon",
        emergency_contact_name="Daw Ei Mon",
        emergency_contact_phone="+959444555666",
        medical_notes="",
    )
    parent.students.extend([student, sibling])
    second_parent.students.append(other_student)

    maths = SchoolClass(teacher=teacher, name="Grade 10A Mathematics", subject="Mathematics", year_group="Grade 10", section="A", room="B203")
    science = SchoolClass(teacher=teacher, name="Grade 10A Science", subject="Science", year_group="Grade 10", section="A", room="Lab 1")
    english = SchoolClass(teacher=second_teacher, name="Grade 8A English", subject="English", year_group="Grade 8", section="A", room="C102")
    maths.students.extend([student, sibling])
    science.students.extend([student, sibling])
    english.students.append(other_student)
    db.session.add_all([admin, student, sibling, other_student, maths, science, english])
    db.session.flush()

    slots = [
        Timetable(school_class=maths, day_of_week="Monday", start_time=time(9), end_time=time(10), period="Period 1"),
        Timetable(school_class=science, day_of_week="Tuesday", start_time=time(10), end_time=time(11), period="Period 2"),
        Timetable(school_class=maths, day_of_week="Wednesday", start_time=time(11), end_time=time(12), period="Period 3"),
        Timetable(school_class=science, day_of_week="Friday", start_time=time(13), end_time=time(14), period="Period 5"),
        Timetable(school_class=english, day_of_week="Monday", start_time=time(10), end_time=time(11), period="Period 2"),
    ]
    assignments = [
        Assignment(school_class=maths, title="Algebra Quiz", max_mark=100, weight_pct=20, due_date=date.today() + timedelta(days=7)),
        Assignment(school_class=science, title="Forces Worksheet", max_mark=50, weight_pct=10, due_date=date.today() + timedelta(days=10)),
        Assignment(school_class=english, title="Reading Journal", max_mark=40, weight_pct=15, due_date=date.today() + timedelta(days=5)),
    ]
    db.session.add_all(slots + assignments)
    db.session.flush()

    for offset, status in enumerate(["present", "present", "late", "absent", "present"]):
        db.session.add(
            Attendance(
                school_class=maths,
                student=student,
                session_date=date.today() - timedelta(days=offset),
                status=status,
                note="" if status != "absent" else "Parent notified",
            )
        )
    for offset, status in enumerate(["absent", "present", "absent", "late"]):
        db.session.add(
            Attendance(
                school_class=science,
                student=sibling,
                session_date=date.today() - timedelta(days=offset),
                status=status,
            )
        )
    for offset, status in enumerate(["present", "absent", "present"]):
        db.session.add(
            Attendance(
                school_class=english,
                student=other_student,
                session_date=date.today() - timedelta(days=offset),
                status=status,
            )
        )

    for target_student, assignment, mark in [
        (student, assignments[0], 78),
        (student, assignments[1], 41),
        (sibling, assignments[0], 64),
        (other_student, assignments[2], 30),
    ]:
        db.session.add(
            Grade(
                assignment=assignment,
                student=target_student,
                mark=mark,
                letter_grade=letter_for_mark(mark, assignment.max_mark),
                feedback="Good progress. Keep practising exam-style questions.",
            )
        )

    db.session.add(
        Message(
            sender=teacher.user,
            recipient=parent_user,
            subject="Welcome to the parent portal",
            body="Please review Min Thu's recent attendance and assignment deadlines.",
        )
    )
    db.session.add(
        LeaveRequest(
            student=student,
            requested_by=parent_user,
            start_date=date.today() + timedelta(days=3),
            end_date=date.today() + timedelta(days=3),
            reason="Medical appointment",
            status="draft",
        )
    )
    db.session.add(
        Notice(
            title="Parent meeting week",
            body="Parent meetings will be scheduled by grade level next week.",
            audience="parents",
            status="approved",
            requested_by=dean.user,
            approved_by=headmaster.user,
            approved_at=datetime.utcnow(),
        )
    )
    db.session.add(
        Notice(
            title="Exam duty reminder",
            body="Teachers should confirm exam invigilation availability by Friday.",
            audience="teachers",
            status="pending",
            requested_by=dean.user,
        )
    )
    db.session.commit()
