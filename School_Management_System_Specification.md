# Web-Based School Management System — Full Build Specification

**Student:** Bhone Myint Thu (bj21eh) — BSc Computer Science, CET300 Computing Project
**Institution:** University of Sunderland | **Supervisor:** Dr. Yan Naung Soe
**Source documents:** Project Proposal, Definitive Brief, Project Schedule, Software Methodologies, PACT Analysis, Heuristic Evaluation, ER Diagram, UI Wireframes

---

## 1. Project Overview

A full-stack, multi-role **Web-Based School Management System (SMS)** with a Parent Portal and advanced academic features, built entirely in Python. It replaces fragmented, paper-based, or disconnected school admin tools with a single secure platform covering student records, attendance, grades, timetables, and parent–teacher communication.

**Four user roles:** Administrator, Teacher, Parent, Student — each with a role-specific dashboard and strictly enforced permissions.

---

## 2. Technology Stack (Languages & Tools)

| Layer | Technology |
|---|---|
| **Primary language** | Python 3.10+ |
| **Back-end framework** | Flask (micro-framework, RESTful routing) |
| **ORM / Database layer** | SQLAlchemy / Flask-SQLAlchemy |
| **Database** | SQLite (development) → MySQL or PostgreSQL (production) |
| **Authentication** | Flask-Login (session-based auth) |
| **Forms & CSRF protection** | Flask-WTF |
| **Password hashing** | Werkzeug / bcrypt |
| **Email notifications** | Flask-Mail |
| **Templating (front-end)** | Jinja2 (server-side rendering) |
| **Front-end markup/styling** | HTML5, CSS3, Bootstrap 5 |
| **Client-side scripting** | Vanilla JavaScript |
| **Data visualisation** | Chart.js (grade & attendance analytics) |
| **PDF report generation** | ReportLab (Python library) |
| **Version control** | Git & GitHub |
| **IDE** | PyCharm or VS Code |
| **API/route testing** | Postman |
| **DB inspection** | DB Browser for SQLite / MySQL Workbench |
| **Wireframing/UI design** | Figma |
| **Testing** | pytest (unit tests) + manual UAT |
| **Deployment** | PythonAnywhere or Render (free tier) |

**Why Flask over Django:** chosen for its lightweight, composable architecture — each concern (auth, forms, ORM, mail) is a separate library that can be learned and tested independently, better suited to a solo learning-focused project than Django's "batteries-included" monolith.

**Why SQL over NoSQL:** the data is inherently relational (students belong to classes, attendance links student+session+date, grades link student+assignment), so a relational DB with SQLAlchemy is the correct fit.

---

## 3. Database Design (from ER Diagram — 11 Entities)

| Entity | Key Fields | Relationships |
|---|---|---|
| **USER** | id (PK), email, password_hash, role, created_at | 1:1 with Student/Parent/Teacher |
| **STUDENT** | id (PK), user_id (FK), full_name, year_group, date_of_birth, student_code | 1:M with Attendance, Grade; M:M with Parent via Parent_Student |
| **PARENT** | id (PK), user_id (FK), full_name, phone | M:M with Student via Parent_Student |
| **TEACHER** | id (PK), user_id (FK), full_name, department, staff_code | 1:M with Class |
| **PARENT_STUDENT** (join table) | parent_id (FK), student_id (FK) | resolves many-to-many parent↔child |
| **CLASS** | id (PK), teacher_id (FK), name, subject, year_group, room | 1:M with Attendance, Timetable, Assignment |
| **ATTENDANCE** | id (PK), class_id (FK), student_id (FK), session_date, status, note, marked_at | linked to Class & Student |
| **TIMETABLE** | id (PK), class_id (FK), day_of_week, start_time, end_time, period | linked to Class |
| **ASSIGNMENT** | id (PK), class_id (FK), title, max_mark, weight_pct, due_date, created_at | 1:M with Grade |
| **GRADE** | id (PK), assignment_id (FK), student_id (FK), mark, letter_grade, feedback, graded_at | linked to Assignment & Student |
| **MESSAGE** | id (PK), sender_id (FK), recipient_id (FK), subject, body, is_read, sent_at | supports in-system teacher↔parent messaging |

**Cardinalities:** User↔Student/Parent/Teacher = 1:1; Teacher↔Class = 1:M; Class↔Attendance/Timetable/Assignment = 1:M; Assignment↔Grade = 1:M; Parent↔Student = M:M (via Parent_Student join table); Student/Parent↔Message = 1:M (sends/receives).

---

## 4. UI Screens (from Wireframes)

1. **Login** — role-based authentication entry point
2. **Admin Dashboard** — manage students/teachers/classes, timetable builder, academic calendar, school-wide reports
3. **Teacher Dashboard** — mark attendance, create/grade assignments, message parents
4. **Attendance/Grade entry views** — table-based interfaces with dropdowns/date pickers for error prevention
5. **Parent Portal** — real-time attendance %, grade summaries, assignment deadlines, teacher messaging, PDF report download
6. **Student Dashboard** — personal timetable, attendance %, recent grades, upcoming assignments, announcements, grade-trend chart

**Design system:** navy/blue palette, sidebar navigation (persistent across roles — supports Nielsen's "recognition over recall"), stat cards with colour-coded accent bars, Chart.js bar/line charts, Bootstrap 5 responsive grid (mobile-first for the Parent Portal per NFR2).

---

## 5. Functional Requirements (FR)

| ID | Requirement |
|---|---|
| FR1 | Four distinct user roles with role-specific access permissions |
| FR2 | Admin: add/edit/delete student & teacher records, manage classes, configure academic calendar |
| FR3 | Teacher: mark attendance per session, create/grade assignments, message parents |
| FR4 | Parent Portal: real-time attendance summary, grade progress, deadlines, messages for their child |
| FR5 | Student view: timetable, attendance, grade history, assignments |
| FR6 | Downloadable PDF academic reports (ReportLab) |
| FR7 | Automated email alert (Flask-Mail) when attendance drops below a configurable threshold |
| FR8 | In-system messaging between teachers and parents |
| FR9 | All passwords stored as bcrypt hashes — never plain text |
| FR10 | Search/filter function for student records (Admin) |

## 6. Non-Functional Requirements (NFR)

| ID | Requirement |
|---|---|
| NFR1 | Pages load within 3s; PDF generation ≤10s |
| NFR2 | Fully responsive: mobile (375px+), tablet (768px+), desktop (1024px+) |
| NFR3 | Flask-Login route protection, CSRF tokens on all forms, HTTPS in production |
| NFR4 | GDPR-compliant: only necessary data collected; test data fully fictitious |
| NFR5 | WCAG 2.1 AA accessibility (4.5:1 contrast, semantic HTML5, alt text) |
| NFR6 | PEP 8 style, docstrings, Git version control with meaningful commits |
| NFR7 | Target 99% uptime on free-tier deployment |

---

## 7. Methodology

**Hybrid: Agile (Scrum-inspired sprints) + Iterative Prototyping** for UI/UX.

- Agile chosen because the system decomposes naturally into independently testable modules (auth, records, attendance, grades, portal, notifications), fits a solo 400-hour/23-week schedule, and produces demonstrable increments for fortnightly supervisor reviews.
- Iterative Prototyping (Figma wireframes → PACT analysis → Heuristic evaluation → peer review → build → UAT refinement) governs the front-end design process.
- **Waterfall was rejected**: requires fully specified requirements upfront and gives no testable output until late — incompatible with a project where interaction details emerge only once prototypes are tested, and with the need for regular demonstrable progress.

### Sprint Breakdown

| Sprint | Focus | Dates |
|---|---|---|
| 1 | Research (Flask vs Django, SQL vs NoSQL), PACT, heuristic eval, wireframes, ER diagram | 01/03 – 21/03/2026 |
| 2 | Flask setup, SQLAlchemy models, Jinja2 base templates, routing | 23/03 – 11/04/2026 |
| 3 | Auth: Flask-Login, bcrypt, CSRF (Flask-WTF), RBAC route protection | 13/04 – 25/04/2026 |
| 4 | Front-end: all 4 dashboards, full CRUD, Chart.js analytics | 27/04 – 22/05/2026 |
| 5 | Integration: Flask-Mail alerts, messaging, ReportLab PDFs | 24/05 – 13/06/2026 |
| 6 | Testing & deployment: pytest, UAT, bug fixing, PythonAnywhere/Render | 15/06 – 10/07/2026 |
| 7 | Final report & presentation | 12/07 – 07/08/2026 |

---

## 8. Step-by-Step Build Plan

### Phase 1 — Setup & Foundation
1. Initialise Git repository and Python virtual environment.
2. Install Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF, Flask-Mail, bcrypt/Werkzeug, ReportLab.
3. Create Flask app factory structure (`app/`, `templates/`, `static/`, `config.py`).
4. Set up SQLite database and confirm connection.

### Phase 2 — Data Layer
5. Translate the ER diagram into SQLAlchemy models: `User`, `Student`, `Parent`, `Teacher`, `ParentStudent`, `Class`, `Attendance`, `Timetable`, `Assignment`, `Grade`, `Message`.
6. Define relationships (1:1, 1:M, M:M) exactly as mapped in Section 3.
7. Run migrations / `db.create_all()` and seed with fictitious test data.
8. Build a CRUD data-access layer for each entity.

### Phase 3 — Authentication & Security
9. Implement registration (admin-managed) and login/logout routes.
10. Hash all passwords with bcrypt; never store plain text (FR9).
11. Configure Flask-Login for session management; add `@login_required` and role-based decorators.
12. Add CSRF protection via Flask-WTF to every form (NFR3).

### Phase 4 — Core Modules (per role)
13. **Admin module:** student/teacher CRUD, class/timetable management, academic calendar, school-wide reports, search/filter (FR2, FR10).
14. **Teacher module:** attendance marking UI, assignment creation/grading, mark entry (FR3).
15. **Student module:** read-only views of timetable, attendance, grades, assignments (FR5).
16. **Parent module:** dashboard aggregating child's attendance %, grades, deadlines; messaging inbox (FR4, FR8).

### Phase 5 — Advanced Features
17. Integrate Chart.js for grade-trend and attendance visualisations on Jinja2 templates.
18. Build the in-system messaging feature (Message model + inbox UI).
19. Configure Flask-Mail and write a scheduled/triggered job to send attendance-threshold warning emails (FR7).
20. Implement ReportLab PDF export for academic progress reports (FR6).

### Phase 6 — Front-End Polish
21. Style all templates with Bootstrap 5 for a responsive, mobile-first layout (NFR2), matching the wireframes' sidebar-nav + stat-card pattern.
22. Apply WCAG 2.1 AA accessibility checks: colour contrast, semantic tags, alt text (NFR5).
23. Incorporate heuristic-evaluation fixes: visible system status (loading/success alerts), plain school-language labels, confirm-before-delete dialogs, consistent components.

### Phase 7 — Testing & Deployment
24. Write pytest unit tests for models, routes, and auth logic.
25. Conduct manual User Acceptance Testing with representative user-role scenarios (using fictitious data + signed consent forms per the Ethics/Consent docs).
26. Fix bugs and verify responsiveness across breakpoints.
27. Deploy to PythonAnywhere or Render with HTTPS and environment-variable secrets.

### Phase 8 — Documentation
28. Write the final technical report: requirements analysis, design (ER/UML diagrams), implementation, testing results, critical evaluation.
29. Prepare presentation slides summarising the project.

---

## 9. Ethical & Legal Considerations

- No real student/child data at any stage — all data fictitious and anonymised.
- GDPR (UK Data Protection Act 2018) compliance: data minimisation, purpose limitation, secure storage.
- RBAC via Flask-Login ensures each role only accesses relevant data.
- Passwords bcrypt-hashed; CSRF tokens on all forms; HTTPS in production.
- No DBS check required — no direct contact with minors/vulnerable persons.
- Any usability testing with human participants requires signed informed consent (see Participant Information Sheet & Consent Form).

---

## 10. Key References

- Epstein, J. L. (2011) *School, Family, and Community Partnerships.* Westview Press.
- Grinberg, M. (2018) *Flask Web Development.* O'Reilly Media.
- Connolly, T. and Begg, C. (2014) *Database Systems.* Pearson.
- Sommerville, I. (2016) *Software Engineering.* Pearson.
- Goodall, J. and Montgomery, C. (2014) 'Parental involvement to parental engagement', *Educational Review*, 66(4).
- Uka, E. (2019) 'Web Based Students' Record Management System for Tertiary Institutions', *IJSER*, 10(3).
- Nielsen, J. (1994) *Usability Engineering.* Academic Press.
