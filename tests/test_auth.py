def login(client, email, password="Password123"):
    return client.post("/auth/login", data={"email": email, "password": password}, follow_redirects=True)


def test_login_redirects_to_role_dashboard(client):
    response = login(client, "admin@sms.example.com")
    assert response.status_code == 200
    assert b"Management Dashboard" in response.data


def test_login_page_lists_all_six_demo_roles(client):
    response = client.get("/auth/login")
    for role in [b"Admin", b"Headmaster", b"Dean", b"Teacher", b"Parent", b"Student"]:
        assert role in response.data


def test_headmaster_and_dean_login_to_management_dashboard(client):
    for email in ["headmaster@sms.example.com", "dean@sms.example.com"]:
        response = login(client, email)
        assert b"Management Dashboard" in response.data
        client.post("/auth/logout")


def test_invalid_login_shows_error(client):
    response = login(client, "admin@sms.example.com", "wrong")
    assert b"Invalid email or password" in response.data


def test_parent_signup_creates_account_and_signs_in(client):
    response = client.post(
        "/auth/signup",
        data={
            "role": "parent",
            "full_name": "New Guardian",
            "email": "new.parent@sms.example.com",
            "password": "Password123",
            "confirm_password": "Password123",
            "phone": "555-0101",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Account created successfully" in response.data
    assert b"Parent workspace" in response.data


def test_role_protection_blocks_wrong_role(client):
    login(client, "student@sms.example.com")
    response = client.get("/admin/")
    assert response.status_code == 403
