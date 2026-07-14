from test_auth import login

from app.models import User


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
