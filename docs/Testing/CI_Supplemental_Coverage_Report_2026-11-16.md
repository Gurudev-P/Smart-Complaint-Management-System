# CI Supplemental Test and Coverage Report

**Project:** Smart Complaint Management System (SCMS)  
**Project ID:** 67  
**Repository:** https://github.com/Gurudev-P/Smart-Complaint-Management-System  
**Evidence date:** 16 November 2026  
**Branch:** `submission/branch-coverage-evidence`  
**Commit:** `497879cbc55f61f3cc53f5753f7e26c2ed2f469a`

## 1. Purpose

This supplemental report records a successful GitHub Actions run with branch coverage measurement enabled. It supplements (and does not overwrite) the October 2026 Test Plan and System Validation Report.

## 2. CI execution

- Workflow: **SCMS Continuous Integration**
- Run: [GitHub Actions run #11](https://github.com/Gurudev-P/Smart-Complaint-Management-System/actions/runs/43919369419)
- Result: **Success**
- Python job: **Success**
- Frontend JavaScript job: **Success**
- Ruff lint: **Success**
- Chromium installation for Playwright E2E: **Success**
- Python test suite: **215 passed, 0 failed, 1 warning** (24.15 seconds)
- Evidence artifact: [scms-test-and-coverage-evidence](https://github.com/Gurudev-P/Smart-Complaint-Management-System/actions/runs/43919369419/artifacts/14253905788)

## 3. Coverage results

Coverage was collected for `backend/app` with `pytest-cov --cov-branch`.

| Measure | Covered | Valid | Result |
|---|---:|---:|---:|
| Statements / lines | 1,351 | 1,424 | **94.87%** |
| Branches | 232 | 288 | **80.56%** |

The values above are read from the uploaded `coverage.xml` artifact (`line-rate=0.9487`; `branch-rate=0.8056`). They are not estimated from the older October report.

## 4. Evidence files

The workflow artifact contains:
- `coverage.xml` - machine-readable line and branch coverage totals
- `htmlcov/` - module-level HTML coverage report
- `junit.xml` - JUnit test execution report

The artifact was uploaded successfully on 16 November 2026. GitHub lists its retention expiry as 16 December 2026; download and archive it with the final project records before expiry.

## 5. Relationship to earlier test report

The October 2026 Test Plan and System Validation Report record 207 automated tests and 94.6% backend statement coverage. The CI execution documented here is a later run: 215 Python tests passed and branch coverage is now measured. Preserve both records with their dates rather than silently replacing historical results.

## 6. Limitations

- The CI result is evidence for the cited commit and workflow run, not a guarantee that future commits pass.
- One pytest warning was reported; it did not fail the run.
- The frontend job passed, but its test count is not included in the Python JUnit total.
- The uploaded artifact has a 30-day retention period; archive it for long-term submission evidence.
