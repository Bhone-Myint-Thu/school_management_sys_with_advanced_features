from datetime import date
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from ..extensions import db
from ..forms import AssignmentSubmissionForm
from ..models import Assignment, AssignmentSubmission, Notice, SchoolClass, Timetable
from ..security import roles_required

bp = Blueprint("student", __name__, url_prefix="/student")


@bp.route("/")
@login_required
@roles_required("student")
def dashboard():
    AssignmentSubmission.ensure_table()
    student = current_user.student
    class_ids = [school_class.id for school_class in student.classes]
    timetable = Timetable.query.filter(Timetable.class_id.in_(class_ids)).order_by(Timetable.day_of_week, Timetable.start_time).all()
    assignments = (
        Assignment.query.join(Assignment.school_class)
        .filter(SchoolClass.id.in_(class_ids))
        .order_by(Assignment.due_date)
        .all()
    )
    submissions = {row.assignment_id: row for row in AssignmentSubmission.query.filter_by(student_id=student.id).all()}
    notices = Notice.query.filter(Notice.status == "approved", Notice.audience == "all").order_by(Notice.approved_at.desc()).limit(5).all()
    return render_template(
        "student/dashboard.html",
        student=student,
        timetable=timetable,
        assignments=assignments,
        submissions=submissions,
        notices=notices,
        days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    )


@bp.route("/assignments")
@login_required
@roles_required("student")
def assignments():
    AssignmentSubmission.ensure_table()
    student = current_user.student
    class_ids = [school_class.id for school_class in student.classes]
    rows = (
        Assignment.query.join(Assignment.school_class)
        .filter(SchoolClass.id.in_(class_ids))
        .order_by(Assignment.due_date)
        .all()
    )
    submissions = {row.assignment_id: row for row in AssignmentSubmission.query.filter_by(student_id=student.id).all()}
    return render_template("student/assignments.html", assignments=rows, submissions=submissions, today=date.today())


@bp.route("/timetable")
@login_required
@roles_required("student")
def timetable():
    student = current_user.student
    class_ids = [school_class.id for school_class in student.classes]
    timetable = Timetable.query.filter(Timetable.class_id.in_(class_ids)).order_by(Timetable.day_of_week, Timetable.start_time).all()
    return render_template("student/timetable.html", student=student, timetable=timetable, days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])


@bp.route("/assignments/<int:assignment_id>/upload", methods=["GET", "POST"])
@login_required
@roles_required("student")
def assignment_upload(assignment_id):
    AssignmentSubmission.ensure_table()
    student = current_user.student
    class_ids = {school_class.id for school_class in student.classes}
    assignment = db.get_or_404(Assignment, assignment_id)
    if assignment.class_id not in class_ids:
        return ("Forbidden", 403)
    submission = AssignmentSubmission.query.filter_by(assignment_id=assignment.id, student_id=student.id).first()
    if assignment.due_date < date.today():
        flash("The upload deadline has passed.", "warning")
        return redirect(url_for("student.assignments"))
    form = AssignmentSubmissionForm()
    if form.validate_on_submit():
        upload = form.file.data
        original = secure_filename(upload.filename)
        stored = f"{student.id}-{assignment.id}-{uuid4().hex}-{original}"
        upload_dir = Path(current_app.instance_path) / "uploads" / "assignments"
        upload_dir.mkdir(parents=True, exist_ok=True)
        upload.save(upload_dir / stored)
        was_existing = submission is not None
        if submission is None:
            submission = AssignmentSubmission(assignment=assignment, student=student)
        submission.original_filename = original
        submission.stored_filename = stored
        submission.note = form.note.data
        db.session.add(submission)
        db.session.commit()
        flash("Assignment re-uploaded." if was_existing else "Assignment uploaded.", "success")
        return redirect(url_for("student.assignments"))
    return render_template("student/assignment_upload.html", form=form, assignment=assignment, submission=submission)
