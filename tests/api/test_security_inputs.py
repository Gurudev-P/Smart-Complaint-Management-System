"""Input handling and hardening (NFR-02, NFR-03, NFR-07)."""
import pytest

API = "/api/v1/complaints"


@pytest.mark.req("NFR-07")
def test_html_is_stored_as_plain_text(client, user, submit):
    payload = '<script>alert("x")</script><img src=x onerror=alert(1)>'
    c = submit(user, description=payload)
    assert client.get(f"{API}/{c['complaint_id']}", headers=user.headers).json()["description"] == payload
    # The frontend renders all values with textContent; see tests/e2e for the browser check.


@pytest.mark.req("NFR-07")
@pytest.mark.parametrize("q", ["' OR 1=1 --", "%", "_", "\\", "'; DROP TABLE complaints; --"])
def test_search_is_parameterised(client, admin, user, submit, q):
    submit(user)
    res = client.get(API, params={"q": q}, headers=admin.headers)
    assert res.status_code == 200
    assert client.get(API, headers=admin.headers).json()["total"] == 1


@pytest.mark.req("NFR-07")
def test_oversized_and_wrong_types(client, user, category):
    h = user.headers
    base = {"category_id": str(category.category_id), "priority": "LOW"}
    assert client.post(API, json={**base, "description": "x" * 2001}, headers=h).status_code == 422
    assert client.post(API, json={**base, "description": 12345678901}, headers=h).status_code == 422
    assert client.post(API, content=b"not json", headers={**h, "Content-Type": "application/json"}).status_code == 422
    assert client.get(API, params={"q": "x" * 101}, headers=h).status_code == 422


@pytest.mark.req("NFR-03")
def test_creator_cannot_overwrite_audit_fields(client, user, submit):
    c = submit(user)
    res = client.patch(f"{API}/{c['complaint_id']}", json={"description": "Changed text here", "status": "CLOSED", "user_id": "x"}, headers=user.headers)
    assert res.status_code == 200
    assert res.json()["status"] == "SUBMITTED"
    assert res.json()["creator"]["user_id"] == user.id


@pytest.mark.req("NFR-02")
def test_no_delete_endpoints_exist(client, admin, user, submit):
    c = submit(user)
    for path in (f"{API}/{c['complaint_id']}", f"/api/v1/users/{user.id}"):
        assert client.delete(path, headers=admin.headers).status_code == 405


def test_security_headers(client):
    res = client.get("/api/v1/health")
    assert res.headers["X-Content-Type-Options"] == "nosniff"
    assert res.headers["X-Frame-Options"] == "DENY"


def test_frontend_served(client):
    res = client.get("/")
    assert res.status_code == 200 and "<div id=\"app\"" in res.text
    assert client.get("/static/js/app.js").status_code == 200
