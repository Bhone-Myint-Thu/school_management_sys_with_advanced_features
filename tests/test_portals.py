from test_auth import login


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
    ]:
        assert client.get(path).status_code == 200


def test_parent_student_detail_and_timetable_load(client):
    login(client, "parent@sms.example.com")
    assert client.get("/parent/students/1").status_code == 200
    assert client.get("/parent/students/1/timetable").status_code == 200
