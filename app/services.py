from io import BytesIO

from flask import current_app
from flask_mail import Message as MailMessage
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .extensions import mail
from .models import Student


def send_attendance_alert(student: Student):
    if student.attendance_percentage >= current_app.config["ATTENDANCE_ALERT_THRESHOLD"]:
        return False

    recipients = [parent.user.email for parent in student.parents]
    if not recipients:
        return False

    msg = MailMessage(
        subject=f"Attendance alert for {student.full_name}",
        recipients=recipients,
        body=(
            f"{student.full_name}'s attendance is currently "
            f"{student.attendance_percentage}%, below the configured threshold."
        ),
    )
    mail.send(msg)
    return True


def build_student_report_pdf(student: Student):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 72

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(72, y, "Academic Progress Report")
    y -= 34

    pdf.setFont("Helvetica", 11)
    for label, value in [
        ("Student", student.full_name),
        ("Student code", student.student_code),
        ("Year group", student.year_group),
        ("Attendance", f"{student.attendance_percentage}%"),
    ]:
        pdf.drawString(72, y, f"{label}: {value}")
        y -= 18

    y -= 10
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(72, y, "Grades")
    y -= 22
    pdf.setFont("Helvetica", 10)
    if not student.grades:
        pdf.drawString(72, y, "No grades have been recorded yet.")
    for grade in student.grades:
        assignment = grade.assignment
        pdf.drawString(
            72,
            y,
            f"{assignment.school_class.subject} - {assignment.title}: "
            f"{grade.mark}/{assignment.max_mark} ({grade.letter_grade})",
        )
        y -= 16
        if y < 72:
            pdf.showPage()
            y = height - 72
            pdf.setFont("Helvetica", 10)

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer
