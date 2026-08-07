# EduManage Pro — School Management System

EduManage Pro is a role-based school portal built with Flask. It provides separate workspaces for administrators, school leaders, teachers, parents, and students. The project uses SQLite by default and includes fictitious demonstration data, making it suitable for development, assessment, and presentations.

## Main Features

- Six roles: administrator, headmaster, dean, teacher, parent, and student
- Secure authentication with hashed passwords and role-protected pages
- Student, parent, teacher, class, grade-level, and department management
- Class timetables, attendance, assignments, submissions, and grades
- Parent leave requests and staff approval workflows
- Teacher-parent messaging and portal notifications
- Headmaster notice approval workflow
- Parent PDF student reports
- Student assignment uploads and grade trend charts
- Light and dark display themes
- Search and grade/class filters throughout the portal
- Fictitious presentation data only

## Requirements

- Python 3.10 or newer
- `pip` and Python virtual-environment support
- A modern browser such as Chrome, Firefox, or Edge

SQLite is used automatically, so a separate database server is not required.

## Installation and First Run

From the project directory, create a virtual environment and install the dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create the database and load the demonstration records:

```bash
flask --app run.py init-db
```

Start the application:

```bash
flask --app run.py run
```

Open <http://127.0.0.1:5000> in a browser. Stop the development server with `Ctrl+C`.

> `init-db` deletes and recreates all application tables. Do not run it against a database containing information that you want to keep.

## Demo Accounts

Every seeded account uses the password `Password123`.

| Role | Email | Best use in a demonstration |
| --- | --- | --- |
| Administrator | `admin@sms.example.com` | Manage school records, accounts, classes, timetable, leave, and settings |
| Headmaster | `headmaster@sms.example.com` | Review school data and approve pending notices |
| Dean | `dean@sms.example.com` | Manage academic records and submit notices for approval |
| Teacher | `teacher@sms.example.com` | Attendance, assignments, grades, leave decisions, and messages |
| Teacher | `teacher2@sms.example.com` | View the Grade 8 English demonstration class |
| Teacher | `teacher3@sms.example.com` | View the Grade 9 Mathematics demonstration class |
| Parent | `parent@sms.example.com` | Monitor Min Thu and Hnin Thu |
| Parent | `parent2@sms.example.com` | Monitor Aye Chan |
| Parent | `parent3@sms.example.com` | Monitor the Grade 9 demonstration students |
| Student | `student@sms.example.com` | View Min Thu's timetable, assignments, and grades |
| Student | `student2@sms.example.com` | View Hnin Thu's records |
| Student | `student3@sms.example.com` | View Aye Chan's records |
| Student | `student4@sms.example.com` | View Su Myat Noe's Grade 9 records |
| Student | `student5@sms.example.com` | View Kaung Htet's Grade 9 records |

## General Portal Use

1. Open the login page and enter one of the demo email addresses.
2. Enter `Password123` and select **Sign in to Dashboard**.
3. Use the left sidebar to open the features available to that role.
4. Use the search bar to locate accessible students or records.
5. Select the `!` button to view recent messages and approved notices.
6. Select the sun/moon button to change between light and dark themes.
7. Select the profile avatar in the top-right corner to view account details or log out.

Each role can access only its permitted workspace. A direct attempt to open another role's protected page returns an access error.

## Role Guide

### Administrator

The administrator has a school-wide management workspace.

- **Dashboard:** review totals for students, teachers, classes, and pending leave requests. Filter attendance summaries by month, year, grade, and class.
- **Students:** search, filter, create, edit, or delete student records. Connect students to parents and classes.
- **Teachers:** manage teacher, dean, and headmaster profiles, departments, and assigned grade levels.
- **Parents:** maintain guardian contact information and linked students.
- **Classes:** create classes, select the grade and teacher, and enroll students from the same grade.
- **Timetable:** create and review class periods, rooms, days, and start/end times.
- **Leave:** review requests and record an approved, refused, or draft decision with a response note.
- **Notices:** create announcements. When notice approval is enabled, administrator notices remain pending until approved by the headmaster.
- **Settings:** update school details, academic session, attendance threshold, enabled workflows, grade levels, departments, and user accounts.

When creating a user in **Settings**, link it to the matching student, parent, or staff profile before using role-specific features.

### Headmaster

The headmaster uses the management workspace and can access the same school-wide records as management staff. The headmaster also has the final notice-approval permission.

To approve a notice:

1. Open **Notices**.
2. Locate a pending notice submitted by the administrator or dean.
3. Select **Approve**.
4. The notice becomes visible to its selected audience.

A notice created directly by the headmaster is approved immediately.

### Dean

The dean uses the management workspace for academic oversight. The dean can manage records, classes, timetables, and leave requests. Notices created by the dean are sent to the headmaster when notice approval is enabled.

### Teacher

Teachers see only students and classes assigned to their profile.

- **Students:** review assigned students and their academic details.
- **Attendance → Mark Attendance:** choose a class and date, then record each student as present, late, or absent.
- **Attendance → Check Records:** filter and review previous attendance sessions.
- **Assignment → Create Assignment:** enter a title, class, due date, maximum mark, and weighting.
- **Assignment → Records:** review assignments and download uploaded student work.
- **Grade → Enter Grade:** select an assignment and student, enter a mark, and add feedback.
- **Grade → Records:** review recorded marks and calculated letter grades.
- **Leave:** review requests for students in the teacher's classes and update their status when teacher decisions are enabled.
- **Messages:** send messages to parents and review inbox/sent items.

### Parent

Parents can access only students linked to their profile.

- **Dashboard:** view children, current notices, and recent messages.
- **Students:** open a child's profile to review attendance and grades.
- **Timetable:** view schedules for all linked children or an individual child.
- **Leave:** select a child, enter dates and a reason, and submit a leave request.
- **Messages:** contact teachers and review received or sent messages.
- **PDF Report:** open a child's details and download the available student report.

### Student

Students can access only their own academic information.

- **Dashboard:** review timetable entries, upcoming assignments, submissions, notices, and grade trends.
- **Timetable:** view the weekly class schedule.
- **Assignments:** review deadlines and upload work before the due date. Uploading again replaces the student's current submission record.

## Suggested Presentation Walkthrough

For a short end-to-end demonstration:

1. Sign in as the **Dean** and create a notice for teachers, parents, or everyone.
2. Log out, sign in as the **Headmaster**, and approve the pending notice.
3. Sign in as the **Teacher** and mark attendance, create an assignment, or enter a grade.
4. Sign in as the **Parent** to inspect the child's updated records, submit leave, send a message, and download a PDF report.
5. Sign in as the **Student** to show the timetable, assignments, notices, grade chart, and upload workflow.
6. Finish as the **Administrator** to show school-wide statistics, filters, record management, and system settings.

## Resetting Demo Data

To restore the original fictitious dataset, stop the server and run:

```bash
flask --app run.py init-db
```

This removes changes made during the presentation and recreates the SQLite database with demo users, Grade 8–10 classes, attendance, grades, assignments, leave requests, messages, and notices.

## Configuration

The defaults work without environment configuration. For a custom deployment, copy the example file and export the values appropriate to your shell or hosting platform:

```bash
cp .env.example .env
```

Important settings include:

| Variable | Purpose | Default |
| --- | --- | --- |
| `SECRET_KEY` | Session and CSRF security | Development-only value |
| `DATABASE_URL` | SQLAlchemy database connection | SQLite in `instance/` |
| `ATTENDANCE_ALERT_THRESHOLD` | Percentage used for attendance alerts | `85` |
| `MAIL_SERVER` / `MAIL_PORT` | Outgoing email server | `localhost:25` |
| `MAIL_USERNAME` / `MAIL_PASSWORD` | Optional mail authentication | Empty |
| `MAIL_DEFAULT_SENDER` | Sender used by email notifications | `noreply@sms.local` |
| `MAIL_SUPPRESS_SEND` | Prevent real email delivery | `True` |

The application reads environment variables; it does not automatically load `.env` without an environment loader or hosting-platform support.

## Assignment Uploads

Student files are stored under `instance/uploads/assignments/`. Keep that directory writable when deploying the application. Uploaded files and the SQLite database are runtime data and should be backed up if the system is used beyond a demonstration.

## Running Tests

With the virtual environment activated, run:

```bash
pytest -q
```

The tests use an in-memory SQLite database and do not overwrite the normal development database.

## Troubleshooting

- **`flask: command not found`:** activate the virtual environment with `source .venv/bin/activate`, or run `.venv/bin/flask --app run.py run`.
- **Database tables are missing:** run `flask --app run.py init-db`.
- **Login fails:** verify the email spelling and use the case-sensitive password `Password123`.
- **A page returns 403:** log in with a role permitted to use that page.
- **A teacher sees no students:** assign the teacher to a class and enroll students through the management workspace.
- **A parent sees no children:** link student records to the parent through the parent/student management forms.
- **Charts do not appear offline:** Chart.js is loaded from a CDN, so the browser needs internet access for the chart library.
- **Email is not delivered:** sending is suppressed by default; configure the mail variables and set `MAIL_SUPPRESS_SEND=False`.

## Development Notes

- Application factory: `app/create_app()`
- Development entry point: `run.py`
- Database models: `app/models.py`
- Demo seed data: `app/seed.py`
- HTML templates: `app/templates/`
- Styles and browser scripts: `app/static/`
- Automated tests: `tests/`

This repository contains fictitious school data only. Replace the development secret, review file-upload controls, configure backups, and use a production WSGI server before any real-world deployment.
