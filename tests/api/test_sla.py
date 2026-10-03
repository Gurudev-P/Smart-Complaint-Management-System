"""SLA monitoring and escalation (FR-16–FR-19, BR-06, BR-07)."""
from datetime import timedelta

import pytest

from backend.app.core.timeutil import as_utc
from backend.app.models import SLA, Complaint
from backend.app.services.auth_service import AuthService
from backend.app.services.sla_service import SLAService

API = "/api/v1/complaints"


def run_check(db, minutes_from_now=0):
    from backend.app.core.timeutil import utcnow

    system = AuthService(db).ensure_system_user()
    return SLAService(db).run_check(system.user_id, now=utcnow() + timedelta(minutes=minutes_from_now))


@pytest.mark.req("FR-16", "BR-06")
@pytest.mark.parametrize("priority,minutes", [("CRITICAL", 240), ("HIGH", 1440), ("MEDIUM", 4320), ("LOW", 10080)])
def test_sla_attached_from_priority_rule(client, user, submit, priority, minutes):
    c = submit(user, priority=priority)
    assert c["sla"]["target_duration"] == minutes


@pytest.mark.req("FR-16", "BR-06")
def test_updated_rule_applies_to_new_complaints(client, admin, user, submit):
    rules = client.get("/api/v1/sla/rules", headers=admin.headers).json()
    critical = next(r for r in rules if r["priority"] == "CRITICAL")
    res = client.patch(f"/api/v1/sla/rules/{critical['rule_id']}", json={"target_minutes": 60}, headers=admin.headers)
    assert res.status_code == 200
    assert submit(user, priority="CRITICAL")["sla"]["target_duration"] == 60


@pytest.mark.req("FR-16", "NFR-07")
@pytest.mark.parametrize("body", [{"target_minutes": 0}, {"approaching_percent": 100}, {"target_minutes": "abc"}])
def test_rule_validation(client, admin, body):
    rule = client.get("/api/v1/sla/rules", headers=admin.headers).json()[0]
    assert client.patch(f"/api/v1/sla/rules/{rule['rule_id']}", json=body, headers=admin.headers).status_code == 422


@pytest.mark.req("FR-17")
def test_approaching_deadline_notifies_once(client, db_session, user, admin, staff, submit):
    cid = submit(user, priority="CRITICAL")["complaint_id"]  # 240 minutes
    client.post(f"{API}/{cid}/assign", json={"staff_id": staff.id}, headers=admin.headers)
    assert run_check(db_session, minutes_from_now=60)["approaching_notified"] == 0
    assert run_check(db_session, minutes_from_now=200)["approaching_notified"] == 1
    assert run_check(db_session, minutes_from_now=210)["approaching_notified"] == 0  # idempotent
    events = [n["event_type"] for n in client.get("/api/v1/notifications", headers=staff.headers).json()["items"]]
    assert "SLA_APPROACHING" in events
    detail = client.get(f"{API}/{cid}", headers=staff.headers).json()
    assert detail["sla"]["state"] in ("ON_TRACK", "APPROACHING")


@pytest.mark.req("FR-18", "BR-07", "FR-19")
def test_overdue_complaint_escalated_once(client, db_session, user, admin, staff, submit):
    cid = submit(user, priority="CRITICAL")["complaint_id"]
    client.post(f"{API}/{cid}/assign", json={"staff_id": staff.id}, headers=admin.headers)
    first = run_check(db_session, minutes_from_now=241)
    second = run_check(db_session, minutes_from_now=300)
    assert first["escalated"] == 1 and second["escalated"] == 0  # SDD §10.3 idempotency

    detail = client.get(f"{API}/{cid}", headers=admin.headers).json()
    assert detail["status"] == "ESCALATED"
    assert detail["sla"]["escalation_level"] == 1
    assert detail["history"][-1]["changed_by"]["name"] == "System"

    # FR-19: escalated complaints are visible to administrators
    escalated = client.get(API, params={"status": "ESCALATED"}, headers=admin.headers).json()
    assert [c["complaint_id"] for c in escalated["items"]] == [cid]
    for actor in (admin, staff):
        events = [n["event_type"] for n in client.get("/api/v1/notifications", headers=actor.headers).json()["items"]]
        assert "COMPLAINT_ESCALATED" in events

    # the resolver resumes and resolves the escalated complaint
    assert client.patch(f"{API}/{cid}/status", json={"new_status": "IN_PROGRESS"}, headers=staff.headers).status_code == 200
    res = client.post(f"{API}/{cid}/resolve", json={"resolution_details": "Fixed after escalation."}, headers=staff.headers)
    assert res.json()["status"] == "RESOLVED"


@pytest.mark.req("FR-18")
def test_resolved_complaints_are_not_escalated(client, db_session, user, admin, staff, submit):
    cid = submit(user, priority="CRITICAL")["complaint_id"]
    client.post(f"{API}/{cid}/assign", json={"staff_id": staff.id}, headers=admin.headers)
    client.patch(f"{API}/{cid}/status", json={"new_status": "IN_PROGRESS"}, headers=staff.headers)
    client.post(f"{API}/{cid}/resolve", json={"resolution_details": "Done quickly."}, headers=staff.headers)
    assert run_check(db_session, minutes_from_now=10_000)["escalated"] == 0


@pytest.mark.req("FR-18")
def test_unassigned_overdue_complaint_escalates_and_must_be_assigned(client, db_session, user, admin, staff, submit):
    cid = submit(user, priority="CRITICAL")["complaint_id"]
    assert run_check(db_session, minutes_from_now=300)["escalated"] == 1
    assert client.patch(f"{API}/{cid}/status", json={"new_status": "IN_PROGRESS"}, headers=admin.headers).status_code == 400
    res = client.post(f"{API}/{cid}/assign", json={"staff_id": staff.id}, headers=admin.headers)
    assert res.json()["status"] == "ASSIGNED"


@pytest.mark.req("FR-19", "BR-09")
def test_manual_escalation_admin_only(client, user, admin, staff, submit):
    cid = submit(user)["complaint_id"]
    client.post(f"{API}/{cid}/assign", json={"staff_id": staff.id}, headers=admin.headers)
    assert client.patch(f"{API}/{cid}/status", json={"new_status": "ESCALATED"}, headers=staff.headers).status_code == 403
    res = client.patch(f"{API}/{cid}/status", json={"new_status": "ESCALATED"}, headers=admin.headers)
    assert res.status_code == 200 and res.json()["status"] == "ESCALATED"


def test_overdue_filter(client, db_session, user, admin, submit):
    cid = submit(user, priority="CRITICAL")["complaint_id"]
    submit(user, priority="LOW")
    sla = db_session.query(SLA).join(Complaint).filter(Complaint.complaint_id == __import__("uuid").UUID(cid)).one()
    sla.deadline = as_utc(sla.deadline) - timedelta(days=2)
    db_session.commit()
    res = client.get(API, params={"overdue": True}, headers=admin.headers).json()
    assert [c["complaint_id"] for c in res["items"]] == [cid]
    assert res["items"][0]["sla"]["state"] == "OVERDUE"


def test_sla_check_endpoint_admin_only(client, admin, user):
    assert client.post("/api/v1/sla/check", headers=user.headers).status_code == 403
    assert client.post("/api/v1/sla/check", headers=admin.headers).json() == {"checked": 0, "approaching_notified": 0, "escalated": 0}
