from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


parent_student = db.Table(
    "parent_student",
    db.Column("parent_id", db.Integer, db.ForeignKey("parents.id"), primary_key=True),
    db.Column("student_id", db.Integer, db.ForeignKey("students.id"), primary_key=True),
)

class_student = db.Table(
    "class_student",
    db.Column("class_id", db.Integer, db.ForeignKey("classes.id"), primary_key=True),
    db.Column("student_id", db.Integer, db.ForeignKey("students.id"), primary_key=True),
)

teacher_grade = db.Table(
    "teacher_grade",
    db.Column("teacher_id", db.Integer, db.ForeignKey("teachers.id"), primary_key=True),
    db.Column("grade_id", db.Integer, db.ForeignKey("grade_levels.id"), primary_key=True),
)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    student = db.relationship("Student", back_populates="user", uselist=False, cascade="all, delete-orphan")
    parent = db.relationship("Parent", back_populates="user", uselist=False, cascade="all, delete-orphan")
    teacher = db.relationship("Teacher", back_populates="user", uselist=False, cascade="all, delete-orphan")

    sent_messages = db.relationship(
        "Message", foreign_keys="Message.sender_id", back_populates="sender", cascade="all, delete-orphan"
    )
    received_messages = db.relationship(
        "Message", foreign_keys="Message.recipient_id", back_populates="recipient", cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def display_name(self):
        profile = self.student or self.parent or self.teacher
        return getattr(profile, "full_name", self.email)


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    year_group = db.Column(db.String(20), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    student_code = db.Column(db.String(30), unique=True, nullable=False)
    address = db.Column(db.String(255), default="")
    emergency_contact_name = db.Column(db.String(120), default="")
    emergency_contact_phone = db.Column(db.String(40), default="")
    medical_notes = db.Column(db.String(255), default="")

    user = db.relationship("User", back_populates="student")
    parents = db.relationship("Parent", secondary=parent_student, back_populates="students")
    classes = db.relationship("SchoolClass", secondary=class_student, back_populates="students")
    attendance = db.relationship("Attendance", back_populates="student", cascade="all, delete-orphan")
    grades = db.relationship("Grade", back_populates="student", cascade="all, delete-orphan")
    leave_requests = db.relationship("LeaveRequest", back_populates="student", cascade="all, delete-orphan")

    @property
    def attendance_percentage(self):
        marked = [row for row in self.attendance if row.status in {"present", "late", "absent"}]
        if not marked:
            return 100.0
        attended = [row for row in marked if row.status in {"present", "late"}]
        return round((len(attended) / len(marked)) * 100, 1)


class Parent(db.Model):
    __tablename__ = "parents"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(40))
    address = db.Column(db.String(255), default="")
    relationship = db.Column(db.String(60), default="Parent")
    emergency_contact = db.Column(db.String(40), default="")

    user = db.relationship("User", back_populates="parent")
    students = db.relationship("Student", secondary=parent_student, back_populates="parents")


class Teacher(db.Model):
    __tablename__ = "teachers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(80), nullable=False)
    staff_code = db.Column(db.String(30), unique=True, nullable=False)
    position = db.Column(db.String(30), default="teacher", nullable=False)

    user = db.relationship("User", back_populates="teacher")
    classes = db.relationship("SchoolClass", back_populates="teacher")
    grade_levels = db.relationship("GradeLevel", secondary=teacher_grade, back_populates="teachers")


class SchoolClass(db.Model):
    __tablename__ = "classes"

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    subject = db.Column(db.String(80), nullable=False)
    year_group = db.Column(db.String(20), nullable=False)
    room = db.Column(db.String(30), nullable=False)
    section = db.Column(db.String(20), default="A", nullable=False)

    teacher = db.relationship("Teacher", back_populates="classes")
    students = db.relationship("Student", secondary=class_student, back_populates="classes")
    attendance = db.relationship("Attendance", back_populates="school_class", cascade="all, delete-orphan")
    timetable = db.relationship("Timetable", back_populates="school_class", cascade="all, delete-orphan")
    assignments = db.relationship("Assignment", back_populates="school_class", cascade="all, delete-orphan")


class GradeLevel(db.Model):
    __tablename__ = "grade_levels"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    sequence = db.Column(db.Integer, unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    teachers = db.relationship("Teacher", secondary=teacher_grade, back_populates="grade_levels")

    @classmethod
    def ensure_table(cls):
        cls.__table__.create(db.engine, checkfirst=True)

    @classmethod
    def ensure_defaults(cls):
        cls.ensure_table()
        if cls.query.count():
            return
        for number in range(1, 13):
            db.session.add(cls(name=f"Grade {number}", code=f"G{number:02d}", sequence=number))
        db.session.commit()

    @classmethod
    def choices(cls):
        cls.ensure_defaults()
        return [(row.name, row.name) for row in cls.query.order_by(cls.sequence)]


class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @classmethod
    def ensure_table(cls):
        cls.__table__.create(db.engine, checkfirst=True)

    @classmethod
    def ensure_defaults(cls):
        cls.ensure_table()
        if cls.query.count():
            return
        defaults = [
            ("Leadership", "LEAD"),
            ("Academic Affairs", "ACAD"),
            ("Science", "SCI"),
            ("English", "ENG"),
            ("Mathematics", "MATH"),
        ]
        for name, code in defaults:
            db.session.add(cls(name=name, code=code))
        db.session.commit()

    @classmethod
    def choices(cls):
        cls.ensure_defaults()
        return [(row.name, row.name) for row in cls.query.order_by(cls.name)]


class Attendance(db.Model):
    __tablename__ = "attendance"
    __table_args__ = (db.UniqueConstraint("class_id", "student_id", "session_date", name="uq_attendance_session"),)

    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    session_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="present")
    note = db.Column(db.String(255))
    marked_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    school_class = db.relationship("SchoolClass", back_populates="attendance")
    student = db.relationship("Student", back_populates="attendance")


class Timetable(db.Model):
    __tablename__ = "timetable"

    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False)
    day_of_week = db.Column(db.String(12), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    period = db.Column(db.String(30), nullable=False)

    school_class = db.relationship("SchoolClass", back_populates="timetable")


class Assignment(db.Model):
    __tablename__ = "assignments"

    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    max_mark = db.Column(db.Float, nullable=False, default=100)
    weight_pct = db.Column(db.Float, nullable=False, default=10)
    due_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    school_class = db.relationship("SchoolClass", back_populates="assignments")
    grades = db.relationship("Grade", back_populates="assignment", cascade="all, delete-orphan")
    submissions = db.relationship("AssignmentSubmission", back_populates="assignment", cascade="all, delete-orphan")


class AssignmentSubmission(db.Model):
    __tablename__ = "assignment_submissions"

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    note = db.Column(db.Text, default="")
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    assignment = db.relationship("Assignment", back_populates="submissions")
    student = db.relationship("Student")

    @classmethod
    def ensure_table(cls):
        cls.__table__.create(db.engine, checkfirst=True)


class Grade(db.Model):
    __tablename__ = "grades"
    __table_args__ = (db.UniqueConstraint("assignment_id", "student_id", name="uq_grade_assignment_student"),)

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    mark = db.Column(db.Float, nullable=False)
    letter_grade = db.Column(db.String(5), nullable=False)
    feedback = db.Column(db.Text)
    graded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    assignment = db.relationship("Assignment", back_populates="grades")
    student = db.relationship("Student", back_populates="grades")


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    subject = db.Column(db.String(160), nullable=False)
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    sender = db.relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    recipient = db.relationship("User", foreign_keys=[recipient_id], back_populates="received_messages")


class LeaveRequest(db.Model):
    __tablename__ = "leave_requests"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    requested_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="pending", nullable=False)
    response_note = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    student = db.relationship("Student", back_populates="leave_requests")
    requested_by = db.relationship("User")


class Notice(db.Model):
    __tablename__ = "notices"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    body = db.Column(db.Text, nullable=False)
    audience = db.Column(db.String(20), default="all", nullable=False)
    status = db.Column(db.String(20), default="pending", nullable=False)
    requested_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    approved_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    approved_at = db.Column(db.DateTime)

    requested_by = db.relationship("User", foreign_keys=[requested_by_id])
    approved_by = db.relationship("User", foreign_keys=[approved_by_id])


class SystemSetting(db.Model):
    __tablename__ = "system_settings"

    id = db.Column(db.Integer, primary_key=True, default=1)
    school_name = db.Column(db.String(120), default="EduManage Demonstration School", nullable=False)
    academic_session = db.Column(db.String(30), default="2026-27", nullable=False)
    timezone = db.Column(db.String(60), default="Asia/Yangon", nullable=False)
    attendance_alert_threshold = db.Column(db.Float, default=85.0, nullable=False)
    default_grade_start = db.Column(db.Integer, default=1, nullable=False)
    default_grade_end = db.Column(db.Integer, default=12, nullable=False)
    attendance_mode = db.Column(db.String(30), default="daily_class", nullable=False)
    default_notice_audience = db.Column(db.String(20), default="all", nullable=False)
    notice_approval_required = db.Column(db.Boolean, default=True, nullable=False)
    teacher_leave_decisions_enabled = db.Column(db.Boolean, default=True, nullable=False)
    parent_leave_requests_enabled = db.Column(db.Boolean, default=True, nullable=False)
    portal_message = db.Column(db.Text, default="Welcome to the school portal.", nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @classmethod
    def ensure_table(cls):
        cls.__table__.create(db.engine, checkfirst=True)

    @classmethod
    def current(cls):
        cls.ensure_table()
        settings = db.session.get(cls, 1)
        if settings:
            return settings
        settings = cls(id=1)
        db.session.add(settings)
        db.session.commit()
        return settings

    @classmethod
    def defaults(cls):
        return cls(id=1)


def letter_for_mark(mark, max_mark=100):
    pct = 0 if max_mark == 0 else (mark / max_mark) * 100
    if pct >= 70:
        return "A"
    if pct >= 60:
        return "B"
    if pct >= 50:
        return "C"
    if pct >= 40:
        return "D"
    return "F"
