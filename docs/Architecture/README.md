# High-Level Architecture

## Smart Complaint Management System

**Document:** [High_Level_Architecture_Smart_Complaint_Management_System.docx](High_Level_Architecture_Smart_Complaint_Management_System.docx)

The architecture document establishes the system context, layered modular architecture, component responsibilities, security boundaries, logical data domains, deployment structure, technology mapping, and requirement traceability.

## Architectural Components

The repository contains these major components:

- Browser frontend (HTML/CSS/JavaScript)
- FastAPI REST API under `/api/v1`
- Authentication and role-based authorization
- Complaint management and state-transition logic
- Repository/data-access layer and PostgreSQL persistence
- Assignment, SLA monitoring, and escalation services
- In-app notification service
- Dashboard and CSV reporting
- Background SLA scheduler
- Alembic database migrations
- Docker Compose development environment

## Key Workflows

**Complaint submission:** User → frontend → FastAPI → complaint service → repository → PostgreSQL.

**Assignment and resolution:** Administrator/staff → frontend → authorized API → complaint/assignment service → PostgreSQL, with status history and notifications recorded.

**SLA monitoring:** Background scheduler → SLA service → PostgreSQL; overdue complaints are escalated and notifications are generated.

**Notifications:** Core workflows generate in-app notifications. An adapter boundary exists for external channels, but real email/SMS/WhatsApp providers are not configured in the current baseline.

## Technology and Deployment Mapping

| Concern | Current repository implementation |
|---|---|
| Frontend | HTML / CSS / JavaScript |
| Backend | Python + FastAPI |
| Database | PostgreSQL |
| Data access and migrations | SQLAlchemy + Alembic |
| Tests | pytest, Playwright, Node.js `node:test` |
| Continuous integration | GitHub Actions (`.github/workflows/ci.yml`) |
| Jenkins | A Jenkins pipeline exists with local-machine path assumptions |
| Containerization | Dockerfile and Docker Compose |
| Static analysis | Ruff in GitHub Actions |

## Status and Relationship to Other Documents

The architecture is a completed structural baseline, not an indication that design or implementation is still the next phase. Implementation and verification are recorded in the repository and in the linked Software Design, Test Plan, and System Validation documents. Implementation refinements found during validation are listed in the [Implementation Design Refinements Addendum](../Software_Design/Implementation_Refinements_Addendum.md).

See the [Final Submission Readiness Checklist](../FINAL_SUBMISSION_READINESS.md) for remaining release and course deliverables.
