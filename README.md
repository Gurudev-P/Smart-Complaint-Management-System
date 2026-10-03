# Smart Complaint Management System

## Project Information

**Project ID:** 67  
**Team Name:** Gundu Guru  
**Institution:** PES University  
**Department:** Computer Science and Engineering(AI&ML)

## Project Description

The Smart Complaint Management System is a web-based platform for lodging, tracking, categorizing, assigning, escalating, and resolving complaints.

The system provides role-based access for users, staff/resolvers, and administrators. It also supports SLA monitoring, escalation, notifications, and administrative reporting.

## Team Members

| Name           | SRN           |
|----------------|---------------|
| Purum Gurudev  | PES2UG24AM125 |
| Prashyanth V   | PES2UG24AM120 |
| Aditya Pradeep | PES2UG24AM900 |
| Nihar S Jain   | PES2UG24AM104 |

## Getting Started

### Option A — Docker (recommended)

```bash
docker compose up --build
```

Open http://localhost:8000 and sign in as `admin@scms.example.com` / `Admin@1234`
(set `ADMIN_EMAIL` / `ADMIN_PASSWORD` to change the first administrator).

### Option B — Local Python

Requires Python 3.11+ and PostgreSQL 14+.

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                                   # then edit DATABASE_URL and SECRET_KEY
alembic upgrade head                                   # create the schema
python -m backend.app.seed                             # optional demo users and categories
uvicorn backend.app.main:app --reload
```

- Web app: http://localhost:8000
- Interactive API docs (Swagger): http://localhost:8000/docs

Demo accounts created by the seed script:

| Role          | Email                     | Password     |
|---------------|---------------------------|--------------|
| Administrator | admin@scms.example.com    | Admin@1234   |
| Staff         | staff1@scms.example.com   | Staff@1234   |
| Staff         | staff2@scms.example.com   | Staff@1234   |
| User          | user@scms.example.com     | User@1234    |

### Running the tests

```bash
pytest tests --ignore=tests/e2e --cov=backend/app        # unit + API (SQLite in memory)
TEST_DATABASE_URL=postgresql+psycopg://user:pass@localhost/scms_test pytest tests --ignore=tests/e2e   # same suite on PostgreSQL
python -m playwright install chromium && pytest tests/e2e  # browser end-to-end tests
node --test tests/frontend/*.test.mjs                     # front-end validation rules
ruff check backend tests                                   # static analysis
python tests/perf/load_test.py --url http://localhost:8000 --users 50   # load test (server must be running)
```

## Repository Structure

```
backend/app/
  api/v1/          REST endpoints (auth, users, complaints, categories, sla, notifications, reports)
  core/            configuration, security (bcrypt + JWT), constants and the complaint state model
  models/          SQLAlchemy entities
  repositories/    data-access layer
  services/        business rules: auth, complaint/assignment/resolution, SLA & escalation, notifications, reports
  jobs/            background SLA scheduler
  schemas/         Pydantic request/response validation
database/migrations/  Alembic migrations
frontend/          HTML/CSS/JavaScript single-page web client (served by FastAPI)
tests/             unit, api, e2e (Playwright), frontend (node:test), perf
docs/              SRS, plan, architecture, design, test and validation reports
```

## Documentation

- [Software Requirements Specification](docs/SRS/README.md)
- [Project Plan](docs/Project-Plan/README.md)
- [High-Level Architecture](docs/Architecture/README.md)
- [Software Design](docs/Software_Design/README.md)
- [Test Plan and Test Report](docs/Testing/README.md)
- [System Validation Report](docs/Validation/README.md)

## Project Status

- Requirements / SRS — Completed
- Project Planning — Completed
- High-Level Architecture — Completed
- Software Design — Completed
- Implementation — Completed (backend API, web front end, SLA scheduler)
- Testing — Completed ([Test Plan & Report](docs/Testing/README.md))
- System Validation — Completed ([System Validation Report](docs/Validation/README.md))
- Final Report & Demonstration — Upcoming
