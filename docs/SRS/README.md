# Software Requirements Specification

## Smart Complaint Management System

This folder contains the SRS baseline for the Smart Complaint Management System, Project ID 67.

**Document:** [SRS_Smart_Complaint_Management_System.docx](SRS_Smart_Complaint_Management_System.docx)

## Purpose and Scope

The SRS establishes the requirements baseline: functional and non-functional requirements, business rules, data requirements, use cases, external interfaces, constraints, and traceability. It describes a web-based complaint management platform supporting:

- User registration and authentication
- Complaint submission and status tracking
- Categorization and priority assignment
- Assignment to authorized staff
- SLA monitoring and escalation
- In-app notifications
- Administrative dashboards and CSV reporting
- Status history and resolution records

## User Roles

| Role | Main responsibilities |
|---|---|
| User | Register/sign in, submit complaints, and track their own complaints |
| Staff / Resolver | View assigned or permitted unassigned complaints, update status, and record resolution details |
| Administrator | Manage users and categories, assign and escalate complaints, configure SLA rules, and access reports |

## Traceability

The baseline defines FR-01 through FR-24, NFR-01 through NFR-07, and BR-01 through BR-10. The implementation, tests, and validation results are documented in Software Design, Test Plan and Report, and System Validation Report.

The lifecycle relationship is:

`SRS → High-Level Architecture → Software Design → Implementation → Testing → System Validation → Final Report and Demonstration → Maintenance`

## Scope and Version Control Note

The current repository stores the v1.0 SRS baseline. The Test Plan mentions proposed v1.1 additions—feedback/reopen, attachments, departments, and login lockout—as outside the submitted Software Design baseline. No separately versioned, approved SRS v1.1 was located in this repository during the documentation audit. Treat these items as proposed scope changes until the team and evaluator approve and version an updated SRS; do not silently expand the baseline.

## Status

**Baseline status:** Requirements baseline established. The SRS is a requirements document, so its original scope remains a historical baseline rather than a live task-status report.

For implementation and final-submission status, see the [Final Submission Readiness Checklist](../FINAL_SUBMISSION_READINESS.md).
