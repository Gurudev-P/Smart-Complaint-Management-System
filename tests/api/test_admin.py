"""Administration: users, categories (FR-09, BR-09, Manage Users/Categories use case)."""
import pytest

from tests.conftest import PASSWORD


@pytest.mark.req("FR-09", "BR-09")
def test_category_management_admin_only(client, admin, user):
    body = {"name": "Hostel", "description": "Rooms and mess"}
    assert client.post("/api/v1/categories", json=body, headers=user.headers).status_code == 403
    res = client.post("/api/v1/categories", json=body, headers=admin.headers)
    assert res.status_code == 201
    cid = res.json()["category_id"]
    assert client.post("/api/v1/categories", json={"name": "hostel"}, headers=admin.headers).status_code == 409
    assert client.patch(f"/api/v1/categories/{cid}", json={"active_flag": False}, headers=user.headers).status_code == 403
    assert client.patch(f"/api/v1/categories/{cid}", json={"active_flag": False}, headers=admin.headers).json()["active_flag"] is False
    # inactive categories are hidden from users but visible to admins on request
    assert [c["name"] for c in client.get("/api/v1/categories", headers=user.headers).json()] == []
    assert [c["name"] for c in client.get("/api/v1/categories", params={"include_inactive": True}, headers=admin.headers).json()] == ["Hostel"]
    assert [c["name"] for c in client.get("/api/v1/categories", params={"include_inactive": True}, headers=user.headers).json()] == []


@pytest.mark.req("FR-09", "NFR-07")
def test_category_validation(client, admin, category):
    assert client.post("/api/v1/categories", json={"name": " "}, headers=admin.headers).status_code == 422
    assert client.post("/api/v1/categories", json={"name": "x" * 101}, headers=admin.headers).status_code == 422
    assert client.patch(f"/api/v1/categories/{category.category_id}", json={"name": "it & NETWORK"}, headers=admin.headers).status_code == 200
    assert client.patch("/api/v1/categories/00000000-0000-0000-0000-000000000000", json={"name": "Zed"}, headers=admin.headers).status_code == 404


@pytest.mark.req("FR-03", "BR-09")
def test_admin_creates_staff_who_can_login(client, admin, user):
    body = {"name": "New Staff", "email": "newstaff@test.example.com", "password": PASSWORD, "role": "STAFF"}
    assert client.post("/api/v1/users", json=body, headers=user.headers).status_code == 403
    res = client.post("/api/v1/users", json=body, headers=admin.headers)
    assert res.status_code == 201 and res.json()["role"] == "STAFF"
    login = client.post("/api/v1/auth/login", json={"email": body["email"], "password": PASSWORD})
    assert login.json()["user"]["role"] == "STAFF"


@pytest.mark.req("FR-03")
def test_role_change_and_listing(client, admin, user, staff):
    res = client.patch(f"/api/v1/users/{user.id}", json={"role": "STAFF"}, headers=admin.headers)
    assert res.json()["role"] == "STAFF"
    staff_list = client.get("/api/v1/users", params={"role": "STAFF"}, headers=admin.headers).json()
    assert {u["user_id"] for u in staff_list} == {user.id, staff.id}
    # the internal System account never appears
    assert all(u["email"] != "system@scms.local" for u in client.get("/api/v1/users", headers=admin.headers).json())


def test_admin_cannot_lock_themselves_out(client, admin):
    assert client.patch(f"/api/v1/users/{admin.id}", json={"role": "USER"}, headers=admin.headers).status_code == 400
    assert client.patch(f"/api/v1/users/{admin.id}", json={"account_status": "INACTIVE"}, headers=admin.headers).status_code == 400


def test_staff_can_list_staff_for_assignment_only(client, staff, user):
    assert client.get("/api/v1/users", params={"role": "STAFF"}, headers=staff.headers).status_code == 200
    assert client.get("/api/v1/users", headers=staff.headers).status_code == 403
    assert client.get("/api/v1/users", params={"role": "STAFF"}, headers=user.headers).status_code == 403


def test_bootstrap_admin_and_default_rules(client, admin):
    assert admin.user.role == "ADMIN"
    rules = client.get("/api/v1/sla/rules", headers=admin.headers).json()
    assert [r["priority"] for r in rules] == ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
