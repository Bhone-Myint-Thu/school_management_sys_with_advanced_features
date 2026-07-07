# Web-Based School Management System

Flask implementation of the CET300 School Management System specification. The project is intentionally self-contained and uses SQLite by default, so it does not touch local PostgreSQL, pyenv, or Odoo services.

## Features

- Four roles: administrator, teacher, parent, student
- Flask-Login authentication with hashed passwords
- CSRF-protected Flask-WTF forms
- SQLAlchemy models for all 11 ERD entities
- Admin records, class, timetable, and student search views
- Student list, teacher list, and leave request management pages
- Headmaster/dean notice approval dashboard and scoped teacher access
- Grade/class filters for students, teachers, classes, timetable, and dashboard attendance
- Teacher attendance, assignment, grading, and parent messaging tools
- Parent portal with attendance/grade overview, leave requests, and ReportLab PDF export
- Student dashboard with timetable, assignments, and Chart.js grade trend
- Flask-Mail attendance alert hook with sending suppressed by default
- Fictitious demo data only

## Local Setup

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
flask init-db
flask run
```

Open `http://127.0.0.1:5000`.

Demo accounts all use `Password123`:

- `admin@sms.example.com`
- `headmaster@sms.example.com`
- `dean@sms.example.com`
- `teacher@sms.example.com`
- `teacher2@sms.example.com`
- `parent@sms.example.com`
- `parent2@sms.example.com`
- `student@sms.example.com`
- `student2@sms.example.com`
- `student3@sms.example.com`

## Environment

Copy `.env.example` values into your shell or deployment dashboard. `DATABASE_URL` defaults to a local SQLite file inside `instance/`.

For email testing, configure `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`, and set `MAIL_SUPPRESS_SEND=False`.

## Tests

```bash
pytest
```
