def login(client, email, password="Password123"):
    return client.post("/auth/login", data={"email": email, "password": password}, follow_redirects=True)


def test_login_redirects_to_role_dashboard(client):
    response = login(client, "admin@sms.example.com")
    assert response.status_code == 200
    assert b"Management Dashboard" in response.data


def test_invalid_login_shows_error(client):
    response = login(client, "admin@sms.example.com", "wrong")
    assert b"Invalid email or password" in response.data


def test_role_protection_blocks_wrong_role(client):
    login(client, "student@sms.example.com")
    response = client.get("/admin/")
    assert response.status_code == 403
