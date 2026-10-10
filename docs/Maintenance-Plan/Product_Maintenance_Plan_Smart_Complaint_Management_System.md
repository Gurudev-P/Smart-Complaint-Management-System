# Product Maintenance Plan

## Smart Complaint Management System (SCMS)

| Document control | Value |
|---|---|
| Project ID | 67 |
| Team | Gundu Guru |
| Institution / Department | PES University — Computer Science and Engineering (AI&ML) |
| Version | 1.0 |
| Prepared | 10 October 2026 |
| Status | Proposed maintenance baseline for team review |
| Owner | SCMS project team; repository owner coordinates releases |

## Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | 10 October 2026 | Initial maintenance plan based on the repository, project plan, test report, and system validation report. |

## 1. Purpose and scope

This plan defines how the SCMS team should maintain the application after implementation and during final sprint demonstrations. It covers corrective, adaptive, perfective, and preventive maintenance for the FastAPI backend, browser frontend, PostgreSQL database and Alembic migrations, SLA scheduler, Docker Compose environment, automated tests, and repository workflows.

This is a student-project maintenance plan, not a claim that a production support service or managed production environment is currently operating. Procedures marked **recommended** are proposed practices; they are not represented as already automated.

## 2. Maintenance objectives

- Preserve the core complaint lifecycle: authenticate, submit, categorize, assign, update status, resolve, notify, and report.
- Protect complaint, account, and status-history data from unauthorized access or accidental loss.
- Keep changes reproducible through GitHub branches, pull requests, automated checks, and documented releases.
- Detect regressions with tests and targeted smoke checks before a change is merged or demonstrated.
- Keep project documentation consistent with the actual implementation and record deviations from the submitted SRS, Software Design, and Test Plan.

## 3. System baseline and known operating constraints

The current repository describes a layered modular web application: HTML/CSS/JavaScript frontend, Python 3.12 and FastAPI backend, PostgreSQL (PostgreSQL 16 in the recorded test environment), SQLAlchemy/Alembic data layer, and a background SLA scheduler. Docker Compose provides the local application and database environment. GitHub Actions runs Ruff and the Python test suite, including Playwright browser tests, and a separate Node.js frontend test job. Jenkins is also present in the repository.

The System Validation Report records a baseline of 41/41 requirements validated, 207 automated tests passed, 94.6% backend statement coverage, and a load test with 50 concurrent users / 2,050 requests with zero errors and p95 latency of 829 ms. These are results recorded by that report, not a guarantee of current production performance or an ongoing service-level objective. Re-run the relevant checks before final freeze and after material changes.

Known constraints to respect:

- The repository's Docker Compose setup includes development fallback values and demo credentials. Do not expose a shared or production deployment using those defaults; set unique secrets and administrator credentials outside source control.
- A PostgreSQL Docker named volume (pgdata) provides persistence, but it is not a backup. No automated database backup job or dedicated monitoring/alerting service was verified in the repository when this plan was prepared.
- The test report says real email/SMS/WhatsApp delivery is not configured; the external-channel adapter boundary is exercised with a stub. Do not describe external message delivery as operational until a provider is configured and verified.
- The test report identifies one accepted issue involving login-burst latency, and notes that formal penetration testing, a formal accessibility audit, and browsers other than Chromium are outside the current verification scope.
- The Jenkinsfile contains machine-specific local paths. If Jenkins is moved to another machine or a hosted runner, update and verify that configuration before relying on it.

## 4. Maintenance responsibilities

| Role / member | Maintenance responsibility |
|---|---|
| Purum Gurudev — repository owner | Coordinate triage and releases; maintain authentication/account controls and CI configuration; verify PR checks, backups, and final release tag. |
| Prashyanth V | Maintain complaint submission, categorization, tracking, and CSV/report filtering; validate data and workflow changes with regression tests. |
| Aditya Pradeep | Maintain assignment, status workflow, SLA monitoring/escalation, and administration-related behavior; review scheduler and deadline handling. |
| Nihar S Jain | Maintain notification behavior and event filtering, dashboard/reporting behavior, and related regressions. |
| All members | Report defects with reproduction steps; review relevant changes; protect secrets and data; update documentation and test evidence for work they change. |

Ownership identifies the first point of contact; it does not remove the responsibility of the whole team to review, test, and understand the integrated product.

## 5. Types of maintenance

| Type | Trigger | Required action |
|---|---|---|
| Corrective | A defect, failed test, incorrect result, or security issue is reported. | Open/update a GitHub issue, reproduce the problem, fix it on a branch, add a regression test, pass CI, obtain review, and document the result. |
| Adaptive | Python/library/browser/OS/database/Docker change or an environment change. | Check compatibility, update dependencies/configuration deliberately, run unit/API/E2E/frontend tests, validate migrations, and test a fresh Docker Compose start. |
| Perfective | Usability, reporting, or performance improvement. | Create a scoped issue with acceptance criteria; estimate and prioritize it; compare behavior and performance before/after; update user-facing documentation. |
| Preventive | Dependency warnings, outdated secrets, growing logs/data, fragile scripts, or recurring defects. | Review security advisories, rotate compromised credentials, test database restore, improve brittle configuration, and add monitoring/tests where needed. |

## 6. Routine maintenance schedule

| Frequency / trigger | Check or action | Evidence to retain |
|---|---|---|
| Every pull request | Review scope and tests; require successful GitHub Actions checks; inspect security-sensitive changes; merge only after review. | PR review, CI results, linked issue. |
| After each merge to main | Verify CI completed; perform a local Docker Compose smoke test for material changes; confirm health endpoint and core complaint path. | Actions run, smoke-test note, defect issue if needed. |
| Weekly or during each sprint | Review open/accepted defects, failed workflows, dependency warnings, and changes to requirements; confirm assigned work and docs are current. | Issue/project updates, sprint notes. |
| Before a release, migration, or recorded demonstration | Take a database backup; check environment variables and demo accounts; run tests and migrations; verify login, submission, assignment/status, notification, and CSV export. | Backup stored outside Git, CI run, checklist/results. |
| Monthly (recommended) | Review dependency/security advisories, repository collaborators/permissions, logs and Docker disk usage; check backup retention. | Maintenance log and follow-up issues. |
| Monthly (recommended) and before risky migrations | Perform a restore drill using a non-production database/isolated environment; verify application and sample records after restore. | Restore date, backup identifier, test result, issues found. |
| Immediately after suspected compromise or data loss | Restrict access, preserve relevant logs, rotate affected secrets, preserve a backup of current state if safe, recover only through a reviewed procedure. | Incident record, action timeline, root cause and recovery result. |

## 7. Change, testing, and release procedure

1. **Report and triage.** Open a GitHub issue with a clear summary, impact, reproducible steps, expected/actual behavior, environment, and sanitized evidence. Never include passwords, tokens, real personal data, or raw production records.
2. **Prioritize and assign.** Classify the issue as urgent, high, normal, or low based on data/security impact and effect on core complaint workflows. Assign an owner and acceptance criteria.
3. **Branch and implement.** Work on a descriptive branch; keep the change focused. Include or update unit/API/frontend/E2E tests where applicable and update documentation for changed behavior.
4. **Run checks.** Run the following as applicable: python -m ruff check backend tests, python -m pytest -q, and node --test tests/frontend/*.test.mjs. GitHub Actions runs the configured lint and test jobs on pull requests. For database/deployment-related changes, also validate Alembic migrations and a Docker Compose build/start.
5. **Review and merge.** The assigned contributor opens the PR; a repository owner/team member reviews the diff, acceptance criteria, test evidence, and security implications. Do not merge while required checks fail or a critical issue remains unresolved.
6. **Post-merge smoke test.** Confirm /api/v1/health responds, users can authenticate with the intended environment configuration, and the changed workflow works end to end. Verify scheduler behavior if SLA logic changed.
7. **Record and release.** Update the relevant document and maintenance log. After final tests and the required demo evidence are complete, the repository owner may create a final version tag and freeze feature development. Subsequent changes should be limited to approved fixes and documented.

## 8. Database backup and recovery

### 8.1 Current status and policy

The local Docker Compose database uses a named volume. This protects data across container recreation but does not protect against deletion of the volume, disk failure, accidental destructive migrations, or host loss. The repository did not show an automated backup schedule when this plan was prepared, so the commands below are **manual operating procedures**, not evidence of configured automated backups.

For the student/demo environment, take a backup before every schema migration or release and before each sprint demo that depends on persistent records. Keep backups in a private directory outside the Git repository, restrict access, and never commit database dumps to Git. If SCMS is later used for real users, a responsible operator should define backup frequency and retention formally; a reasonable starting recommendation is nightly backups, short-term daily retention, periodic weekly/monthly copies, encryption, and regular restore drills.

### 8.2 Create a backup (local Docker Compose environment)

Run from the repository root where docker-compose.yml is located:

    mkdir -p "$HOME/scms-backups"
    chmod 700 "$HOME/scms-backups"
    docker compose exec -T db pg_dump -U scms -d scms -Fc \
      > "$HOME/scms-backups/scms-$(date +%Y%m%d-%H%M%S).dump"
    ls -lh "$HOME/scms-backups"

Confirm that the output file is non-empty and keep a note of the date, repository revision, and reason for the backup. Store a copy on an appropriately protected location if the host itself is at risk. Never upload the dump to a public repository.

### 8.3 Restore a backup (destructive; local/demo environment only)

Restore can replace the current database. Confirm the backup path first and create a separate backup of the current database if it is still readable. Stop the application to avoid active connections, then run the commands below with the actual backup filename substituted. These commands assume the repository's current Compose database name/user (scms) and service name (db); adapt and test them before use in any other environment.

    export BACKUP_FILE="$HOME/scms-backups/scms-YYYYMMDD-HHMMSS.dump"
    test -s "$BACKUP_FILE" || { echo "Backup file missing or empty"; exit 1; }
    docker compose stop app
    docker compose exec -T db psql -U scms -d postgres \
      -c "DROP DATABASE IF EXISTS scms WITH (FORCE);"
    docker compose exec -T db psql -U scms -d postgres \
      -c "CREATE DATABASE scms OWNER scms;"
    docker compose exec -T db pg_restore -U scms -d scms \
      --no-owner --no-privileges < "$BACKUP_FILE"
    docker compose up -d app
    docker compose ps

After recovery, check http://localhost:8000/api/v1/health, run alembic current using the configured application environment, sign in with a known demo account, and verify representative complaints, history, notifications, and reports. If any check fails, keep the system out of use, preserve logs, and troubleshoot before accepting new writes. Do not run the destructive restore commands on a production database without a reviewed, environment-specific recovery procedure.

### 8.4 Migration policy

- Back up before every migration and test it against a disposable/restored copy first.
- Run alembic upgrade head using the intended database configuration and verify the reported current revision.
- Prefer forward-fix migrations when data may be lost; do not assume a downgrade can safely reverse a data-changing migration.
- After migration, run tests and smoke checks before reopening the application to users.

## 9. Monitoring and troubleshooting

The current setup can be inspected with Docker Compose and the application health endpoint. A dedicated production monitoring or alerting system is not confirmed in the repository.

Useful local commands:

    docker compose ps
    docker compose logs --since=1h app db
    curl -f http://localhost:8000/api/v1/health
    docker stats

During maintenance, review application exceptions, sustained 5xx responses, database connection errors, failed logins or authorization denials, scheduler/SLA processing errors, container restarts, disk usage, and response-time changes. Do not log passwords, access tokens, or unnecessary personal/complaint details. For a shared or production deployment, configure suitable log retention, access controls, uptime/error alerts, database capacity monitoring, and secure secret management before relying on the service operationally.

Use the existing validation result (p95 829 ms under its recorded 50-user / 2,050-request test) as a comparison point only. Investigate repeatable regressions under comparable conditions; do not treat that one test as a production performance guarantee.

## 10. Security and privacy maintenance

- Keep .env, tokens, passwords, signing keys, database dumps, and user data out of Git. Use .env.example only for non-secret placeholders.
- Change the documented demo credentials before sharing a non-local deployment. Never expose the Docker Compose fallback secret or default administrator password to an untrusted network.
- Restrict repository/project permissions to required collaborators and review them during maintenance.
- Apply dependency and base-image updates deliberately; review release notes and advisories, run CI, and smoke-test before release.
- On suspected credential compromise, restrict access, rotate the affected secret, invalidate/replace sessions as appropriate, inspect logs, and document the incident.
- Use synthetic or sanitized examples in issues, screenshots, and videos. Decide formal record-retention and deletion rules with the system owner before any real-user data is stored.
- Treat external email/SMS/WhatsApp integrations as disabled until credentials, consent/recipient handling, delivery failure behavior, and end-to-end tests are configured and verified.

## 11. Incident and defect handling

| Severity | Example | Response |
|---|---|---|
| Critical | Suspected data exposure, data corruption/loss, authentication/authorization bypass, or application unavailable. | Notify the repository owner/team immediately; restrict access or writes if needed; preserve logs; protect a copy of the current state; rotate compromised secrets; restore only from a verified backup; document and test the fix before reopening. |
| High | Core login, complaint submission, assignment, resolution, or SLA processing fails for intended users. | Create a high-priority issue, reproduce and assign an owner, provide a workaround if safe, add a regression test, and prioritize a reviewed fix. |
| Normal | A non-critical notification, dashboard, export, or administrative path is impaired. | Record the impact and reproduction steps; schedule a fix; verify with the relevant tests. |
| Low | Cosmetic issue, minor usability improvement, or non-blocking documentation defect. | Add to backlog and address by priority and available time. |

Every incident or accepted defect should record the affected version/commit, impact, trigger, workaround, root cause when known, fix/PR, test evidence, and any remaining risk. Do not mark an unresolved issue as fixed solely because the code changed; verify the behavior.

## 12. Recovery goals and data lifecycle

For the current educational environment, the immediate recovery objective is to restore the latest verified backup and demonstrate that core workflows work. Actual recovery point and recovery time depend on when the last backup was taken and the time needed to restore and verify it; this project has no formally approved RPO/RTO guarantee. If the system is used beyond demonstrations, the owner must set those targets and retention rules explicitly.

Test and demo data may be reset only when the team agrees it is safe. Keep database exports, logs, and screenshots private if they contain identifiers or complaint details. Remove temporary exports and old backups according to the retention policy adopted by the system owner.

## 13. Maintenance record template

| Field | Record |
|---|---|
| Date / maintainer | |
| Issue(s) and affected version/commit | |
| Reason / severity | |
| Backup identifier (if applicable) | |
| Dependencies, migrations, or configuration changed | |
| Tests and CI run links | |
| Smoke-test / restore outcome | |
| Rollback or recovery performed | |
| Remaining risks / follow-up issue | |

## 14. References

- README.md — installation, environment variables, commands, test suites, repository structure.
- docs/Project-Plan/Project_Plan_Smart_Complaint_Management_System.docx — roles, lifecycle, schedule, risk management, and definition of done.
- docs/Architecture/High_Level_Architecture_Smart_Complaint_Management_System.docx — system components, data and deployment architecture.
- docs/Software_Design/Software_Design_Smart_Complaint_Management_System.docx — detailed API, data, workflow, validation, and security design.
- docs/Testing/Test_Plan_and_Report_Smart_Complaint_Management_System.docx — test strategy, automated results, coverage, performance, known defects, and test limitations.
- docs/Validation/System_Validation_Report_Smart_Complaint_Management_System.docx — requirement validation, baseline metrics, walkthrough evidence, limitations, and sign-off.
- .github/workflows/ci.yml and Jenkinsfile — automated quality/test workflows and their environment assumptions.

## 15. Review and approval

This version is a proposed maintenance baseline for the student team. The repository owner should review it against the final system configuration before the development freeze and update it if the deployment environment, backup process, notification integrations, or support responsibilities change.

| Review role | Name | Date / approval |
|---|---|---|
| Repository owner | Purum Gurudev | |
| Team review | Gundu Guru | |
| Faculty evaluator (if required) | | |
