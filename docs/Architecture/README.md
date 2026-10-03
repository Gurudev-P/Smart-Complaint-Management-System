# High-Level Architecture

## Smart Complaint Management System

This folder contains the High-Level Architecture documentation for the Smart Complaint Management System, Project ID 67.

The architecture document translates the approved requirements into major system components, responsibilities, communication paths, security boundaries, data architecture, and deployment structure.

## Document

**File:** `High_Level_Architecture_Smart_Complaint_Management_System.docx`

## Purpose

The High-Level Architecture establishes the structural blueprint of the system before detailed software design and implementation.

It defines:

- System context
- Architectural style
- Major components
- Component responsibilities
- Component interactions
- Security architecture
- High-level data architecture
- Deployment architecture
- Technology mapping
- Team ownership boundaries
- Architecture-to-requirement mapping

## Architectural Style

The system uses a **Layered Modular Web Architecture**.

The major layers and components include:

- Web Frontend
- Backend REST API
- Authentication Service
- Complaint Service
- Assignment / SLA / Escalation Service
- Notification Service
- Dashboard and Reporting
- Data Access / Repository Layer
- Background Scheduler
- PostgreSQL Database

## Major Workflows

The architecture defines the main system flows for:

### Complaint Submission

`User → Web Frontend → Backend REST API → Complaint Service → Data Access → PostgreSQL`

### Assignment and Resolution

`Administrator/Staff → Web Frontend → Backend REST API → Assignment / Complaint Service → Database`

### SLA and Escalation

`Background Scheduler → SLA / Escalation Service → Data Access → Database`

### Notifications

`Application Event → Notification Service → In-App Store / Configured External Providers`

## Security Architecture

The architecture defines high-level security controls including:

- Authentication before protected operations
- Role-based authorization
- Secure password hashing
- API and service-layer input validation
- Restricted administrative operations
- Secure configuration of external notification credentials

## Data Architecture

The architecture identifies the primary logical data groups:

- User / Role
- Complaint
- Category / Priority
- Assignment
- Status History
- SLA
- Notification
- Resolution

Detailed database tables, keys, relationships, indexes, and normalization are deferred to the Software Design phase.

## Deployment Architecture

The planned deployment separates:

- Client browser
- Frontend / web layer
- Application server
- PostgreSQL database
- Notification integrations

Docker is planned for environment consistency, while Jenkins is planned for CI/CD automation.

## Technology Mapping

The architecture maps the major system concerns to the planned technologies:

| Concern          | Planned Technology                    |
|------------------|---------------------------------------|
| Frontend         | HTML / CSS / JavaScript or equivalent |
| Backend          | Python + FastAPI                      |
| Database         | PostgreSQL                            |
| Testing          | Pytest and API/client testing tools   |
| CI/CD            | Jenkins                               |
| Containerization | Docker                                |
| Source Control   | Git + GitHub                          |
| Agile Tracking   | GitHub Issues / Projects              |
| Static Analysis  | SonarQube or equivalent               |

## Requirement Traceability

The architecture maps functional and non-functional requirement groups to the components responsible for implementing them.

This provides a link between the SRS and the detailed software design.

## Design Boundary

The architecture intentionally does not define:

- Detailed class structures
- Exact database schema
- Detailed API request/response contracts
- Implementation-level code structure

These are specified in the Software Design phase.

## Relationship With Other Documents

The architecture is derived from the approved SRS and acts as the structural foundation for the Software Design Document.

The relationship is:

`SRS → High-Level Architecture → Software Design → Implementation`

## Status

**Status:** Architecture Baseline

**Next Related Phase:** Software Design
