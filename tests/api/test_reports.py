"""Dashboard and reporting (FR-22–FR-24)."""
from datetime import timedelta

import pytest

from backend.app.core.timeutil import utcnow

API = "/api/v1/complaints"


def lifecycle(client, admin, staff, cid, resolve=True):
    client.post(f"{API}/{cid}/assign", json={"staff_id": staff.id}, headers=admin.headers)
    client.patch(f"{API}/{cid}/status", json={"new_status": "IN_PROGRESS"}, headers=staff.headers)
    if resolve:
        client.post(f"{API}/{cid}/resolve", json={"resolution_details": "Fixed it properly."}, headers=staff.headers)


@pytest.mark.req("FR-22", "FR-24")
def test_summary_counts_and_metrics(client, admin, user, staff, submit):
    ids = [submit(user, priority=p)["complaint_id"] for p in ("LOW", "HIGH", "HIGH", "CRITICAL")]
    lifecycle(client, admin, staff, ids[0])
    lifecycle(client, admin, staff, ids[1], resolve=False)

    s = client.get("/api/v1/reports/summary", headers=admin.headers).json()
    assert s["total"] == 4
    assert s["open"] == 3
    assert s["by_status"] == {"SUBMITTED": 2, "ASSIGNED": 0, "IN_PROGRESS": 1, "ESCALATED": 0, "RESOLVED": 1, "CLOSED": 0}
    assert s["by_priority"] == {"LOW": 1, "MEDIUM": 0, "HIGH": 2, "CRITICAL": 1}
    assert s["by_category"] == {"IT & Network": 4}
    assert s["resolved"] == 1
    assert s["sla_compliance_percent"] == 100.0
    assert s["avg_resolution_hours"] is not None
    assert len(s["trend"]) == 14 and s["trend"][-1]["count"] == 4


@pytest.mark.req("FR-23")
def test_summary_filters(client, admin, user, submit):
    submit(user, priority="LOW")
    submit(user, priority="HIGH")
    h = admin.headers
    assert client.get("/api/v1/reports/summary", params={"priority": "HIGH"}, headers=h).json()["total"] == 1
    future = (utcnow() + timedelta(days=1)).isoformat()
    assert client.get("/api/v1/reports/summary", params={"from": future}, headers=h).json()["total"] == 0
    past = (utcnow() - timedelta(days=1)).isoformat()
    assert client.get("/api/v1/reports/summary", params={"from": past}, headers=h).json()["total"] == 2
    assert client.get("/api/v1/reports/summary", params={"from": future, "to": past}, headers=h).status_code == 400


@pytest.mark.req("FR-22", "BR-08")
def test_staff_summary_limited_to_assigned(client, admin, user, staff, submit):
    a = submit(user)["complaint_id"]
    submit(user)
    lifecycle(client, admin, staff, a, resolve=False)
    s = client.get("/api/v1/reports/summary", headers=staff.headers).json()
    assert s["scope"] == "assigned" and s["total"] == 1


@pytest.mark.req("BR-09")
def test_reports_forbidden_for_users(client, user):
    assert client.get("/api/v1/reports/summary", headers=user.headers).status_code == 403
    assert client.get("/api/v1/reports/complaints", headers=user.headers).status_code == 403


@pytest.mark.req("FR-23", "FR-24")
def test_complaint_report_and_csv_export(client, admin, user, submit):
    submit(user, priority="HIGH", description='Comma, "quotes" and a newline\nin text')
    submit(user, priority="LOW")
    report = client.get("/api/v1/reports/complaints", params={"priority": "HIGH"}, headers=admin.headers).json()
    assert report["total"] == 1
    res = client.get("/api/v1/reports/complaints.csv", headers=admin.headers)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    lines = res.text.strip().splitlines()
    assert lines[0].startswith("Reference,Created (UTC),Category")
    assert len(lines) == 3
