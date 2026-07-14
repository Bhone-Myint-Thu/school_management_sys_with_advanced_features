from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from ..extensions import db
from ..forms import LoginForm, SignupForm
from ..models import Parent, Student, User

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash("Signed in successfully.", "success")
            return redirect(request.args.get("next") or url_for("main.index"))
        flash("Invalid email or password.", "danger")
    return render_template("auth/login.html", form=form)


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = SignupForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        if User.query.filter_by(email=email).first():
            form.email.errors.append("An account with this email already exists.")
        elif form.role.data == "student" and not all([form.year_group.data, form.date_of_birth.data, form.student_code.data]):
            flash("Student sign up needs year group, date of birth, and student code.", "danger")
        elif form.role.data == "student" and Student.query.filter_by(student_code=form.student_code.data.strip()).first():
            form.student_code.errors.append("This student code is already registered.")
        else:
            user = User(email=email, role=form.role.data)
            user.set_password(form.password.data)
            if form.role.data == "parent":
                profile = Parent(user=user, full_name=form.full_name.data, phone=form.phone.data, relationship="Parent")
            else:
                profile = Student(
                    user=user,
                    full_name=form.full_name.data,
                    year_group=form.year_group.data.strip(),
                    date_of_birth=form.date_of_birth.data,
                    student_code=form.student_code.data.strip(),
                )
            db.session.add(profile)
            db.session.commit()
            login_user(user)
            flash("Account created successfully.", "success")
            return redirect(url_for("main.index"))
    return render_template("auth/signup.html", form=form)


@bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    flash("Signed out.", "info")
    return redirect(url_for("auth.login"))
