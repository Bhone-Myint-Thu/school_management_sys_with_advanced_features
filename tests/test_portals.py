from datetime import date, timedelta
from io import BytesIO

from test_auth import login

from app.extensions import db
from app.models import Assignment, Attendance, Department, GradeLevel, SchoolClass, Student, Teacher, User


def test_parent_can_download_child_report(client):
    login(client, "parent@sms.example.com")
    response = client.get("/parent/reports/1")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"


def test_teacher_can_view_attendance_form(client):
    login(client, "teacher@sms.example.com")
    response = client.get("/teacher/attendance", follow_redirects=True)
    assert response.status_code == 200
    assert b"Create Attendance" in response.data


def test_student_dashboard_loads(client):
    login(client, "student@sms.example.com")
    response = client.get("/student/")
    assert response.status_code == 200
    assert b"Student Dashboard" in response.data


def test_admin_student_teacher_and_leave_pages_load(client):
    login(client, "admin@sms.example.com")
    assert b"Students" in client.get("/admin/students").data
    assert b"Teachers" in client.get("/admin/teachers").data
    assert b"Leave Requests" in client.get("/admin/leave").data


def test_parent_leave_page_loads(client):
    login(client, "parent@sms.example.com")
    response = client.get("/parent/leave")
    assert response.status_code == 200
    assert b"Submit Leave Request" in response.data


def test_teacher_students_and_leave_pages_load(client):
    login(client, "teacher@sms.example.com")
    assert b"Students List" in client.get("/teacher/students").data
    assert b"Leave Requests" in client.get("/teacher/leave").data
    assert b"Create Attendance" in client.get("/teacher/attendance/create").data
    assert b"Attendance Records" in client.get("/teacher/attendance/records").data
    assert b"Create Assignment" in client.get("/teacher/assignments/create").data
    assert b"Assignment Records" in client.get("/teacher/assignments/records").data
    assert b"Enter Grade" in client.get("/teacher/grades/create").data
    assert b"Grade Records" in client.get("/teacher/grades/records").data
    assert b"Send Message" in client.get("/teacher/messages/send").data
    assert b"Inbox" in client.get("/teacher/messages/inbox").data


def test_teacher_only_sees_corresponding_students(client):
    login(client, "teacher@sms.example.com")
    response = client.get("/teacher/students")
    assert b"Min Thu" in response.data
    assert b"Hnin Thu" in response.data
    assert b"Aye Chan" not in response.data


def test_management_notice_dashboard_loads(client):
    login(client, "admin@sms.example.com")
    response = client.get("/admin/notices")
    assert response.status_code == 200
    assert b"Notice Dashboard" in response.data


def test_teacher_can_update_corresponding_leave_status(client):
    login(client, "teacher@sms.example.com")
    response = client.post("/teacher/leave/1/set/approved", follow_redirects=True)
    assert response.status_code == 200
    assert b"Approved" in response.data
    response = client.post("/teacher/leave/1/set/refused", follow_redirects=True)
    assert b"Refused" in response.data
    response = client.post("/teacher/leave/1/set/draft", follow_redirects=True)
    assert b"Draft" in response.data


def test_management_detail_pages_load(client):
    login(client, "admin@sms.example.com")
    for path in [
        "/admin/students/1",
        "/admin/parents",
        "/admin/parents/1",
        "/admin/classes",
        "/admin/classes/1",
        "/admin/timetable",
        "/admin/timetable/1",
        "/admin/leave/1",
        "/admin/settings",
    ]:
        assert client.get(path).status_code == 200


def test_admin_teacher_and_parent_search_filters(client):
    login(client, "admin@sms.example.com")
    response = client.get("/admin/teachers?q=T-1001")
    assert b"Daw May Hnin" in response.data

    response = client.get("/admin/parents?q=Min Thu")
    assert b"U Aung Ko" in response.data


def test_global_search_dispatches_to_role_student_list(client):
    login(client, "teacher@sms.example.com")
    response = client.get("/search?q=Min", follow_redirects=True)
    assert b"Students List" in response.data
    assert b"Min Thu" in response.data
    assert b"Hnin Thu" not in response.data


def test_management_settings_can_be_updated(client):
    login(client, "admin@sms.example.com")
    response = client.post(
        "/admin/settings",
        data={
            "school_name": "Future Leaders School",
            "academic_session": "2027-28",
            "timezone": "Asia/Yangon",
            "attendance_alert_threshold": "90",
            "default_grade_start": "1",
            "default_grade_end": "12",
            "attendance_mode": "daily_class",
            "default_notice_audience": "teachers",
            "notice_approval_required": "y",
            "teacher_leave_decisions_enabled": "y",
            "parent_leave_requests_enabled": "y",
            "portal_message": "Welcome back to the portal.",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"System settings updated." in response.data
    assert b"Future Leaders School" in response.data
    assert b"2027-28" in response.data


def test_settings_can_create_user_change_password_and_link_profile(client):
    login(client, "admin@sms.example.com")
    response = client.post(
        "/admin/settings/users/create",
        data={
            "account-email": "aye.login@sms.example.com",
            "account-role": "student",
            "account-password": "OldPass123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"User account created" in response.data

    with client.application.app_context():
        user = User.query.filter_by(email="aye.login@sms.example.com").one()
        user_id = user.id

    response = client.post(
        "/admin/settings/users/password",
        data={"password-user_id": user_id, "password-password": "NewPass123"},
        follow_redirects=True,
    )
    assert b"User password changed." in response.data

    response = client.post(
        "/admin/settings/users/link",
        data={"link-profile_ref": "student:3", "link-user_id": user_id},
        follow_redirects=True,
    )
    assert b"User account connected to profile." in response.data

    client.post("/auth/logout")
    response = login(client, "aye.login@sms.example.com", "NewPass123")
    assert b"Student Dashboard" in response.data


def test_settings_can_create_managed_grade(client):
    login(client, "admin@sms.example.com")
    response = client.post(
        "/admin/settings/grades/create",
        data={"grade-sequence": "13"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Grade 13 created with code G13." in response.data

    with client.application.app_context():
        grade = GradeLevel.query.filter_by(name="Grade 13").one()
        assert grade.code == "G13"


def test_settings_can_create_department(client):
    login(client, "admin@sms.example.com")
    response = client.post(
        "/admin/settings/departments/create",
        data={"department-name": "Computer Science", "department-code": "CS"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Computer Science department created." in response.data

    with client.application.app_context():
        department = Department.query.filter_by(name="Computer Science").one()
        assert department.code == "CS"


def test_teacher_create_uses_grade_multiselect_and_auto_staff_code(client):
    login(client, "admin@sms.example.com")
    response = client.post(
        "/admin/teachers/new",
        data={
            "email": "grade8.teacher@sms.example.com",
            "password": "Password123",
            "full_name": "Daw Grade Eight",
            "department": "Science",
            "grade_ids": ["8"],
            "position": "teacher",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Teacher saved." in response.data

    with client.application.app_context():
        teacher = Teacher.query.filter_by(full_name="Daw Grade Eight").one()
        assert teacher.staff_code == "G08T001"
        assert [grade.name for grade in teacher.grade_levels] == ["Grade 8"]


def test_student_create_generates_grade_based_code_and_filters_classes(client):
    login(client, "admin@sms.example.com")
    response = client.get("/admin/students/new?year_group=Grade+8")
    assert b"Grade 8 A - English" in response.data
    assert b"Grade 10 A - Mathematics" not in response.data

    response = client.post(
        "/admin/students/new",
        data={
            "email": "new.grade8@sms.example.com",
            "password": "Password123",
            "full_name": "Mg New Grade",
            "year_group": "Grade 8",
            "date_of_birth": "2013-01-01",
            "address": "Yangon",
            "emergency_contact_name": "Guardian",
            "emergency_contact_phone": "+950000",
            "medical_notes": "",
            "parent_ids": "0",
            "class_ids": ["3"],
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Student saved." in response.data

    with client.application.app_context():
        student = Student.query.filter_by(full_name="Mg New Grade").one()
        assert student.student_code == "G08001"
        assert student.classes[0].year_group == "Grade 8"


def test_class_form_filters_students_by_selected_grade(client):
    login(client, "admin@sms.example.com")
    response = client.get("/admin/classes/new?year_group=Grade+8")
    assert response.status_code == 200
    assert b"Aye Chan" in response.data
    assert b"Min Thu" not in response.data
    assert b"Hnin Thu" not in response.data


def test_class_create_rejects_student_from_another_grade(client):
    login(client, "admin@sms.example.com")
    response = client.post(
        "/admin/classes/new",
        data={
            "teacher_id": "1",
            "name": "Grade 8B Science",
            "subject": "Science",
            "year_group": "Grade 8",
            "section": "B",
            "room": "C103",
            "student_ids": ["1"],
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Only students from the selected grade" in response.data


def test_class_and_timetable_lists_are_grouped_by_grade(client):
    login(client, "admin@sms.example.com")
    response = client.get("/admin/classes")
    assert b"Grade 8" in response.data
    assert b"Grade 10" in response.data

    response = client.get("/admin/timetable?year_group=Grade+8")
    assert b"Grade 8A English" in response.data
    assert b"Grade 10A Mathematics" not in response.data


def test_timetable_rejects_overlapping_class_slot(client):
    login(client, "admin@sms.example.com")
    response = client.post(
        "/admin/timetable/new",
        data={
            "class_id": "1",
            "day_of_week": "Monday",
            "start_time": "09:30",
            "end_time": "10:30",
            "period": "Overlap",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"This class already has a timetable slot at that time." in response.data


def test_notifications_can_be_marked_read(client):
    login(client, "parent@sms.example.com")
    response = client.get("/parent/")
    assert b"1 unread" in response.data
    response = client.post("/notifications/read", follow_redirects=True)
    assert response.status_code == 200
    assert b"0 unread" in response.data


def test_parent_student_detail_and_timetable_load(client):
    login(client, "parent@sms.example.com")
    assert client.get("/parent/students/1").status_code == 200
    assert client.get("/parent/students/1/timetable").status_code == 200
    assert client.get("/parent/timetable").status_code == 200


def test_student_timetable_and_assignment_upload(client):
    login(client, "student@sms.example.com")
    response = client.get("/student/timetable")
    assert response.status_code == 200
    assert b"weekly class calendar" in response.data
    assert client.get("/student/assignments").status_code == 200

    response = client.post(
        "/student/assignments/1/upload",
        data={"file": (BytesIO(b"homework"), "homework.txt"), "note": "Submitted"},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Assignment uploaded." in response.data

    response = client.post(
        "/student/assignments/1/upload",
        data={"file": (BytesIO(b"new homework"), "homework2.txt"), "note": "Updated"},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"Assignment re-uploaded." in response.data


def test_student_cannot_upload_after_assignment_deadline(client):
    with client.application.app_context():
        school_class = db.session.get(SchoolClass, 1)
        assignment = Assignment(
            school_class=school_class,
            title="Closed Assignment",
            max_mark=100,
            weight_pct=10,
            due_date=date.today() - timedelta(days=1),
        )
        db.session.add(assignment)
        db.session.commit()
        assignment_id = assignment.id

    login(client, "student@sms.example.com")
    response = client.post(
        f"/student/assignments/{assignment_id}/upload",
        data={"file": (BytesIO(b"late"), "late.txt"), "note": "Late"},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"The upload deadline has passed." in response.data


def test_teacher_attendance_month_calendar_and_day_detail(client):
    with client.application.app_context():
        row = Attendance.query.filter_by(status="absent").order_by(Attendance.session_date.desc()).first()
        selected_date = row.session_date

    login(client, "teacher@sms.example.com")
    response = client.get(f"/teacher/attendance/records?month={selected_date.month}&year={selected_date.year}")
    assert response.status_code == 200
    assert b"Click a day for details" in response.data
    assert b"Absent students" not in response.data

    response = client.get(f"/teacher/attendance/records/{selected_date.isoformat()}")
    assert response.status_code == 200
    assert b"Absent Students" in response.data


def test_teacher_can_save_whole_class_attendance(client):
    login(client, "teacher@sms.example.com")
    response = client.get("/teacher/attendance/create?year_group=Grade+10&class_id=1")
    assert response.status_code == 200
    assert b"Min Thu" in response.data
    assert b"Hnin Thu" in response.data

    response = client.post(
        "/teacher/attendance/create?year_group=Grade+10&class_id=1",
        data={
            "class_id": "1",
            "session_date": date.today().isoformat(),
            "present_student_ids": ["1"],
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Attendance saved for 2 students" in response.data

    with client.application.app_context():
        records = Attendance.query.filter_by(class_id=1, session_date=date.today()).all()
        statuses = {row.student_id: row.status for row in records}
        assert statuses == {1: "present", 2: "absent"}


def test_teacher_attendance_detail_is_scoped_by_class(client):
    login(client, "teacher@sms.example.com")
    response = client.get(
        f"/teacher/attendance/records/{date.today().isoformat()}?year_group=Grade+10&class_id=1"
    )
    assert response.status_code == 200
    assert b"Grade 10A Mathematics" in response.data
    assert b"Grade 10A Science" not in response.data
