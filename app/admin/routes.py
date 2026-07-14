from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, or_

from ..access import MANAGEMENT_ROLES, visible_classes_query
from ..extensions import db
from ..forms import (
    ClassForm,
    LeaveDecisionForm,
    NoticeForm,
    ParentForm,
    ProfileUserLinkForm,
    StudentForm,
    SystemSettingsForm,
    TeacherForm,
    TimetableForm,
    UserAccountForm,
    UserPasswordForm,
)
from ..models import Attendance, LeaveRequest, Notice, Parent, SchoolClass, Student, SystemSetting, Teacher, Timetable, User
from ..security import roles_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


def _save_user(user, email, role, password=None):
    user.email = email.lower().strip()
    user.role = role
    if password:
        user.set_password(password)
    return user


def _parent_choices():
    choices = [(0, "No parent linked")]
    choices.extend((parent.id, parent.full_name) for parent in Parent.query.order_by(Parent.full_name))
    return choices


def _class_choices(include_all=False):
    choices = [(row.id, f"{row.year_group} {row.section} - {row.subject}") for row in SchoolClass.query.order_by(SchoolClass.year_group, SchoolClass.section, SchoolClass.subject)]
    return ([(0, "All classes")] + choices) if include_all else choices


def _student_choices():
    return [(student.id, f"{student.full_name} ({student.student_code})") for student in Student.query.order_by(Student.full_name)]


def _apply_student_filters(query):
    search = request.args.get("q", "").strip()
    year_group = request.args.get("year_group", "").strip()
    class_id = request.args.get("class_id", type=int) or 0
    if search:
        pattern = f"%{search}%"
        query = query.filter((Student.full_name.ilike(pattern)) | (Student.student_code.ilike(pattern)))
    if year_group:
        query = query.filter(Student.year_group == year_group)
    if class_id:
        query = query.filter(Student.classes.any(SchoolClass.id == class_id))
    return query, search, year_group, class_id


def _apply_teacher_filters(query):
    search = request.args.get("q", "").strip()
    department = request.args.get("department", "").strip()
    position = request.args.get("position", "").strip()
    if search:
        pattern = f"%{search}%"
        query = query.join(User).filter(
            or_(Teacher.full_name.ilike(pattern), Teacher.staff_code.ilike(pattern), Teacher.department.ilike(pattern), User.email.ilike(pattern))
        )
    if department:
        query = query.filter(Teacher.department == department)
    if position:
        query = query.filter(Teacher.position == position)
    return query, search, department, position


def _apply_parent_filters(query):
    search = request.args.get("q", "").strip()
    relationship = request.args.get("relationship", "").strip()
    year_group = request.args.get("year_group", "").strip()
    if search:
        pattern = f"%{search}%"
        query = query.join(User).filter(
            or_(
                Parent.full_name.ilike(pattern),
                Parent.phone.ilike(pattern),
                Parent.relationship.ilike(pattern),
                User.email.ilike(pattern),
                Parent.students.any(Student.full_name.ilike(pattern)),
                Parent.students.any(Student.student_code.ilike(pattern)),
            )
        )
    if relationship:
        query = query.filter(Parent.relationship == relationship)
    if year_group:
        query = query.filter(Parent.students.any(Student.year_group == year_group))
    return query, search, relationship, year_group


def _apply_class_filters(query):
    year_group = request.args.get("year_group", "").strip()
    if year_group:
        query = query.filter(SchoolClass.year_group == year_group)
    return query, year_group


def _grade_choices():
    return [f"Grade {i}" for i in range(1, 13)]


def _user_choices():
    return [(user.id, f"{user.email} ({user.role})") for user in User.query.order_by(User.email)]


def _profile_choices():
    choices = []
    choices.extend((f"student:{row.id}", f"Student - {row.full_name} ({row.user.email})") for row in Student.query.order_by(Student.full_name))
    choices.extend((f"parent:{row.id}", f"Parent - {row.full_name} ({row.user.email})") for row in Parent.query.order_by(Parent.full_name))
    choices.extend((f"teacher:{row.id}", f"Teacher - {row.full_name} ({row.user.email})") for row in Teacher.query.order_by(Teacher.full_name))
    return choices


def _prepare_account_forms(account_form=None, password_form=None, link_form=None):
    account_form = account_form or UserAccountForm(prefix="account")
    password_form = password_form or UserPasswordForm(prefix="password")
    link_form = link_form or ProfileUserLinkForm(prefix="link")
    password_form.user_id.choices = _user_choices()
    link_form.user_id.choices = _user_choices()
    link_form.profile_ref.choices = _profile_choices()
    return account_form, password_form, link_form


def _profile_from_ref(profile_ref):
    profile_type, raw_id = profile_ref.split(":", 1)
    model_map = {"student": Student, "parent": Parent, "teacher": Teacher}
    if profile_type not in model_map:
        return None, None
    return profile_type, db.session.get(model_map[profile_type], int(raw_id))


def _user_can_link_profile(user, profile_type, profile):
    if profile_type == "student" and user.role != "student":
        return False, "Student profiles must be linked to student user accounts."
    if profile_type == "parent" and user.role != "parent":
        return False, "Parent profiles must be linked to parent user accounts."
    if profile_type == "teacher" and user.role not in {"teacher", "dean", "headmaster"}:
        return False, "Teacher profiles must be linked to teacher, dean, or headmaster user accounts."
    linked_profiles = [user.student, user.parent, user.teacher]
    for linked in linked_profiles:
        if linked is not None and (linked.__class__ is not profile.__class__ or linked.id != profile.id):
            return False, "That user account is already connected to another profile."
    return True, ""


@bp.route("/")
@login_required
@roles_required("admin", "headmaster", "dean")
def dashboard():
    month = request.args.get("month", type=int) or 0
    year = request.args.get("year", type=int) or 0
    class_id = request.args.get("class_id", type=int) or 0
    year_group = request.args.get("year_group", "").strip()
    attendance = Attendance.query.join(SchoolClass)
    if month:
        attendance = attendance.filter(func.extract("month", Attendance.session_date) == month)
    if year:
        attendance = attendance.filter(func.extract("year", Attendance.session_date) == year)
    if class_id:
        attendance = attendance.filter(Attendance.class_id == class_id)
    if year_group:
        attendance = attendance.filter(SchoolClass.year_group == year_group)
    absence_rows = (
        attendance.filter(Attendance.status == "absent")
        .with_entities(SchoolClass.year_group, SchoolClass.name, func.count(Attendance.id).label("absences"))
        .group_by(SchoolClass.year_group, SchoolClass.name)
        .order_by(func.count(Attendance.id).desc())
        .all()
    )

    class_summary = (
        db.session.query(SchoolClass.year_group, SchoolClass.name, func.count(Student.id).label("student_count"))
        .outerjoin(SchoolClass.students)
        .group_by(SchoolClass.year_group, SchoolClass.name)
        .order_by(SchoolClass.year_group, SchoolClass.name)
        .all()
    )
    return render_template(
        "admin/dashboard.html",
        students=Student.query.order_by(Student.full_name).all(),
        teachers=Teacher.query.order_by(Teacher.full_name).all(),
        classes=SchoolClass.query.order_by(SchoolClass.name).all(),
        parents=Parent.query.order_by(Parent.full_name).all(),
        leave_requests=LeaveRequest.query.order_by(LeaveRequest.created_at.desc()).limit(5).all(),
        absence_rows=absence_rows,
        class_summary=class_summary,
        grade_choices=_grade_choices(),
        selected_month=month,
        selected_year=year,
        selected_class_id=class_id,
        selected_year_group=year_group,
    )


@bp.route("/settings", methods=["GET", "POST"])
@login_required
@roles_required("admin", "headmaster", "dean")
def settings():
    settings = SystemSetting.current()
    active_tab = request.args.get("tab", "system")
    form = SystemSettingsForm(obj=settings)
    account_form, password_form, link_form = _prepare_account_forms()
    if form.validate_on_submit():
        if form.default_grade_start.data > form.default_grade_end.data:
            form.default_grade_end.errors.append("Ending grade must be greater than or equal to starting grade.")
        else:
            form.populate_obj(settings)
            db.session.commit()
            flash("System settings updated.", "success")
            return redirect(url_for("admin.settings", tab="system"))
    return render_template(
        "admin/settings.html",
        form=form,
        settings=settings,
        active_tab=active_tab,
        account_form=account_form,
        password_form=password_form,
        link_form=link_form,
        users=User.query.order_by(User.email).all(),
    )


@bp.route("/settings/users/create", methods=["POST"])
@login_required
@roles_required("admin", "headmaster", "dean")
def setting_user_create():
    form, _, _ = _prepare_account_forms(account_form=UserAccountForm(prefix="account"))
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        if User.query.filter_by(email=email).first():
            flash("A user with that email already exists.", "danger")
        else:
            user = _save_user(User(), email, form.role.data, form.password.data)
            db.session.add(user)
            db.session.commit()
            flash("User account created. Link it to a profile before role-specific access is used.", "success")
    else:
        flash("Please check the user account form.", "danger")
    return redirect(url_for("admin.settings", tab="create-user"))


@bp.route("/settings/users/password", methods=["POST"])
@login_required
@roles_required("admin", "headmaster", "dean")
def setting_user_password():
    _, form, _ = _prepare_account_forms(password_form=UserPasswordForm(prefix="password"))
    if form.validate_on_submit():
        user = db.session.get(User, form.user_id.data)
        if user:
            user.set_password(form.password.data)
            db.session.commit()
            flash("User password changed.", "success")
        else:
            flash("User account not found.", "danger")
    else:
        flash("Please check the password form.", "danger")
    return redirect(url_for("admin.settings", tab="change-password"))


@bp.route("/settings/users/link", methods=["POST"])
@login_required
@roles_required("admin", "headmaster", "dean")
def setting_user_link():
    _, _, form = _prepare_account_forms(link_form=ProfileUserLinkForm(prefix="link"))
    if form.validate_on_submit():
        profile_type, profile = _profile_from_ref(form.profile_ref.data)
        user = db.session.get(User, form.user_id.data)
        if not profile or not user:
            flash("Profile or user account not found.", "danger")
        else:
            allowed, message = _user_can_link_profile(user, profile_type, profile)
            if not allowed:
                flash(message, "danger")
            else:
                profile.user = user
                if profile_type == "teacher":
                    profile.position = user.role
                db.session.commit()
                flash("User account connected to profile.", "success")
    else:
        flash("Please check the profile connection form.", "danger")
    return redirect(url_for("admin.settings", tab="connect-account"))


@bp.route("/students")
@login_required
@roles_required("admin", "headmaster", "dean")
def students():
    rows, search, year_group, class_id = _apply_student_filters(Student.query)
    return render_template(
        "admin/students.html",
        students=rows.order_by(Student.full_name).all(),
        search=search,
        grade_choices=_grade_choices(),
        classes=SchoolClass.query.order_by(SchoolClass.year_group, SchoolClass.name).all(),
        selected_year_group=year_group,
        selected_class_id=class_id,
    )


@bp.route("/students/<int:student_id>")
@login_required
@roles_required("admin", "headmaster", "dean")
def student_detail(student_id):
    student = db.get_or_404(Student, student_id)
    return render_template("admin/student_detail.html", student=student)


@bp.route("/teachers")
@login_required
@roles_required("admin", "headmaster", "dean")
def teachers():
    rows, search, department, position = _apply_teacher_filters(Teacher.query)
    return render_template(
        "admin/teachers.html",
        teachers=rows.order_by(Teacher.full_name).all(),
        departments=[row[0] for row in db.session.query(Teacher.department).distinct().order_by(Teacher.department).all()],
        positions=["teacher", "dean", "headmaster"],
        search=search,
        selected_department=department,
        selected_position=position,
    )


@bp.route("/parents")
@login_required
@roles_required("admin", "headmaster", "dean")
def parents():
    rows, search, relationship, year_group = _apply_parent_filters(Parent.query)
    return render_template(
        "admin/parents.html",
        parents=rows.order_by(Parent.full_name).all(),
        relationships=[row[0] for row in db.session.query(Parent.relationship).distinct().order_by(Parent.relationship).all() if row[0]],
        grade_choices=_grade_choices(),
        search=search,
        selected_relationship=relationship,
        selected_year_group=year_group,
    )


@bp.route("/parents/<int:parent_id>")
@login_required
@roles_required("admin", "headmaster", "dean")
def parent_detail(parent_id):
    parent = db.get_or_404(Parent, parent_id)
    return render_template("admin/parent_detail.html", parent=parent)


@bp.route("/classes")
@login_required
@roles_required("admin", "headmaster", "dean")
def classes():
    rows, year_group = _apply_class_filters(SchoolClass.query)
    return render_template("admin/classes.html", classes=rows.order_by(SchoolClass.year_group, SchoolClass.name).all(), grade_choices=_grade_choices(), selected_year_group=year_group)


@bp.route("/classes/<int:class_id>")
@login_required
@roles_required("admin", "headmaster", "dean")
def class_detail(class_id):
    school_class = db.get_or_404(SchoolClass, class_id)
    return render_template("admin/class_detail.html", school_class=school_class)


@bp.route("/timetable")
@login_required
@roles_required("admin", "headmaster", "dean")
def timetable():
    rows, year_group = _apply_class_filters(SchoolClass.query)
    return render_template("admin/timetable.html", classes=rows.order_by(SchoolClass.year_group, SchoolClass.name).all(), grade_choices=_grade_choices(), selected_year_group=year_group)


@bp.route("/timetable/<int:class_id>")
@login_required
@roles_required("admin", "headmaster", "dean")
def timetable_detail(class_id):
    school_class = db.get_or_404(SchoolClass, class_id)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    return render_template("admin/timetable_detail.html", school_class=school_class, days=days)


@bp.route("/leave")
@login_required
@roles_required("admin", "headmaster", "dean")
def leave():
    rows = LeaveRequest.query.order_by(LeaveRequest.created_at.desc()).all()
    form = LeaveDecisionForm()
    return render_template("admin/leave.html", leave_requests=rows, form=form)


@bp.route("/leave/<int:leave_id>")
@login_required
@roles_required("admin", "headmaster", "dean")
def leave_detail(leave_id):
    row = db.get_or_404(LeaveRequest, leave_id)
    form = LeaveDecisionForm()
    return render_template("admin/leave_detail.html", leave_request=row, form=form)


@bp.route("/leave/<int:leave_id>/decision", methods=["POST"])
@login_required
@roles_required("admin", "headmaster", "dean")
def leave_decision(leave_id):
    row = db.get_or_404(LeaveRequest, leave_id)
    form = LeaveDecisionForm()
    if form.validate_on_submit():
        row.status = form.status.data
        row.response_note = form.response_note.data
        db.session.commit()
        flash("Leave request updated.", "success")
    return redirect(url_for("admin.leave"))


@bp.route("/notices", methods=["GET", "POST"])
@login_required
@roles_required("admin", "headmaster", "dean")
def notices():
    settings = SystemSetting.current()
    form = NoticeForm()
    if request.method == "GET":
        form.audience.data = settings.default_notice_audience
    if form.validate_on_submit():
        status = "approved" if current_user.role == "headmaster" or not settings.notice_approval_required else "pending"
        notice = Notice(
            title=form.title.data,
            body=form.body.data,
            audience=form.audience.data,
            status=status,
            requested_by=current_user,
            approved_by=current_user if status == "approved" else None,
            approved_at=datetime.utcnow() if status == "approved" else None,
        )
        db.session.add(notice)
        db.session.commit()
        flash("Notice announced." if status == "approved" else "Notice request sent to Headmaster.", "success")
        return redirect(url_for("admin.notices"))
    rows = Notice.query.order_by(Notice.created_at.desc()).all()
    return render_template("admin/notices.html", form=form, notices=rows, settings=settings)


@bp.route("/notices/<int:notice_id>/approve", methods=["POST"])
@login_required
@roles_required("headmaster")
def notice_approve(notice_id):
    notice = db.get_or_404(Notice, notice_id)
    notice.status = "approved"
    notice.approved_by = current_user
    notice.approved_at = datetime.utcnow()
    db.session.commit()
    flash("Notice approved and announced.", "success")
    return redirect(url_for("admin.notices"))


@bp.route("/parents/new", methods=["GET", "POST"])
@login_required
@roles_required("admin", "headmaster", "dean")
def parent_create():
    form = ParentForm()
    if form.validate_on_submit():
        user = _save_user(User(), form.email.data, "parent", form.password.data or "Password123")
        parent = Parent(
            user=user,
            full_name=form.full_name.data,
            phone=form.phone.data,
            address=form.address.data,
            relationship=form.relationship.data,
            emergency_contact=form.emergency_contact.data,
        )
        db.session.add(parent)
        db.session.commit()
        flash("Parent saved.", "success")
        return redirect(url_for("admin.parents"))
    return render_template("admin/form.html", form=form, title="Add Parent")


@bp.route("/parents/<int:parent_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin", "headmaster", "dean")
def parent_edit(parent_id):
    parent = db.get_or_404(Parent, parent_id)
    form = ParentForm(obj=parent)
    form.email.data = form.email.data or parent.user.email
    if form.validate_on_submit():
        _save_user(parent.user, form.email.data, "parent", form.password.data)
        parent.full_name = form.full_name.data
        parent.phone = form.phone.data
        parent.address = form.address.data
        parent.relationship = form.relationship.data
        parent.emergency_contact = form.emergency_contact.data
        db.session.commit()
        flash("Parent updated.", "success")
        return redirect(url_for("admin.parent_detail", parent_id=parent.id))
    return render_template("admin/form.html", form=form, title="Edit Parent")


@bp.route("/parents/<int:parent_id>/delete", methods=["POST"])
@login_required
@roles_required("admin", "headmaster", "dean")
def parent_delete(parent_id):
    parent = db.get_or_404(Parent, parent_id)
    db.session.delete(parent.user)
    db.session.commit()
    flash("Parent deleted.", "info")
    return redirect(url_for("admin.parents"))


@bp.route("/students/new", methods=["GET", "POST"])
@login_required
@roles_required("admin", "headmaster", "dean")
def student_create():
    form = StudentForm()
    form.parent_ids.choices = _parent_choices()
    form.class_ids.choices = _class_choices()
    if form.validate_on_submit():
        user = _save_user(User(), form.email.data, "student", form.password.data or "Password123")
        student = Student(
            user=user,
            full_name=form.full_name.data,
            year_group=form.year_group.data,
            date_of_birth=form.date_of_birth.data,
            student_code=form.student_code.data,
            address=form.address.data,
            emergency_contact_name=form.emergency_contact_name.data,
            emergency_contact_phone=form.emergency_contact_phone.data,
            medical_notes=form.medical_notes.data,
        )
        if form.parent_ids.data:
            student.parents.append(db.session.get(Parent, form.parent_ids.data))
        student.classes = [db.session.get(SchoolClass, class_id) for class_id in form.class_ids.data]
        db.session.add(student)
        db.session.commit()
        flash("Student saved.", "success")
        return redirect(url_for("admin.students"))
    return render_template("admin/form.html", form=form, title="Add Student")


@bp.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin", "headmaster", "dean")
def student_edit(student_id):
    student = db.get_or_404(Student, student_id)
    form = StudentForm(obj=student)
    form.parent_ids.choices = _parent_choices()
    form.class_ids.choices = _class_choices()
    if request.method == "GET":
        form.email.data = student.user.email
        form.parent_ids.data = student.parents[0].id if student.parents else 0
        form.class_ids.data = [school_class.id for school_class in student.classes]
    if form.validate_on_submit():
        _save_user(student.user, form.email.data, "student", form.password.data)
        student.full_name = form.full_name.data
        student.year_group = form.year_group.data
        student.date_of_birth = form.date_of_birth.data
        student.student_code = form.student_code.data
        student.address = form.address.data
        student.emergency_contact_name = form.emergency_contact_name.data
        student.emergency_contact_phone = form.emergency_contact_phone.data
        student.medical_notes = form.medical_notes.data
        student.parents = []
        if form.parent_ids.data:
            student.parents.append(db.session.get(Parent, form.parent_ids.data))
        student.classes = [db.session.get(SchoolClass, class_id) for class_id in form.class_ids.data]
        db.session.commit()
        flash("Student updated.", "success")
        return redirect(url_for("admin.student_detail", student_id=student.id))
    return render_template("admin/form.html", form=form, title="Edit Student")


@bp.route("/students/<int:student_id>/delete", methods=["POST"])
@login_required
@roles_required("admin", "headmaster", "dean")
def student_delete(student_id):
    student = db.get_or_404(Student, student_id)
    db.session.delete(student.user)
    db.session.commit()
    flash("Student deleted.", "info")
    return redirect(url_for("admin.students"))


@bp.route("/teachers/new", methods=["GET", "POST"])
@login_required
@roles_required("admin", "headmaster", "dean")
def teacher_create():
    form = TeacherForm()
    if form.validate_on_submit():
        user = _save_user(User(), form.email.data, form.position.data, form.password.data or "Password123")
        teacher = Teacher(
            user=user,
            full_name=form.full_name.data,
            department=form.department.data,
            staff_code=form.staff_code.data,
            position=form.position.data,
        )
        db.session.add(teacher)
        db.session.commit()
        flash("Teacher saved.", "success")
        return redirect(url_for("admin.teachers"))
    return render_template("admin/form.html", form=form, title="Add Teacher")


@bp.route("/teachers/<int:teacher_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin", "headmaster", "dean")
def teacher_edit(teacher_id):
    teacher = db.get_or_404(Teacher, teacher_id)
    form = TeacherForm(obj=teacher)
    if request.method == "GET":
        form.email.data = teacher.user.email
    if form.validate_on_submit():
        _save_user(teacher.user, form.email.data, "teacher", form.password.data)
        teacher.user.role = form.position.data
        teacher.full_name = form.full_name.data
        teacher.department = form.department.data
        teacher.staff_code = form.staff_code.data
        teacher.position = form.position.data
        db.session.commit()
        flash("Teacher updated.", "success")
        return redirect(url_for("admin.teachers"))
    return render_template("admin/form.html", form=form, title="Edit Teacher")


@bp.route("/teachers/<int:teacher_id>/delete", methods=["POST"])
@login_required
@roles_required("admin", "headmaster", "dean")
def teacher_delete(teacher_id):
    teacher = db.get_or_404(Teacher, teacher_id)
    db.session.delete(teacher.user)
    db.session.commit()
    flash("Teacher deleted.", "info")
    return redirect(url_for("admin.teachers"))


@bp.route("/classes/new", methods=["GET", "POST"])
@login_required
@roles_required("admin", "headmaster", "dean")
def class_create():
    form = ClassForm()
    form.teacher_id.choices = [(teacher.id, teacher.full_name) for teacher in Teacher.query.order_by(Teacher.full_name)]
    form.student_ids.choices = _student_choices()
    if form.validate_on_submit():
        school_class = SchoolClass(
            teacher_id=form.teacher_id.data,
            name=form.name.data,
            subject=form.subject.data,
            year_group=form.year_group.data,
            section=form.section.data,
            room=form.room.data,
        )
        school_class.students = [db.session.get(Student, student_id) for student_id in form.student_ids.data]
        db.session.add(school_class)
        db.session.commit()
        flash("Class saved.", "success")
        return redirect(url_for("admin.classes"))
    return render_template("admin/form.html", form=form, title="Add Class")


@bp.route("/classes/<int:class_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin", "headmaster", "dean")
def class_edit(class_id):
    school_class = db.get_or_404(SchoolClass, class_id)
    form = ClassForm(obj=school_class)
    form.teacher_id.choices = [(teacher.id, teacher.full_name) for teacher in Teacher.query.order_by(Teacher.full_name)]
    form.student_ids.choices = _student_choices()
    if request.method == "GET":
        form.teacher_id.data = school_class.teacher_id
        form.student_ids.data = [student.id for student in school_class.students]
    if form.validate_on_submit():
        school_class.teacher_id = form.teacher_id.data
        school_class.name = form.name.data
        school_class.subject = form.subject.data
        school_class.year_group = form.year_group.data
        school_class.section = form.section.data
        school_class.room = form.room.data
        school_class.students = [db.session.get(Student, student_id) for student_id in form.student_ids.data]
        db.session.commit()
        flash("Class updated.", "success")
        return redirect(url_for("admin.class_detail", class_id=school_class.id))
    return render_template("admin/form.html", form=form, title="Edit Class")


@bp.route("/classes/<int:class_id>/delete", methods=["POST"])
@login_required
@roles_required("admin", "headmaster", "dean")
def class_delete(class_id):
    school_class = db.get_or_404(SchoolClass, class_id)
    db.session.delete(school_class)
    db.session.commit()
    flash("Class deleted.", "info")
    return redirect(url_for("admin.classes"))


@bp.route("/timetable/new", methods=["GET", "POST"])
@login_required
@roles_required("admin", "headmaster", "dean")
def timetable_create():
    form = TimetableForm()
    form.class_id.choices = [(row.id, row.name) for row in SchoolClass.query.order_by(SchoolClass.name)]
    if form.validate_on_submit():
        slot = Timetable(
            class_id=form.class_id.data,
            day_of_week=form.day_of_week.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            period=form.period.data,
        )
        db.session.add(slot)
        db.session.commit()
        flash("Timetable slot saved.", "success")
        return redirect(url_for("admin.timetable_detail", class_id=form.class_id.data))
    return render_template("admin/form.html", form=form, title="Add Timetable Slot")
