# Software Design

## Smart Complaint Management System

**Baseline document:** [Software_Design_Smart_Complaint_Management_System.docx](Software_Design_Smart_Complaint_Management_System.docx) — Version 1.0.

The Software Design Document defines detailed module boundaries, UML models, complaint state transitions, database structure, API contracts, validation, error handling, security, non-functional considerations, and requirement-to-design traceability.

## Implemented Design Areas

The repository contains corresponding code for authentication and authorization, complaint creation/tracking, categorization, assignment and resolution, SLA rules and escalation, in-app notifications, reporting/CSV export, PostgreSQL models, Alembic migrations, and unit/API/browser/frontend tests.

## Implementation Refinements

Validation identified refinements made during implementation that were not fully incorporated in the original Version 1.0 design baseline. These are listed in the companion [Implementation Design Refinements Addendum](Implementation_Refinements_Addendum.md). It covers the additional `sla_rules` table, escalation transitions, the internal System account, additional endpoints, expected-status concurrency checks, and uppercase role values.

## Status

**Status:** Design baseline completed and used by the implementation. The old “Next SDLC Phase: Implementation” label in the original index is retired because implementation and validation artifacts now exist.

The addendum is a companion change record; it does not silently replace the original Version 1.0 document. If a single consolidated Software Design Document is required for submission, incorporate the addendum and issue a controlled Version 1.1.

See the [Final Submission Readiness Checklist](../FINAL_SUBMISSION_READINESS.md) for remaining release tasks.
