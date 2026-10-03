"""Assignment, status updates and resolution (FR-12–FR-15, FR-20, BR-03–BR-05, BR-10)."""
import pytest

from backend.app.core.constants import Role

API = "/api/v1/complaints"


def assign(client, actor, cid, staff_id):
    return client.post(f"{API}/{cid}/assign", json={"staff_id": staff_id}, headers=actor.headers)


def status(client, actor, cid, new, expected=None):
    body = {"new_status": new}
    if expected:
        body["expected_status"] = expected
    return client.patch(f"{API}/{cid}/status", json=body, headers=actor.headers)


def resolve(client, actor, cid, details="Replaced the faulty router and verified connectivity."):
    return client.post(f"{API}/{cid}/resolve", json={"resolution_details": details}, headers=actor.headers)


@pytest.mark.req("FR-12", "FR-13", "FR-14", "FR-15", "BR-10")
def test_full_lifecycle(client, user, admin, staff, submit):
    cid = submit(user)["complaint_id"]

    res = assign(client, admin, cid, staff.id)
    assert res.status_code == 200
    assert res.json()["status"] == "ASSIGNED" and res.json()["assignee"]["user_id"] == staff.id

    # the assigned complaint appears in the staff member's queue
    queue = client.get(API, params={"scope": "assigned"}, headers=staff.headers).json()
    assert [c["complaint_id"] for c in queue["items"]] == [cid]

    assert status(client, staff, cid, "IN_PROGRESS").json()["status"] == "IN_PROGRESS"
    res = resolve(client, staff, cid)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "RESOLVED"
    assert body["resolution"]["resolver"]["user_id"] == staff.id
    assert body["sla"]["state"] == "MET"

    res = status(client, admin, cid, "CLOSED")
    assert res.status_code == 200
    history = [(h["old_status"], h["new_status"]) for h in res.json()["history"]]
    assert history == [
        ("SUBMITTED", "SUBMITTED"),
        ("SUBMITTED", "ASSIGNED"),
        ("ASSIGNED", "IN_PROGRESS"),
        ("IN_PROGRESS", "RESOLVED"),
        ("RESOLVED", "CLOSED"),
    ]


@pytest.mark.req("FR-12", "BR-03")
def test_normal_user_cannot_assign(client, user, staff, submit):
    cid = submit(user)["complaint_id"]
    assert assign(client, user, cid, staff.id).status_code == 403


@pytest.mark.req("FR-12")
def test_assign_target_must_be_active_staff(client, user, admin, make_user, submit):
    cid = submit(user)["complaint_id"]
    other_user = make_user(Role.USER)
    assert assign(client, admin, cid, other_user.id).status_code == 400
    assert assign(client, admin, cid, "00000000-0000-0000-0000-000000000000").status_code == 400
    inactive = make_user(Role.STAFF)
    client.patch(f"/api/v1/users/{inactive.id}", json={"account_status": "INACTIVE"}, headers=admin.headers)
    assert assign(client, admin, cid, inactive.id).status_code == 400


@pytest.mark.req("FR-12")
def test_staff_can_take_unassigned_complaints_and_reassign(client, user, staff, make_user, submit):
    cid = submit(user)["complaint_id"]
    unassigned = client.get(API, params={"scope": "unassigned"}, headers=staff.headers).json()
    assert [c["complaint_id"] for c in unassigned["items"]] == [cid]
    assert assign(client, staff, cid, staff.id).status_code == 200
    assert assign(client, staff, cid, staff.id).status_code == 409  # already assigned
    other = make_user(Role.STAFF)
    res = assign(client, staff, cid, other.id)
    assert res.status_code == 200 and res.json()["assignee"]["user_id"] == other.id
    # previous assignee no longer sees it in their queue
    assert client.get(API, params={"scope": "assigned"}, headers=staff.headers).json()["total"] == 0


@pytest.mark.req("BR-04")
def test_only_assigned_staff_can_update(client, user, admin, staff, make_user, submit):
    cid = submit(user)["complaint_id"]
    assign(client, admin, cid, staff.id)
    intruder = make_user(Role.STAFF)
    assert status(client, intruder, cid, "IN_PROGRESS").status_code == 403
    assert status(client, user, cid, "IN_PROGRESS").status_code == 403
    assert status(client, staff, cid, "IN_PROGRESS").status_code == 200
    assert resolve(client, intruder, cid).status_code in (403, 404)


@pytest.mark.req("FR-13", "NFR-03")
@pytest.mark.parametrize("new", ["RESOLVED", "ASSIGNED", "SUBMITTED", "CLOSED"])
def test_invalid_transitions_rejected(client, user, admin, staff, submit, new):
    cid = submit(user)["complaint_id"]
    assign(client, admin, cid, staff.id)
    res = status(client, admin, cid, new)
    assert res.status_code == 400
    assert client.get(f"{API}/{cid}", headers=admin.headers).json()["status"] == "ASSIGNED"


@pytest.mark.req("FR-14", "BR-05")
def test_resolution_details_required(client, user, admin, staff, submit):
    cid = submit(user)["complaint_id"]
    assign(client, admin, cid, staff.id)
    status(client, staff, cid, "IN_PROGRESS")
    assert resolve(client, staff, cid, details="   ").status_code == 422
    assert client.post(f"{API}/{cid}/resolve", json={}, headers=staff.headers).status_code == 422
    assert client.get(f"{API}/{cid}", headers=staff.headers).json()["status"] == "IN_PROGRESS"


@pytest.mark.req("FR-14")
def test_cannot_resolve_before_work_starts_or_twice(client, user, admin, staff, submit):
    cid = submit(user)["complaint_id"]
    assign(client, admin, cid, staff.id)
    assert resolve(client, staff, cid).status_code == 400
    status(client, staff, cid, "IN_PROGRESS")
    assert resolve(client, staff, cid).status_code == 200
    assert resolve(client, staff, cid).status_code == 400


@pytest.mark.req("NFR-03")
def test_stale_expected_status_conflict(client, user, admin, staff, submit):
    cid = submit(user)["complaint_id"]
    assign(client, admin, cid, staff.id)
    assert status(client, staff, cid, "IN_PROGRESS", expected="SUBMITTED").status_code == 409


@pytest.mark.req("BR-09")
def test_close_is_admin_only(client, user, admin, staff, submit):
    cid = submit(user)["complaint_id"]
    assign(client, admin, cid, staff.id)
    status(client, staff, cid, "IN_PROGRESS")
    resolve(client, staff, cid)
    assert status(client, staff, cid, "CLOSED").status_code == 403
    assert status(client, user, cid, "CLOSED").status_code == 403
    assert status(client, admin, cid, "CLOSED").status_code == 200
    assert assign(client, admin, cid, staff.id).status_code == 400  # closed is final


@pytest.mark.req("FR-20", "FR-21")
def test_notifications_follow_the_workflow(client, user, admin, staff, submit):
    cid = submit(user, priority="HIGH")["complaint_id"]
    admin_notes = client.get("/api/v1/notifications", headers=admin.headers).json()
    assert any(n["event_type"] == "COMPLAINT_SUBMITTED" for n in admin_notes["items"])  # high priority alert

    assign(client, admin, cid, staff.id)
    staff_notes = client.get("/api/v1/notifications", headers=staff.headers).json()
    assert staff_notes["unread"] == 1 and staff_notes["items"][0]["event_type"] == "COMPLAINT_ASSIGNED"
    assert staff_notes["items"][0]["channel"] == "IN_APP"

    status(client, staff, cid, "IN_PROGRESS")
    resolve(client, staff, cid)
    events = [n["event_type"] for n in client.get("/api/v1/notifications", headers=user.headers).json()["items"]]
    assert events.count("STATUS_CHANGED") == 3  # assigned, in progress, resolved
    assert "COMPLAINT_SUBMITTED" in events


@pytest.mark.req("FR-20")
def test_mark_notifications_read(client, user, admin, submit):
    submit(user)
    notes = client.get("/api/v1/notifications", headers=user.headers).json()
    nid = notes["items"][0]["notification_id"]
    assert client.patch(f"/api/v1/notifications/{nid}/read", headers=admin.headers).status_code == 403
    assert client.patch(f"/api/v1/notifications/{nid}/read", headers=user.headers).json()["read_status"] is True
    assert client.get("/api/v1/notifications", params={"unread_only": True}, headers=user.headers).json()["items"] == []
    submit(user)
    assert client.post("/api/v1/notifications/read-all", headers=user.headers).json()["updated"] == 1
