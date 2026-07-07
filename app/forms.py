from flask_wtf import FlaskForm
from wtforms import DateField, FloatField, PasswordField, SelectField, SelectMultipleField, StringField, SubmitField, TextAreaField, TimeField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign in")


class StudentForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[Optional(), Length(min=8)])
    full_name = StringField("Full name", validators=[DataRequired(), Length(max=120)])
    year_group = StringField("Year group", validators=[DataRequired(), Length(max=20)])
    date_of_birth = DateField("Date of birth", validators=[DataRequired()])
    student_code = StringField("Student code", validators=[DataRequired(), Length(max=30)])
    address = StringField("Address", validators=[Optional(), Length(max=255)])
    emergency_contact_name = StringField("Emergency contact name", validators=[Optional(), Length(max=120)])
    emergency_contact_phone = StringField("Emergency contact phone", validators=[Optional(), Length(max=40)])
    medical_notes = StringField("Medical notes", validators=[Optional(), Length(max=255)])
    parent_ids = SelectField("Parent", coerce=int, validators=[Optional()])
    class_ids = SelectMultipleField("Classes", coerce=int, validators=[Optional()])
    submit = SubmitField("Save student")


class ParentForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[Optional(), Length(min=8)])
    full_name = StringField("Full name", validators=[DataRequired(), Length(max=120)])
    phone = StringField("Phone", validators=[Optional(), Length(max=40)])
    address = StringField("Address", validators=[Optional(), Length(max=255)])
    relationship = StringField("Relationship", validators=[Optional(), Length(max=60)])
    emergency_contact = StringField("Emergency contact", validators=[Optional(), Length(max=40)])
    submit = SubmitField("Save parent")


class TeacherForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[Optional(), Length(min=8)])
    full_name = StringField("Full name", validators=[DataRequired(), Length(max=120)])
    department = StringField("Department", validators=[DataRequired(), Length(max=80)])
    staff_code = StringField("Staff code", validators=[DataRequired(), Length(max=30)])
    position = SelectField(
        "Position",
        choices=[("teacher", "Teacher"), ("dean", "Dean"), ("headmaster", "Headmaster")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Save teacher")


class ClassForm(FlaskForm):
    teacher_id = SelectField("Teacher", coerce=int, validators=[DataRequired()])
    name = StringField("Class name", validators=[DataRequired(), Length(max=80)])
    subject = StringField("Subject", validators=[DataRequired(), Length(max=80)])
    year_group = StringField("Year group", validators=[DataRequired(), Length(max=20)])
    section = StringField("Section", validators=[DataRequired(), Length(max=20)])
    room = StringField("Room", validators=[DataRequired(), Length(max=30)])
    student_ids = SelectMultipleField("Students", coerce=int, validators=[Optional()])
    submit = SubmitField("Save class")


class TimetableForm(FlaskForm):
    class_id = SelectField("Class", coerce=int, validators=[DataRequired()])
    day_of_week = SelectField(
        "Day",
        choices=[(d, d) for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]],
        validators=[DataRequired()],
    )
    start_time = TimeField("Start time", validators=[DataRequired()])
    end_time = TimeField("End time", validators=[DataRequired()])
    period = StringField("Period", validators=[DataRequired(), Length(max=30)])
    submit = SubmitField("Save timetable slot")


class AttendanceForm(FlaskForm):
    class_id = SelectField("Class", coerce=int, validators=[DataRequired()])
    student_id = SelectField("Student", coerce=int, validators=[DataRequired()])
    session_date = DateField("Session date", validators=[DataRequired()])
    status = SelectField("Status", choices=[("present", "Present"), ("late", "Late"), ("absent", "Absent")])
    note = StringField("Note", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Save attendance")


class AssignmentForm(FlaskForm):
    class_id = SelectField("Class", coerce=int, validators=[DataRequired()])
    title = StringField("Title", validators=[DataRequired(), Length(max=120)])
    max_mark = FloatField("Max mark", validators=[DataRequired(), NumberRange(min=1)])
    weight_pct = FloatField("Weight %", validators=[DataRequired(), NumberRange(min=0, max=100)])
    due_date = DateField("Due date", validators=[DataRequired()])
    submit = SubmitField("Save assignment")


class GradeForm(FlaskForm):
    assignment_id = SelectField("Assignment", coerce=int, validators=[DataRequired()])
    student_id = SelectField("Student", coerce=int, validators=[DataRequired()])
    mark = FloatField("Mark", validators=[DataRequired(), NumberRange(min=0)])
    feedback = TextAreaField("Feedback", validators=[Optional()])
    submit = SubmitField("Save grade")


class MessageForm(FlaskForm):
    recipient_id = SelectField("Recipient", coerce=int, validators=[DataRequired()])
    subject = StringField("Subject", validators=[DataRequired(), Length(max=160)])
    body = TextAreaField("Message", validators=[DataRequired()])
    submit = SubmitField("Send message")


class LeaveRequestForm(FlaskForm):
    student_id = SelectField("Student", coerce=int, validators=[DataRequired()])
    start_date = DateField("Start date", validators=[DataRequired()])
    end_date = DateField("End date", validators=[DataRequired()])
    reason = TextAreaField("Reason", validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField("Submit leave request")


class LeaveDecisionForm(FlaskForm):
    status = SelectField(
        "Decision",
        choices=[("draft", "Reset to Draft"), ("approved", "Approve"), ("refused", "Refuse")],
        validators=[DataRequired()],
    )
    response_note = StringField("Response note", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Save decision")


class NoticeForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=160)])
    body = TextAreaField("Notice", validators=[DataRequired()])
    audience = SelectField(
        "Audience",
        choices=[("teachers", "Teachers only"), ("parents", "Parents and teachers"), ("all", "All users")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Submit notice")


class DateFilterForm(FlaskForm):
    month = SelectField("Month", coerce=int, choices=[(0, "All months")] + [(i, str(i)) for i in range(1, 13)])
    year = SelectField("Year", coerce=int, choices=[(0, "All years")] + [(y, str(y)) for y in range(2024, 2031)])
    year_group = SelectField("Grade", choices=[("", "All grades")] + [(f"Grade {i}", f"Grade {i}") for i in range(1, 13)])
    class_id = SelectField("Class", coerce=int, validators=[Optional()])
    submit = SubmitField("Apply filters")
