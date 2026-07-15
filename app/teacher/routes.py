import calendar
from datetime import date
from pathlib import Path

from flask import Blueprint, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from sqlalchemy import extract

from ..extensions import db
from ..access import can_manage_leave, can_view_student, visible_students_query
from ..forms import AssignmentForm, AttendanceForm, GradeForm, LeaveDecisionForm, MessageForm
from ..models import Assignment, AssignmentSubmission, Attendance, Grade, LeaveRequest, Notice, Parent, SchoolClass, Student, SystemSetting, User, letter_for_mark
from ..security import roles_required
from ..services import send_attendance_alert

bp = Blueprint("teacher", __name__, url_prefix="/teacher")


def _teacher_classes():
    return SchoolClass.query.filter_by(teacher_id=current_user.teacher.id).order_by(SchoolClass.name).all()


def _grade_choices():
    return [f"Grade {i}" for i in range(1, 13)]


def _filter_students(query):
    search = request.args.get("q", "").strip()
    year_group = request.args.get("year_group", "").strip()
    class_id = request.args.get("class_id", type=int) or 0
    if search:
        pattern = f"%{search}%"
        query = query.filter((Student.full_name.ilike(pattern)) | (Student.student_code.ilike(pattern)) | (Student.user.has(User.email.ilike(pattern))))
    if year_group:
        query = query.filter(Student.year_group == year_group)
    if class_id:
        query = query.filter(Student.classes.any(SchoolClass.id == class_id))
    return query, search, year_group, class_id


def _filter_teacher_classes(query):
    year_group = request.args.get("year_group", "").strip()
    class_id = request.args.get("class_id", type=int) or 0
    if year_group:
        query = query.filter(SchoolClass.year_group == year_group)
    if class_id:
        query = query.filter(SchoolClass.id == class_id)
    return query, year_group, class_id


def _teacher_class_context():
    year_group = request.args.get("year_group", "").strip()
    class_id = request.args.get("class_id", type=int) or 0
    query = SchoolClass.query.filter_by(teacher_id=current_user.teacher.id)
    if year_group:
        query = query.filter(SchoolClass.year_group == year_group)
    classes = query.order_by(SchoolClass.year_group, SchoolClass.name).all()
    if class_id and class_id not in {row.id for row in classes}:
        class_id = 0
    return year_group, class_id, classes


def _group_attendance_by_date(records):
    date_map = {}
    for row in records:
        bucket = date_map.get(row.session_date)
        if bucket is None:
            bucket = {"date": row.session_date, "records": [], "absent": [], "present": [], "late": []}
            date_map[row.session_date] = bucket
        bucket["records"].append(row)
        if row.status == "absent":
            bucket["absent"].append(row.student)
        elif row.status == "late":
            bucket["late"].append(row.student)
        else:
            bucket["present"].append(row.student)
    return date_map


def _attendance_month_grid(records, year, month):
    date_map = _group_attendance_by_date(records)
    weeks = []
    for week in calendar.Calendar(firstweekday=0).monthdatescalendar(year, month):
        week_cells = []
        for day in week:
            bucket = date_map.get(day, {"date": day, "records": [], "absent": [], "present": [], "late": []})
            week_cells.append(
                {
                    "date": day,
                    "in_month": day.month == month,
                    "records": bucket["records"],
                    "absent": bucket["absent"],
                    "present": bucket["present"],
                    "late": bucket["late"],
                }
            )
        weeks.append(week_cells)
    return weeks


def _visible_students_for_context(year_group="", class_id=0):
    query = visible_students_query()
    if year_group:
        query = query.filter(Student.year_group == year_group)
    if class_id:
        query = query.filter(Student.classes.any(SchoolClass.id == class_id))
    return query.order_by(Student.full_name).all()


def _assignments_for_context(year_group="", class_id=0):
    query = Assignment.query.join(SchoolClass).filter(SchoolClass.teacher_id == current_user.teacher.id)
    if year_group:
        query = query.filter(SchoolClass.year_group == year_group)
    if class_id:
        query = query.filter(Assignment.class_id == class_id)
    return query.order_by(SchoolClass.year_group, SchoolClass.name, Assignment.due_date).all()


def _group_by_grade_class(rows, class_getter):
    grouped = []
    grade_map = {}
    for row in rows:
        school_class = class_getter(row)
        grade = school_class.year_group
        class_name = school_class.name
        grade_bucket = grade_map.get(grade)
        if grade_bucket is None:
            grade_bucket = {"grade": grade, "classes": [], "_class_map": {}}
            grade_map[grade] = grade_bucket
            grouped.append(grade_bucket)
        class_bucket = grade_bucket["_class_map"].get(class_name)
        if class_bucket is None:
            class_bucket = {"class": school_class, "rows": []}
            grade_bucket["_class_map"][class_name] = class_bucket
            grade_bucket["classes"].append(class_bucket)
        class_bucket["rows"].append(row)
    for grade_bucket in grouped:
        grade_bucket.pop("_class_map", None)
    return grouped


@bp.route("/")
@login_required
@roles_required("teacher")
def dashboard():
    classes = _teacher_classes()
    students = visible_students_query().order_by(Student.full_name).all()
    leave_requests = LeaveRequest.query.filter(LeaveRequest.student_id.in_([student.id for student in students])).order_by(LeaveRequest.created_at.desc()).limit(6).all()
    return render_template(
        "teacher/dashboard.html",
        classes=classes,
        assignments=Assignment.query.join(SchoolClass).filter(SchoolClass.teacher_id == current_user.teacher.id).all(),
        students=students,
        leave_requests=leave_requests,
        notices=Notice.query.filter(Notice.status == "approved", Notice.audience.in_(["teachers", "parents", "all"])).order_by(Notice.approved_at.desc()).limit(5).all(),
        inbox=current_user.received_messages,
    )


@bp.route("/students")
@login_required
@roles_required("teacher")
def students():
    rows, search, year_group, class_id = _filter_students(visible_students_query())
    class_query = SchoolClass.query.filter_by(teacher_id=current_user.teacher.id)
    if year_group:
        class_query = class_query.filter(SchoolClass.year_group == year_group)
    return render_template(
        "teacher/students.html",
        students=rows.order_by(Student.full_name).all(),
        classes=class_query.order_by(SchoolClass.year_group, SchoolClass.name).all(),
        grade_choices=_grade_choices(),
        search=search,
        selected_year_group=year_group,
        selected_class_id=class_id,
    )


@bp.route("/students/<int:student_id>")
@login_required
@roles_required("teacher")
def student_detail(student_id):
    student = db.get_or_404(Student, student_id)
    if not can_view_student(student):
        return ("Forbidden", 403)
    return render_template("teacher/student_detail.html", student=student)


@bp.route("/leave")
@login_required
@roles_required("teacher")
def leave():
    students = visible_students_query().all()
    rows = LeaveRequest.query.filter(LeaveRequest.student_id.in_([student.id for student in students])).order_by(LeaveRequest.created_at.desc()).all()
    return render_template("teacher/leave.html", leave_requests=rows, settings=SystemSetting.current())


@bp.route("/leave/<int:leave_id>/set/<status>", methods=["POST"])
@login_required
@roles_required("teacher")
def leave_set_status(leave_id, status):
    if not SystemSetting.current().teacher_leave_decisions_enabled:
        flash("Teacher leave decisions are disabled in system settings.", "warning")
        return redirect(url_for("teacher.leave_detail", leave_id=leave_id))
    if status not in {"draft", "approved", "refused"}:
        return ("Bad request", 400)
    row = db.get_or_404(LeaveRequest, leave_id)
    if not can_manage_leave(row):
        return ("Forbidden", 403)
    row.status = status
    if status == "draft":
        row.response_note = "Reset to draft by teacher"
    elif status == "approved":
        row.response_note = "Approved by teacher"
    else:
        row.response_note = "Refused by teacher"
    db.session.commit()
    flash("Leave request updated.", "success")
    return redirect(url_for("teacher.leave_detail", leave_id=row.id))


@bp.route("/leave/<int:leave_id>", methods=["GET", "POST"])
@login_required
@roles_required("teacher")
def leave_detail(leave_id):
    row = db.get_or_404(LeaveRequest, leave_id)
    if not can_manage_leave(row):
        return ("Forbidden", 403)
    settings = SystemSetting.current()
    form = LeaveDecisionForm()
    if form.validate_on_submit():
        if not settings.teacher_leave_decisions_enabled:
            flash("Teacher leave decisions are disabled in system settings.", "warning")
            return redirect(url_for("teacher.leave_detail", leave_id=row.id))
        row.status = form.status.data
        row.response_note = form.response_note.data
        db.session.commit()
        flash("Leave request updated.", "success")
        return redirect(url_for("teacher.leave_detail", leave_id=row.id))
    return render_template("teacher/leave_detail.html", leave_request=row, form=form, settings=settings)


@bp.route("/attendance", methods=["GET", "POST"])
@login_required
@roles_required("teacher")
def attendance():
    return redirect(url_for("teacher.attendance_create"))


@bp.route("/attendance/create", methods=["GET", "POST"])
@login_required
@roles_required("teacher")
def attendance_create():
    selected_year_group, selected_class_id, scoped_classes = _teacher_class_context()
    form = AttendanceForm(session_date=date.today())
    form.class_id.choices = [(row.id, f"{row.year_group} - {row.name}") for row in scoped_classes]
    form.student_id.choices = [
        (row.id, f"{row.full_name} ({row.year_group})") for row in _visible_students_for_context(selected_year_group, selected_class_id)
    ]
    if selected_class_id and request.method == "GET":
        form.class_id.data = selected_class_id
    if form.validate_on_submit():
        row = Attendance.query.filter_by(
            class_id=form.class_id.data,
            student_id=form.student_id.data,
            session_date=form.session_date.data,
        ).first() or Attendance(class_id=form.class_id.data, student_id=form.student_id.data, session_date=form.session_date.data)
        row.status = form.status.data
        row.note = form.note.data
        db.session.add(row)
        db.session.commit()
        send_attendance_alert(row.student)
        flash("Attendance saved.", "success")
        return redirect(url_for("teacher.attendance_records"))
    return render_template(
        "teacher/attendance_create.html",
        form=form,
        classes=_teacher_classes(),
        scoped_classes=scoped_classes,
        grade_choices=_grade_choices(),
        selected_year_group=selected_year_group,
        selected_class_id=selected_class_id,
    )


@bp.route("/attendance/records")
@login_required
@roles_required("teacher")
def attendance_records():
    class_query, year_group, class_id = _filter_teacher_classes(SchoolClass.query.filter_by(teacher_id=current_user.teacher.id))
    class_ids = [row.id for row in class_query.all()]
    selected_year = request.args.get("year", type=int) or date.today().year
    selected_month = request.args.get("month", type=int) or date.today().month
    records = (
        Attendance.query.join(SchoolClass)
        .filter(
            Attendance.class_id.in_(class_ids),
            extract("year", Attendance.session_date) == selected_year,
            extract("month", Attendance.session_date) == selected_month,
        )
        .order_by(SchoolClass.year_group, SchoolClass.name, Attendance.session_date.desc())
        .all()
    )
    return render_template(
        "teacher/attendance_records.html",
        records=records,
        weeks=_attendance_month_grid(records, selected_year, selected_month),
        classes=class_query.order_by(SchoolClass.year_group, SchoolClass.name).all(),
        grade_choices=_grade_choices(),
        selected_year_group=year_group,
        selected_class_id=class_id,
        selected_year=selected_year,
        selected_month=selected_month,
        selected_month_name=calendar.month_name[selected_month],
        years=list(range(date.today().year - 2, date.today().year + 3)),
        months=[(i, calendar.month_name[i]) for i in range(1, 13)],
    )


@bp.route("/attendance/records/<session_date>")
@login_required
@roles_required("teacher")
def attendance_day_detail(session_date):
    try:
        selected_date = date.fromisoformat(session_date)
    except ValueError:
        return ("Bad request", 400)
    class_query, year_group, class_id = _filter_teacher_classes(SchoolClass.query.filter_by(teacher_id=current_user.teacher.id))
    class_ids = [row.id for row in class_query.all()]
    records = (
        Attendance.query.join(SchoolClass).join(Student)
        .filter(Attendance.class_id.in_(class_ids), Attendance.session_date == selected_date)
        .order_by(SchoolClass.year_group, SchoolClass.name, Student.full_name)
        .all()
    )
    grouped = _group_attendance_by_date(records).get(selected_date, {"records": [], "absent": [], "present": [], "late": []})
    return render_template(
        "teacher/attendance_day_detail.html",
        selected_date=selected_date,
        records=records,
        grouped=grouped,
        selected_year_group=year_group,
        selected_class_id=class_id,
    )


@bp.route("/assignments", methods=["GET", "POST"])
@login_required
@roles_required("teacher")
def assignments():
    return redirect(url_for("teacher.assignment_create"))


@bp.route("/assignments/create", methods=["GET", "POST"])
@login_required
@roles_required("teacher")
def assignment_create():
    selected_year_group, selected_class_id, scoped_classes = _teacher_class_context()
    form = AssignmentForm()
    form.class_id.choices = [(row.id, f"{row.year_group} - {row.name}") for row in scoped_classes]
    if selected_class_id and request.method == "GET":
        form.class_id.data = selected_class_id
    if form.validate_on_submit():
        assignment = Assignment(
            class_id=form.class_id.data,
            title=form.title.data,
            max_mark=form.max_mark.data,
            weight_pct=form.weight_pct.data,
            due_date=form.due_date.data,
        )
        db.session.add(assignment)
        db.session.commit()
        flash("Assignment saved.", "success")
        return redirect(url_for("teacher.assignment_records"))
    return render_template(
        "teacher/assignment_create.html",
        form=form,
        classes=_teacher_classes(),
        scoped_classes=scoped_classes,
        grade_choices=_grade_choices(),
        selected_year_group=selected_year_group,
        selected_class_id=selected_class_id,
    )


@bp.route("/assignments/records")
@login_required
@roles_required("teacher")
def assignment_records():
    AssignmentSubmission.ensure_table()
    class_query, year_group, class_id = _filter_teacher_classes(SchoolClass.query.filter_by(teacher_id=current_user.teacher.id))
    class_ids = [row.id for row in class_query.all()]
    rows = (
        Assignment.query.join(SchoolClass)
        .filter(Assignment.class_id.in_(class_ids))
        .order_by(SchoolClass.year_group, SchoolClass.name, Assignment.due_date)
        .all()
    )
    return render_template(
        "teacher/assignment_records.html",
        assignments=rows,
        grouped_assignments=_group_by_grade_class(rows, lambda row: row.school_class),
        classes=class_query.order_by(SchoolClass.year_group, SchoolClass.name).all(),
        grade_choices=_grade_choices(),
        selected_year_group=year_group,
        selected_class_id=class_id,
    )


@bp.route("/assignments/submissions/<int:submission_id>/download")
@login_required
@roles_required("teacher")
def assignment_submission_download(submission_id):
    AssignmentSubmission.ensure_table()
    submission = db.get_or_404(AssignmentSubmission, submission_id)
    if submission.assignment.school_class.teacher_id != current_user.teacher.id:
        return ("Forbidden", 403)
    upload_dir = Path(current_app.instance_path) / "uploads" / "assignments"
    return send_from_directory(upload_dir, submission.stored_filename, as_attachment=True, download_name=submission.original_filename)


@bp.route("/grades", methods=["GET", "POST"])
@login_required
@roles_required("teacher")
def grades():
    return redirect(url_for("teacher.grade_create"))


@bp.route("/grades/create", methods=["GET", "POST"])
@login_required
@roles_required("teacher")
def grade_create():
    AssignmentSubmission.ensure_table()
    selected_year_group, selected_class_id, scoped_classes = _teacher_class_context()
    form = GradeForm()
    form.assignment_id.choices = [
        (row.id, f"{row.school_class.subject}: {row.title}")
        for row in _assignments_for_context(selected_year_group, selected_class_id)
    ]
    form.student_id.choices = [
        (row.id, f"{row.full_name} ({row.year_group})") for row in _visible_students_for_context(selected_year_group, selected_class_id)
    ]
    if form.validate_on_submit():
        assignment = db.session.get(Assignment, form.assignment_id.data)
        grade = Grade.query.filter_by(assignment_id=assignment.id, student_id=form.student_id.data).first() or Grade(
            assignment_id=assignment.id, student_id=form.student_id.data
        )
        grade.mark = form.mark.data
        grade.letter_grade = letter_for_mark(form.mark.data, assignment.max_mark)
        grade.feedback = form.feedback.data
        db.session.add(grade)
        db.session.commit()
        flash("Grade saved.", "success")
        return redirect(url_for("teacher.grade_records"))
    return render_template(
        "teacher/grade_create.html",
        form=form,
        classes=_teacher_classes(),
        scoped_classes=scoped_classes,
        grade_choices=_grade_choices(),
        selected_year_group=selected_year_group,
        selected_class_id=selected_class_id,
    )


@bp.route("/grades/records")
@login_required
@roles_required("teacher")
def grade_records():
    class_query, year_group, class_id = _filter_teacher_classes(SchoolClass.query.filter_by(teacher_id=current_user.teacher.id))
    class_ids = [row.id for row in class_query.all()]
    rows = (
        Grade.query.join(Assignment)
        .join(SchoolClass)
        .filter(Assignment.class_id.in_(class_ids))
        .order_by(SchoolClass.year_group, SchoolClass.name, Grade.graded_at.desc())
        .all()
    )
    return render_template(
        "teacher/grade_records.html",
        grades=rows,
        grouped_grades=_group_by_grade_class(rows, lambda row: row.assignment.school_class),
        classes=class_query.order_by(SchoolClass.year_group, SchoolClass.name).all(),
        grade_choices=_grade_choices(),
        selected_year_group=year_group,
        selected_class_id=class_id,
    )


@bp.route("/messages", methods=["GET", "POST"])
@login_required
@roles_required("teacher")
def messages():
    return redirect(url_for("teacher.message_inbox"))


@bp.route("/messages/send", methods=["GET", "POST"])
@login_required
@roles_required("teacher")
def message_send():
    form = MessageForm()
    form.recipient_id.choices = [(parent.user_id, parent.full_name) for parent in Parent.query.order_by(Parent.full_name)]
    if form.validate_on_submit():
        from ..models import Message

        db.session.add(Message(sender=current_user, recipient=db.session.get(User, form.recipient_id.data), subject=form.subject.data, body=form.body.data))
        db.session.commit()
        flash("Message sent.", "success")
        return redirect(url_for("teacher.message_sent"))
    return render_template("teacher/message_send.html", form=form)


@bp.route("/messages/inbox")
@login_required
@roles_required("teacher")
def message_inbox():
    return render_template("teacher/message_inbox.html", inbox=current_user.received_messages)


@bp.route("/messages/sent")
@login_required
@roles_required("teacher")
def message_sent():
    return render_template("teacher/message_sent.html", sent=current_user.sent_messages)
