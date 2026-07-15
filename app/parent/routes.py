from flask import Blueprint, Response, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..forms import LeaveRequestForm, MessageForm
from ..models import LeaveRequest, Message, Notice, SystemSetting, Teacher, Timetable, User
from ..security import roles_required
from ..services import build_student_report_pdf

bp = Blueprint("parent", __name__, url_prefix="/parent")


@bp.route("/")
@login_required
@roles_required("parent")
def dashboard():
    children = current_user.parent.students
    notices = Notice.query.filter(Notice.status == "approved", Notice.audience.in_(["parents", "all"])).order_by(Notice.approved_at.desc()).limit(5).all()
    return render_template("parent/dashboard.html", children=children, inbox=current_user.received_messages, notices=notices)


@bp.route("/students")
@login_required
@roles_required("parent")
def students():
    search = request.args.get("q", "").strip()
    children = current_user.parent.students
    if search:
        needle = search.lower()
        children = [
            child
            for child in children
            if needle in child.full_name.lower()
            or needle in child.student_code.lower()
            or needle in child.year_group.lower()
            or any(needle in school_class.name.lower() or needle in school_class.subject.lower() for school_class in child.classes)
        ]
    return render_template("parent/students.html", children=children, search=search)


@bp.route("/timetable")
@login_required
@roles_required("parent")
def timetable():
    children = current_user.parent.students
    child_ids = [school_class.id for child in children for school_class in child.classes]
    slots = Timetable.query.filter(Timetable.class_id.in_(child_ids)).order_by(Timetable.day_of_week, Timetable.start_time).all()
    slots_by_child = {child.id: [slot for slot in slots if slot.class_id in {school_class.id for school_class in child.classes}] for child in children}
    return render_template("parent/timetable.html", children=children, slots_by_child=slots_by_child, days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])


@bp.route("/students/<int:student_id>")
@login_required
@roles_required("parent")
def student_detail(student_id):
    student = next((child for child in current_user.parent.students if child.id == student_id), None)
    if student is None:
        return ("Not found", 404)
    return render_template("parent/student_detail.html", student=student)


@bp.route("/students/<int:student_id>/timetable")
@login_required
@roles_required("parent")
def student_timetable(student_id):
    student = next((child for child in current_user.parent.students if child.id == student_id), None)
    if student is None:
        return ("Not found", 404)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    class_ids = [school_class.id for school_class in student.classes]
    timetable = Timetable.query.filter(Timetable.class_id.in_(class_ids)).order_by(Timetable.day_of_week, Timetable.start_time).all()
    return render_template("parent/student_timetable.html", student=student, days=days, timetable=timetable)


@bp.route("/leave", methods=["GET", "POST"])
@login_required
@roles_required("parent")
def leave():
    settings = SystemSetting.current()
    form = LeaveRequestForm()
    form.student_id.choices = [(student.id, student.full_name) for student in current_user.parent.students]
    if form.validate_on_submit():
        if not settings.parent_leave_requests_enabled:
            flash("Parent leave requests are disabled in system settings.", "warning")
            return redirect(url_for("parent.leave"))
        student_ids = {student.id for student in current_user.parent.students}
        if form.student_id.data not in student_ids:
            return ("Not found", 404)
        db.session.add(
            LeaveRequest(
                student_id=form.student_id.data,
                requested_by=current_user,
                start_date=form.start_date.data,
                end_date=form.end_date.data,
                reason=form.reason.data,
            )
        )
        db.session.commit()
        flash("Leave request submitted.", "success")
        return redirect(url_for("parent.leave"))
    rows = LeaveRequest.query.filter(LeaveRequest.student_id.in_([student.id for student in current_user.parent.students])).order_by(
        LeaveRequest.created_at.desc()
    )
    return render_template("parent/leave.html", form=form, leave_requests=rows, settings=settings)


@bp.route("/messages", methods=["GET", "POST"])
@login_required
@roles_required("parent")
def messages():
    form = MessageForm()
    form.recipient_id.choices = [(teacher.user_id, teacher.full_name) for teacher in Teacher.query.order_by(Teacher.full_name)]
    if form.validate_on_submit():
        db.session.add(Message(sender=current_user, recipient=db.session.get(User, form.recipient_id.data), subject=form.subject.data, body=form.body.data))
        db.session.commit()
        flash("Message sent.", "success")
        return redirect(url_for("parent.messages"))
    return render_template("parent/messages.html", form=form, inbox=current_user.received_messages, sent=current_user.sent_messages)


@bp.route("/reports/<int:student_id>")
@login_required
@roles_required("parent")
def report(student_id):
    student = next((child for child in current_user.parent.students if child.id == student_id), None)
    if student is None:
        return ("Not found", 404)
    pdf = build_student_report_pdf(student)
    return Response(
        pdf.getvalue(),
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={student.student_code}-report.pdf"},
    )
