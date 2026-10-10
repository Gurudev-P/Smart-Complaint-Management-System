# Final Submission Readiness Checklist

## Smart Complaint Management System (Project ID 67)

**Review date:** 10 October 2026  
**Repository baseline reviewed:** `main` at `79bb3eb` (`docs: add product maintenance plan`)  
**Purpose:** Track the gap between a substantially implemented system and a complete, evidence-backed Software Engineering mini-project submission.

> The accessible course handout in the project files is **Mini-Project Deliverables Part-2**. A separate instructor-issued Part-3 handout was not found in the accessible repository/library during this audit. The supplementary finalization items below are team tracking work, not a claim about an unlocated official document.

## 1. Confirmed Repository Deliverables

| Item | Current evidence | Status |
|---|---|---|
| SRS | `docs/SRS/SRS_Smart_Complaint_Management_System.docx` | Present |
| Project Plan | `docs/Project-Plan/Project_Plan_Smart_Complaint_Management_System.docx` | Present |
| High-Level Architecture | `docs/Architecture/High_Level_Architecture_Smart_Complaint_Management_System.docx` | Present |
| Software Design baseline | `docs/Software_Design/Software_Design_Smart_Complaint_Management_System.docx` | Present; implementation refinements are tracked in a companion addendum |
| Test Plan and Report | `docs/Testing/Test_Plan_and_Report_Smart_Complaint_Management_System.docx` | Present |
| System Validation Report | `docs/Validation/System_Validation_Report_Smart_Complaint_Management_System.docx` | Present, updated report Version 1.1 |
| Consolidated report | `docs/Final-Report/Final_Project_Report_Smart_Complaint_Management_System.docx` | Present as a Sections 1–6 working baseline; final review/export still required |
| Product Maintenance Plan | Markdown and Word copies in `docs/Maintenance-Plan/` | Present; formats need reconciliation before final formal submission |
| GitHub Actions CI | `.github/workflows/ci.yml` | Configured; latest known run on reviewed main commit passed |
| Validation screenshots | `docs/Validation/screenshots/` | Present (12 images) |

The validation report records 41/41 requirements validated, 207 passing automated tests, 94.6% backend statement coverage, and a 50-user load test with zero errors and p95 latency of 829 ms. These figures belong to the report's recorded run. Re-run workflow checks after audit changes and before final freeze.

## 2. Official Part-2 Deliverables

The Part-2 handout specifies a GitHub backlog, story points, assignees, two sprints, GitHub Actions, a one-minute Sprint 1 working-product video, a two-minute Sprint 2 working-product video, documentation of deviations, and a development freeze.

### Backlog and GitHub Project

- [ ] Confirm a GitHub Project is created and linked to this repository.
- [ ] Confirm each backlog story is derived from SRS functional/non-functional requirements.
- [ ] Confirm story points, assignees, sprint assignment, and status are set in the **Project board fields**, not only written in issue descriptions.
- [ ] Review issues #6–16: several are Sprint verification/demo items while implementation is already present. Do not mark them done based only on code presence; satisfy acceptance criteria and retain test/demo evidence.
- [ ] Reconcile overlapping CI tracking: issue #17 and PR #17 implemented GitHub Actions and are closed/merged, while issue #15 remains open with similar acceptance criteria. Close or retarget #15 only after confirming all its acceptance criteria and the Project board records.
- [ ] Review the open/accepted issue list as a team before final freeze.

### Sprint 1 — 19–23 October 2026

- [ ] Complete Sprint 1 items assigned on the Project board.
- [ ] Record a **one-minute** video showing real, working SCMS behavior.
- [ ] Upload the video to the repository and link it from project documentation/issue.
- [ ] Verify relevant pull requests and visible CI checks.

### Sprint 2 — 26–30 October 2026

- [ ] Complete Sprint 2 items assigned on the Project board.
- [ ] Record a **two-minute** video showing the integrated working product.
- [ ] Upload the video to the repository and link it from project documentation/issue.
- [ ] Finish documentation, record accepted deviations/limitations, and freeze development after final verification.

## 3. Supplementary Team Finalization Work

- [x] Add the Product Maintenance Plan in Word and retain a Markdown maintenance reference.
- [x] Configure GitHub Actions for pushes to `main`, pull requests targeting `main`, and manual runs.
- [x] Add a companion Software Design implementation-refinements addendum so validation findings are traceable.
- [x] Add regression validation for whitespace-only category/user names and pass complaint-list search/overdue filters to CSV export (GitHub Actions passed on PR #19).
- [ ] Compare the Markdown and Word maintenance plan before final submission so future edits do not cause drift. Both current Version 1.0 files include a review/approval section and are dated 10 October 2026; re-synchronize the Word copy whenever the Markdown reference receives a material change.
- [ ] Align document-index lifecycle labels with actual implementation stage (changes are on the audit branch).
- [ ] Check the consolidated Word report for stale working-draft labels, consistency with final code, revision history, TOC/page numbering, and required signatures.
- [ ] Export the final report to PDF if required; inspect the entire PDF before submission.
- [ ] Confirm demo accounts are seeded and a fresh Docker Compose setup starts. Change fallback credentials before any shared deployment.
- [ ] Run current CI and a final live walkthrough: login as each role, submit a complaint, assign it, change status, resolve it, verify history/notifications, review SLA behavior, and export filtered CSV.
- [ ] Record known deviations/limitations: external email/SMS/WhatsApp delivery is not configured, login spikes were slow in the recorded load test, only Chromium was covered in the report, formal penetration/accessibility audits were out of scope, and the Jenkinsfile assumes developer-machine paths.
- [ ] After videos, documentation review, tests, and team sign-off, create the agreed final version/tag and freeze feature development.

## 4. Requirements Baseline and Scope Control

The repository contains one SRS document as the v1.0 baseline. The Test Plan refers to proposed v1.1 items (feedback/reopen, attachments, departments, login lockout) as outside that design baseline. Do not claim these items are implemented. If the team/evaluator adopts them, issue an approved, versioned SRS change and assess design, code, and tests before extending scope.

## 5. Release Exit Criteria

The project is ready for final submission only when all of the following are true:

- [ ] Current GitHub Actions checks are green on the reviewed final commit.
- [ ] The GitHub Project backlog, estimates, assignments, sprints, and issue statuses are accurate.
- [ ] Both sprint videos are present in the repository.
- [ ] SRS, plan, architecture, design/addendum, testing, validation, maintenance, and final report are mutually consistent.
- [ ] Accepted limitations and deviations are disclosed and explainable by all team members.
- [ ] Final report format matches submission requirements.
- [ ] Team review and development freeze are recorded.

Update this checklist only when supporting evidence exists; do not check off a deliverable solely because a document or source file exists.
