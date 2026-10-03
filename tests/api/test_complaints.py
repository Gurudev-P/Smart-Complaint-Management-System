import pytest

API = "/api/v1/complaints"


@pytest.mark.req("FR-05", "FR-06", "BR-01")
def test_submit_complaint(client, user, category):
    res = client.post(API, json={"category_id": str(category.category_id), "priority": "HIGH", "description": "  Lab 3 PCs will not boot.  "}, headers=user.headers)
    assert res.status_code == 201
    c = res.json()
    assert c["reference"].startswith("CMP-")
    assert c["status"] == "SUBMITTED"
    assert c["priority"] == "HIGH"
    assert c["category"]["name"] == "IT & Network"
    assert c["creator"]["user_id"] == user.id
    assert c["description"] == "Lab 3 PCs will not boot."
    assert c["created_at"]
    assert c["sla"]["state"] == "ON_TRACK"


@pytest.mark.req("BR-01", "NFR-05")
def test_submit_requires_authentication(client, category):
    res = client.post(API, json={"category_id": str(category.category_id), "priority": "LOW", "description": "No login here"})
    assert res.status_code == 401


@pytest.mark.req("FR-08", "NFR-07")
@pytest.mark.parametrize("missing", ["category_id", "priority", "description"])
def test_missing_mandatory_field_rejected(client, user, category, missing):
    body = {"category_id": str(category.category_id), "priority": "LOW", "description": "Valid description"}
    body.pop(missing)
    res = client.post(API, json=body, headers=user.headers)
    assert res.status_code == 422
    assert any(e["field"] == missing for e in res.json()["errors"])


@pytest.mark.req("FR-09", "BR-02")
def test_unknown_category_rejected(client, user):
    res = client.post(API, json={"category_id": "00000000-0000-0000-0000-000000000000", "priority": "LOW", "description": "Valid description"}, headers=user.headers)
    assert res.status_code == 400


@pytest.mark.req("FR-09", "BR-02")
def test_inactive_category_rejected(client, user, category, db_session):
    category.active_flag = False
    db_session.commit()
    res = client.post(API, json={"category_id": str(category.category_id), "priority": "LOW", "description": "Valid description"}, headers=user.headers)
    assert res.status_code == 400


@pytest.mark.req("FR-07")
def test_view_status_and_history(client, user, submit):
    c = submit(user)
    res = client.get(f"{API}/{c['complaint_id']}", headers=user.headers)
    assert res.status_code == 200
    detail = res.json()
    assert detail["status"] == "SUBMITTED"
    assert len(detail["history"]) == 1
    assert detail["history"][0]["changed_by"]["user_id"] == user.id


@pytest.mark.req("BR-08")
def test_users_only_see_their_own_complaints(client, make_user, submit):
    alice, bob = make_user(), make_user()
    a = submit(alice)
    submit(bob)
    listing = client.get(API, headers=alice.headers).json()
    assert listing["total"] == 1
    assert listing["items"][0]["complaint_id"] == a["complaint_id"]
    # scope=all is ignored for normal users
    assert client.get(API, params={"scope": "all"}, headers=alice.headers).json()["total"] == 1
    # direct access to someone else's complaint is reported as not found
    assert client.get(f"{API}/{a['complaint_id']}", headers=bob.headers).status_code == 404


def test_unknown_complaint_404(client, user):
    assert client.get(f"{API}/00000000-0000-0000-0000-000000000000", headers=user.headers).status_code == 404
    assert client.get(f"{API}/not-a-uuid", headers=user.headers).status_code == 422


def test_creator_can_edit_before_assignment_only(client, user, admin, staff, submit):
    c = submit(user)
    res = client.patch(f"{API}/{c['complaint_id']}", json={"description": "Updated description text"}, headers=user.headers)
    assert res.status_code == 200 and res.json()["description"] == "Updated description text"
    client.post(f"{API}/{c['complaint_id']}/assign", json={"staff_id": staff.id}, headers=admin.headers)
    res = client.patch(f"{API}/{c['complaint_id']}", json={"description": "Another change here"}, headers=user.headers)
    assert res.status_code == 403


@pytest.mark.req("FR-10")
def test_priority_change_by_handler_recalculates_sla(client, user, admin, submit):
    c = submit(user, priority="LOW")
    before = c["sla"]
    assert before["target_duration"] == 7 * 24 * 60
    # the creator cannot change priority
    assert client.patch(f"{API}/{c['complaint_id']}", json={"priority": "CRITICAL"}, headers=user.headers).status_code == 403
    res = client.patch(f"{API}/{c['complaint_id']}", json={"priority": "CRITICAL"}, headers=admin.headers)
    assert res.status_code == 200
    after = res.json()["sla"]
    assert res.json()["priority"] == "CRITICAL"
    assert after["target_duration"] == 4 * 60
    assert after["deadline"] < before["deadline"]


def test_empty_update_rejected(client, user, submit):
    c = submit(user)
    assert client.patch(f"{API}/{c['complaint_id']}", json={}, headers=user.headers).status_code == 400


@pytest.mark.req("FR-23")
def test_filters_search_and_pagination(client, admin, user, submit):
    for i in range(7):
        submit(user, priority="HIGH" if i % 2 else "LOW", description=f"Broken chair number {i} in hall")
    submit(user, priority="CRITICAL", description="Water leakage near the server room")

    h = admin.headers
    assert client.get(API, params={"priority": "HIGH"}, headers=h).json()["total"] == 3
    assert client.get(API, params={"q": "leakage"}, headers=h).json()["total"] == 1
    assert client.get(API, params={"q": "it & network"}, headers=h).json()["total"] == 8  # category name search
    assert client.get(API, params={"status": ["SUBMITTED", "ASSIGNED"]}, headers=h).json()["total"] == 8
    page = client.get(API, params={"limit": 5, "offset": 5}, headers=h).json()
    assert page["total"] == 8 and len(page["items"]) == 3
    assert client.get(API, params={"status": "BOGUS"}, headers=h).status_code == 400
    assert client.get(API, params={"limit": 1000}, headers=h).status_code == 422
