from flask import Blueprint, redirect, url_for
from flask_login import current_user

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    if current_user.role in {"headmaster", "dean"}:
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for(f"{current_user.role}.dashboard"))
