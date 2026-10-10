# Project Plan

## Smart Complaint Management System

**Document:** [Project_Plan_Smart_Complaint_Management_System.docx](Project_Plan_Smart_Complaint_Management_System.docx)

The Project Plan defines the Agile execution framework, tools, primary functional ownership, work breakdown structure, effort estimate, schedule, sprint planning, risks, definition of done, and progress-tracking approach.

## Development and Collaboration Tools

| Area | Repository status |
|---|---|
| Git / GitHub | Source control and pull requests are in use |
| GitHub Issues | Feature and deliverable issues exist; Project board fields and sprint setup need a final check |
| Backend / API | Python + FastAPI |
| Frontend | HTML, CSS, and JavaScript |
| Database | PostgreSQL with SQLAlchemy and Alembic migrations |
| Testing | pytest, Playwright, and Node.js `node:test` |
| CI | GitHub Actions is configured in `.github/workflows/ci.yml` |
| Jenkins | `Jenkinsfile` exists; it includes developer-machine-specific paths and needs review before running on another host |
| Containerization | Dockerfile and Docker Compose are present |
| Static analysis | Ruff is configured in CI. SonarQube itself is not configured in the repository |

## Functional Ownership

| Team member | Primary functionality |
|---|---|
| Purum Gurudev | Authentication and account management |
| Prashyanth V | Complaint submission, categorization, and tracking |
| Aditya Pradeep | Assignment, SLA monitoring, and escalation |
| Nihar S Jain | Notifications, dashboard, and reporting |

All team members remain responsible for integration, testing, review, documentation, and final demonstration evidence.

## Current Execution State

The Project Plan remains the planning baseline; completed implementation work and outstanding coursework evidence are tracked separately. Part-2 requires a GitHub backlog with story points, assignees and two sprint plans, a one-minute Sprint 1 video (19–23 October 2026), a two-minute Sprint 2 video (26–30 October 2026), completed documentation, and a development freeze. Confirm the board itself—not just issue descriptions—contains the required values.

Use the [Final Submission Readiness Checklist](../FINAL_SUBMISSION_READINESS.md) for current action items and unresolved documentation checks.
