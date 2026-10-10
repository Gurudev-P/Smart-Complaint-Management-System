# Smart Complaint Management System

## Project Information

**Project ID:** 67  
**Team Name:** Gundu Guru  
**Institution:** PES University  
**Department:** Computer Science and Engineering (AI&ML)

## Project Description

The Smart Complaint Management System (SCMS) is a web-based platform for lodging, categorizing, assigning, tracking, escalating, and resolving complaints. It supports role-based access for users, staff/resolvers, and administrators, together with SLA monitoring, in-app notifications, dashboards, and CSV reporting.

## Team Members

| Name | SRN |
|---|---|
| Purum Gurudev | PES2UG24AM125 |
| Prashyanth V | PES2UG24AM120 |
| Aditya Pradeep | PES2UG24AM900 |
| Nihar S Jain | PES2UG24AM104 |

## Security and Demo Accounts

The repository includes **local demonstration credentials** for repeatable coursework testing. They are not production credentials. Do not expose a shared or internet-facing deployment with the default Docker Compose secret or demo passwords. Set unique values for `SECRET_KEY`, `ADMIN_EMAIL`, and `ADMIN_PASSWORD` outside source control before any shared deployment. Never commit `.env` files or database dumps.

## Getting Started

### Option A — Docker (recommended)

From the repository root:

```bash
docker compose up --build
```

In a second terminal, seed the local demonstration users and categories:

```bash
docker compose exec app python -m backend.app.seed
```

Open http://localhost:8000. The default local administrator is `admin@scms.example.com` / `Admin@1234`. Change the defaults before sharing the service beyond a trusted local demonstration environment.

### Option B — Local Python

Requires Python 3.11+ and PostgreSQL 14+.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
# Edit DATABASE_URL and set a unique SECRET_KEY in .env.
alembic upgrade head
python -m backend.app.seed
uvicorn backend.app.main:app --reload
```

- Web app: http://localhost:8000
- Interactive API docs (Swagger): http://localhost:8000/docs

The seed script creates local demo users, default complaint categories, and default SLA rules if they do not already exist.

| Role | Email | Local demo password |
|---|---|---|
| Administrator | admin@scms.example.com | Admin@1234 |
| Staff | staff1@scms.example.com | Staff@1234 |
| Staff | staff2@scms.example.com | Staff@1234 |
| User | user@scms.example.com | User@1234 |

### Running the Tests

Run from the repository root. The PostgreSQL tests require a separate test database; do not point `TEST_DATABASE_URL` at a database containing data you need to keep.

```bash
pytest tests --ignore=tests/e2e --cov=backend/app
TEST_DATABASE_URL=postgresql+psycopg://user:pass@localhost/scms_test pytest tests --ignore=tests/e2e
python -m playwright install chromium && pytest tests/e2e
node --test tests/frontend/*.test.mjs
ruff check backend tests
python tests/perf/load_test.py --url http://localhost:8000 --users 50
```

The load test requires a running application. CI configuration is in `.github/workflows/ci.yml`; check the [latest GitHub Actions runs](https://github.com/Gurudev-P/Smart-Complaint-Management-System/actions) for current results. Jenkins is also configured through `Jenkinsfile`, which currently contains developer-machine-specific paths and should be reviewed before running it on another host.

## Repository Structure

```text
backend/app/             FastAPI routes, services, repositories, schemas and models
database/migrations/     Alembic migration history
frontend/                HTML, CSS and JavaScript web client
tests/                   Unit, API, browser E2E, frontend and load tests
docs/                    Requirements, planning, design, test, validation and release documents
.github/workflows/ci.yml GitHub Actions lint and test workflow
Jenkinsfile              Jenkins pipeline for the recorded development environment
```

## Documentation

- [Software Requirements Specification](docs/SRS/README.md) — [Word document](docs/SRS/SRS_Smart_Complaint_Management_System.docx)
- [Project Plan](docs/Project-Plan/README.md) — [Word document](docs/Project-Plan/Project_Plan_Smart_Complaint_Management_System.docx)
- [High-Level Architecture](docs/Architecture/README.md) — [Word document](docs/Architecture/High_Level_Architecture_Smart_Complaint_Management_System.docx)
- [Software Design](docs/Software_Design/README.md) — [Word document](docs/Software_Design/Software_Design_Smart_Complaint_Management_System.docx)
- [Implementation Design Refinements Addendum](docs/Software_Design/Implementation_Refinements_Addendum.md)
- [Test Plan and Test Report](docs/Testing/README.md) — [Word document](docs/Testing/Test_Plan_and_Report_Smart_Complaint_Management_System.docx)
- [System Validation Report](docs/Validation/README.md) — [Word document](docs/Validation/System_Validation_Report_Smart_Complaint_Management_System.docx)
- [Final Project Report](docs/Final-Report/Final_Project_Report_Smart_Complaint_Management_System.docx)
- [Product Maintenance Plan — Markdown reference](docs/Maintenance-Plan/Product_Maintenance_Plan_Smart_Complaint_Management_System.md)
- [Product Maintenance Plan — Word copy](docs/Maintenance-Plan/SCMS_Product_Maintenance_Plan.docx)
- [Final Submission Readiness Checklist](docs/FINAL_SUBMISSION_READINESS.md)

## Current Project Status

**Status as of 10 October 2026:** the core implementation for the repository's SRS v1.0 baseline is present. Requirements, architecture, detailed design, implementation, the test report, system validation, and a Sections 1–6 working-baseline final report are available. The validation report records 207 passing automated tests, 94.6% backend statement coverage, and 41/41 baseline requirements validated; those figures describe the recorded validation run, not a guarantee of current production behavior.

GitHub Actions is enabled and the latest known run on the reviewed main commit passed. Check the Actions page for the latest state after subsequent changes.

The project is **not yet at final submission freeze**. Remaining team deliverables include confirming GitHub Project/backlog fields, recording and uploading the one-minute Sprint 1 video (19–23 October) and two-minute Sprint 2 video (26–30 October), reviewing documentation/version discrepancies, checking the final report and any required PDF export, and freezing development after final checks. Track these items in the [readiness checklist](docs/FINAL_SUBMISSION_READINESS.md).

The Test Plan refers to proposed SRS v1.1 additions (feedback/reopen, attachments, departments, and login lockout) as outside the v1.0 design baseline. Do not present those additions as implemented features unless the team adopts an approved updated requirements baseline.
