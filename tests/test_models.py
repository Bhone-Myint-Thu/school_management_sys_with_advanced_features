from app.models import Student, User, letter_for_mark


def test_seeded_passwords_are_hashed(app):
    with app.app_context():
        user = User.query.filter_by(email="admin@sms.example.com").one()
        assert user.password_hash != "Password123"
        assert user.check_password("Password123")


def test_attendance_percentage(app):
    with app.app_context():
        student = Student.query.filter_by(student_code="S-1001").one()
        assert student.attendance_percentage == 80.0


def test_letter_grade_boundaries():
    assert letter_for_mark(70) == "A"
    assert letter_for_mark(60) == "B"
    assert letter_for_mark(50) == "C"
    assert letter_for_mark(40) == "D"
    assert letter_for_mark(39) == "F"
