from flask import Blueprint, render_template
from flask_login import current_user, login_required

from ..models import Assignment, Notice, SchoolClass, Timetable
from ..security import roles_required

bp = Blueprint("student", __name__, url_prefix="/student")


@bp.route("/")
@login_required
@roles_required("student")
def dashboard():
    student = current_user.student
    class_ids = [school_class.id for school_class in student.classes]
    timetable = Timetable.query.filter(Timetable.class_id.in_(class_ids)).all()
    assignments = (
        Assignment.query.join(Assignment.school_class)
        .filter(SchoolClass.id.in_(class_ids))
        .order_by(Assignment.due_date)
        .all()
    )
    notices = Notice.query.filter(Notice.status == "approved", Notice.audience == "all").order_by(Notice.approved_at.desc()).limit(5).all()
    return render_template("student/dashboard.html", student=student, timetable=timetable, assignments=assignments, notices=notices)
