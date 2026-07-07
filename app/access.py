from flask_login import current_user

from .models import SchoolClass, Student


MANAGEMENT_ROLES = {"admin", "headmaster", "dean"}


def is_management(user=None):
    user = user or current_user
    return user.is_authenticated and user.role in MANAGEMENT_ROLES


def visible_classes_query(user=None):
    user = user or current_user
    query = SchoolClass.query
    if is_management(user):
        return query
    if user.role == "teacher" and user.teacher:
        return query.filter(SchoolClass.teacher_id == user.teacher.id)
    if user.role == "student" and user.student:
        return query.filter(SchoolClass.students.any(id=user.student.id))
    return query.filter(False)


def visible_students_query(user=None):
    user = user or current_user
    query = Student.query
    if is_management(user):
        return query
    if user.role == "teacher" and user.teacher:
        return query.filter(Student.classes.any(SchoolClass.teacher_id == user.teacher.id))
    if user.role == "parent" and user.parent:
        child_ids = [child.id for child in user.parent.students]
        return query.filter(Student.id.in_(child_ids))
    if user.role == "student" and user.student:
        return query.filter(Student.id == user.student.id)
    return query.filter(False)


def can_manage_leave(leave_request, user=None):
    user = user or current_user
    if is_management(user):
        return True
    if user.role == "teacher" and user.teacher:
        return any(school_class.teacher_id == user.teacher.id for school_class in leave_request.student.classes)
    return False


def can_view_student(student, user=None):
    return visible_students_query(user).filter(Student.id == student.id).first() is not None
