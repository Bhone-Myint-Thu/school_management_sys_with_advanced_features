from flask import Blueprint, redirect, request, url_for
from flask_login import current_user, login_required

from ..extensions import db

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    if current_user.role in {"headmaster", "dean"}:
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for(f"{current_user.role}.dashboard"))


@bp.route("/search")
@login_required
def search():
    query = request.args.get("q", "").strip()
    if current_user.role in {"admin", "headmaster", "dean"}:
        return redirect(url_for("admin.students", q=query))
    if current_user.role == "teacher":
        return redirect(url_for("teacher.students", q=query))
    if current_user.role == "parent":
        return redirect(url_for("parent.students", q=query))
    return redirect(url_for("student.dashboard", q=query))


@bp.route("/notifications/read", methods=["POST"])
@login_required
def mark_notifications_read():
    for message in current_user.received_messages:
        message.is_read = True
    db.session.commit()
    return redirect(request.referrer or url_for("main.index"))
