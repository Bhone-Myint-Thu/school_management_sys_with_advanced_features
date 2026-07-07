from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..access import can_manage_leave, can_view_student, visible_students_query
from ..forms import AssignmentForm, AttendanceForm, GradeForm, LeaveDecisionForm, MessageForm
from ..models import Assignment, Attendance, Grade, LeaveRequest, Notice, Parent, SchoolClass, Student, User, letter_for_mark
from ..security import roles_required
from ..services import send_attendance_alert

bp = Blueprint("teacher", __name__, url_prefix="/teacher")


def _teacher_classes():
    return SchoolClass.query.filter_by(teacher_id=current_user.teacher.id).order_by(SchoolClass.name).all()


def _grade_choices():
    return [f"Grade {i}" for i in range(1, 13)]


def _filter_students(query):
    year_group = request.args.get("year_group", "").strip()
    class_id = request.args.get("class_id", type=int) or 0
    if year_group:
        query = query.filter(Student.year_group == year_group)
    if class_id:
        query = query.filter(Student.classes.any(SchoolClass.id == class_id))
    return query, year_group, class_id


def _filter_teacher_classes(query):
    year_group = request.args.get("year_group", "").strip()
    class_id = request.args.get("class_id", type=int) or 0
    if year_group:
        query = query.filter(SchoolClass.year_group == year_group)
    if class_id:
        query = query.filter(SchoolClass.id == class_id)
    return query, year_group, class_id


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
    year_group = request.args.get("year_group", "").strip()
    class_id = request.args.get("class_id", type=int) or 0
    rows = visible_students_query()
    if year_group:
        rows = rows.filter(Student.year_group == year_group)
    if class_id:
        rows = rows.filter(Student.classes.any(SchoolClass.id == class_id))
    return render_template(
        "teacher/students.html",
        students=rows.order_by(Student.full_name).all(),
        classes=_teacher_classes(),
        grade_choices=_grade_choices(),
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
    return render_template("teacher/leave.html", leave_requests=rows)


@bp.route("/leave/<int:leave_id>/set/<status>", methods=["POST"])
@login_required
@roles_required("teacher")
def leave_set_status(leave_id, status):
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
    form = LeaveDecisionForm()
    if form.validate_on_submit():
        row.status = form.status.data
        row.response_note = form.response_note.data
        db.session.commit()
        flash("Leave request updated.", "success")
        return redirect(url_for("teacher.leave_detail", leave_id=row.id))
    return render_template("teacher/leave_detail.html", leave_request=row, form=form)


@bp.route("/attendance", methods=["GET", "POST"])
@login_required
@roles_required("teacher")
def attendance():
    return redirect(url_for("teacher.attendance_create"))


@bp.route("/attendance/create", methods=["GET", "POST"])
@login_required
@roles_required("teacher")
def attendance_create():
    form = AttendanceForm(session_date=date.today())
    form.class_id.choices = [(row.id, row.name) for row in _teacher_classes()]
    form.student_id.choices = [(row.id, row.full_name) for row in visible_students_query().order_by(Student.full_name)]
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
    return render_template("teacher/attendance_create.html", form=form)


@bp.route("/attendance/records")
@login_required
@roles_required("teacher")
def attendance_records():
    class_query, year_group, class_id = _filter_teacher_classes(SchoolClass.query.filter_by(teacher_id=current_user.teacher.id))
    class_ids = [row.id for row in class_query.all()]
    records = Attendance.query.filter(Attendance.class_id.in_(class_ids)).order_by(Attendance.session_date.desc()).all()
    return render_template(
        "teacher/attendance_records.html",
        records=records,
        classes=_teacher_classes(),
        grade_choices=_grade_choices(),
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
    form = AssignmentForm()
    form.class_id.choices = [(row.id, row.name) for row in _teacher_classes()]
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
    return render_template("teacher/assignment_create.html", form=form)


@bp.route("/assignments/records")
@login_required
@roles_required("teacher")
def assignment_records():
    class_query, year_group, class_id = _filter_teacher_classes(SchoolClass.query.filter_by(teacher_id=current_user.teacher.id))
    class_ids = [row.id for row in class_query.all()]
    rows = Assignment.query.filter(Assignment.class_id.in_(class_ids)).order_by(Assignment.due_date).all()
    return render_template(
        "teacher/assignment_records.html",
        assignments=rows,
        classes=_teacher_classes(),
        grade_choices=_grade_choices(),
        selected_year_group=year_group,
        selected_class_id=class_id,
    )


@bp.route("/grades", methods=["GET", "POST"])
@login_required
@roles_required("teacher")
def grades():
    return redirect(url_for("teacher.grade_create"))


@bp.route("/grades/create", methods=["GET", "POST"])
@login_required
@roles_required("teacher")
def grade_create():
    form = GradeForm()
    form.assignment_id.choices = [
        (row.id, f"{row.school_class.subject}: {row.title}")
        for row in Assignment.query.join(SchoolClass).filter(SchoolClass.teacher_id == current_user.teacher.id)
    ]
    form.student_id.choices = [(row.id, row.full_name) for row in visible_students_query().order_by(Student.full_name)]
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
    return render_template("teacher/grade_create.html", form=form)


@bp.route("/grades/records")
@login_required
@roles_required("teacher")
def grade_records():
    class_query, year_group, class_id = _filter_teacher_classes(SchoolClass.query.filter_by(teacher_id=current_user.teacher.id))
    class_ids = [row.id for row in class_query.all()]
    rows = Grade.query.join(Assignment).filter(Assignment.class_id.in_(class_ids)).order_by(Grade.graded_at.desc()).all()
    return render_template(
        "teacher/grade_records.html",
        grades=rows,
        classes=_teacher_classes(),
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
