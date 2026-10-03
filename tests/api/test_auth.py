import pytest

from backend.app.models import User
from tests.conftest import PASSWORD

API = "/api/v1/auth"


@pytest.mark.req("FR-01")
def test_register_creates_user_account(client):
    res = client.post(f"{API}/register", json={"name": "Asha Rao", "email": "Asha@Test.Example.com", "password": "Strong123"})
    assert res.status_code == 201
    body = res.json()
    assert body["email"] == "asha@test.example.com"
    assert body["role"] == "USER"
    assert "password" not in body and "password_hash" not in body


@pytest.mark.req("FR-01")
def test_self_registration_cannot_choose_admin_role(client):
    res = client.post(f"{API}/register", json={"name": "Eve", "email": "eve@test.example.com", "password": "Strong123", "role": "ADMIN"})
    assert res.status_code == 201
    assert res.json()["role"] == "USER"


@pytest.mark.req("FR-01")
def test_duplicate_email_conflict(client):
    body = {"name": "Asha", "email": "dup@test.example.com", "password": "Strong123"}
    assert client.post(f"{API}/register", json=body).status_code == 201
    body["email"] = "DUP@test.example.com"
    res = client.post(f"{API}/register", json=body)
    assert res.status_code == 409


@pytest.mark.req("FR-01", "NFR-07")
@pytest.mark.parametrize(
    "body",
    [
        {"name": "A", "email": "a@test.example.com", "password": "Strong123"},
        {"name": "Asha", "email": "bad", "password": "Strong123"},
        {"name": "Asha", "email": "a@test.example.com", "password": "weak"},
        {"email": "a@test.example.com", "password": "Strong123"},
    ],
)
def test_register_validation(client, body):
    res = client.post(f"{API}/register", json=body)
    assert res.status_code == 422
    assert res.json()["errors"]


@pytest.mark.req("NFR-04")
def test_password_stored_hashed(client, db_session):
    client.post(f"{API}/register", json={"name": "Asha", "email": "h@test.example.com", "password": "Strong123"})
    stored = db_session.query(User).filter_by(email="h@test.example.com").one()
    assert stored.password_hash != "Strong123"
    assert "Strong123" not in stored.password_hash


@pytest.mark.req("FR-02")
def test_login_returns_token_and_profile(client, user):
    res = client.get(f"{API}/me", headers=user.headers)
    assert res.status_code == 200
    assert res.json()["user_id"] == user.id


@pytest.mark.req("FR-04")
@pytest.mark.parametrize("email,password", [("nobody@test.example.com", PASSWORD), (None, "WrongPass1")])
def test_invalid_credentials_generic_401(client, user, email, password):
    res = client.post(f"{API}/login", json={"email": email or user.user.email, "password": password})
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid email or password"


@pytest.mark.req("FR-04")
def test_inactive_account_cannot_login(client, admin, user):
    client.patch(f"/api/v1/users/{user.id}", json={"account_status": "INACTIVE"}, headers=admin.headers)
    res = client.post(f"{API}/login", json={"email": user.user.email, "password": PASSWORD})
    assert res.status_code == 403
    # an existing token stops working too
    assert client.get(f"{API}/me", headers=user.headers).status_code == 401


@pytest.mark.req("FR-02", "NFR-05")
@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer not.a.token"}, {"Authorization": "Basic abc"}])
def test_protected_endpoint_requires_valid_token(client, headers):
    res = client.get(f"{API}/me", headers=headers)
    assert res.status_code == 401


@pytest.mark.req("FR-04")
def test_system_account_cannot_login(client):
    res = client.post(f"{API}/login", json={"email": "system@scms.example.com", "password": "anything1"})
    assert res.status_code == 401


def test_logout(client, user):
    assert client.post(f"{API}/logout", headers=user.headers).status_code == 204
