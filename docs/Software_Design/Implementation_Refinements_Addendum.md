# Implementation Design Refinements Addendum

## Smart Complaint Management System (SCMS)

| Control | Value |
|---|---|
| Project ID | 67 |
| Companion document | Software Design Document, Version 1.0 |
| Addendum version | 1.1 |
| Prepared | 10 October 2026 |
| Status | Implementation-alignment addendum; team review required |

## Purpose

The System Validation Report records design refinements made during implementation and asks that they be folded into a later Software Design revision. This addendum documents those changes against the repository so that implementers, testers, and reviewers can trace behavior without silently rewriting the original Version 1.0 baseline.

This addendum supplements the submitted Software Design Document. If a single consolidated document is required, incorporate these changes, update the revision history and table of contents, and issue a controlled Version 1.1.

## Confirmed Implementation Refinements

| ID | Refinement | Current implementation reference | Reason / verification focus |
|---|---|---|---|
| DR-01 | Add persistent `sla_rules` records keyed by priority with target minutes and due-soon percentage; migration `c3a1f0d2e7b4` adds the table. | [Migration](../../database/migrations/versions/c3a1f0d2e7b4_add_sla_rules.py), [SLA rule model](../../backend/app/models/sla_rule.py), [SLA service](../../backend/app/services/sla_service.py) | Keeps SLA targets configurable rather than hard-coded. Verify seeding and administration of rule values. |
| DR-02 | Permit escalation from open complaints including `SUBMITTED` and `ASSIGNED` before work has started. | [State transitions](../../backend/app/core/constants.py), [SLA service](../../backend/app/services/sla_service.py) | Complaints can breach SLA before assignment or work begins. Verify history and notifications. |
| DR-03 | Allow reassignment from `ESCALATED` to `ASSIGNED`; resuming work requires an active assignee. | [Complaint service](../../backend/app/services/complaint_service.py), [state transitions](../../backend/app/core/constants.py) | An escalated, unassigned complaint must receive an owner before work resumes. |
| DR-04 | Create an internal non-login `System` account for scheduler-generated history records. | [Authentication service](../../backend/app/services/auth_service.py), [SLA service](../../backend/app/services/sla_service.py) | `status_history.changed_by` is required even when a background task causes a change. The account must remain excluded from normal login and user administration. |
| DR-05 | Provide additional implementation endpoints: `/api/v1/users`, `/api/v1/sla/check`, `/api/v1/notifications/read-all`, and `/api/v1/reports/complaints.csv`. | [API router](../../backend/app/api/v1/__init__.py), [user routes](../../backend/app/api/v1/users.py), [administration/report routes](../../backend/app/api/v1/admin.py) | Supports user management, on-demand SLA checks, notification clearing, and CSV reporting. |
| DR-06 | Include optional `expected_status` on status updates and return a conflict when the persisted state no longer matches. | [Status schema](../../backend/app/schemas/complaint.py), [complaint service](../../backend/app/services/complaint_service.py) | Protects against stale concurrent updates. Verify HTTP 409 on mismatch without overwriting the newer state. |
| DR-07 | Use controlled role values `USER`, `STAFF`, and `ADMIN`. | [Role constants](../../backend/app/core/constants.py), [user model](../../backend/app/models/user.py), [authorization dependencies](../../backend/app/api/deps.py) | A shared vocabulary keeps authorization and role-specific UI behavior consistent. |

## Verification Evidence

Relevant tests are available in the repository:

- `tests/api/test_sla.py` and `tests/api/test_scheduler_and_adapters.py` — SLA rules and scheduler behavior.
- `tests/api/test_workflow.py` — status transitions, assignment, resolution, and history.
- `tests/api/test_admin.py` — user/category administration.
- `tests/api/test_auth.py` and `tests/api/test_rbac_matrix.py` — authentication and role restrictions.

The validation report's recorded baseline is 207 passing tests and 94.6% backend statement coverage. These are historical results; run the current CI workflow after changes and use its latest result for the current commit.

## Known Boundaries

- External email, SMS, and WhatsApp providers are not configured; in-app notifications are the active baseline.
- The recorded system/browser test environment uses Chromium.
- The accepted login-burst latency issue and declared test exclusions remain documented in the [System Validation Report](../Validation/System_Validation_Report_Smart_Complaint_Management_System.docx).

## Review Action

Before final sign-off, compare this addendum with the submitted Software Design Document and either incorporate all seven refinements into a controlled Version 1.1 or obtain team/evaluator acceptance of the addendum as a companion record.
