"""Role permission matrix (Software Design Appendix A; NFR-05, NFR-06, BR-09)."""
import pytest

pytestmark = pytest.mark.req("NFR-05", "NFR-06", "BR-09")

ZERO = "00000000-0000-0000-0000-000000000000"

# (method, path, body, {role: expected status}); "anon" = no token
MATRIX = [
    ("GET", "/api/v1/complaints", None, {"anon": 401, "USER": 200, "STAFF": 200, "ADMIN": 200}),
    ("GET", "/api/v1/categories", None, {"anon": 401, "USER": 200, "STAFF": 200, "ADMIN": 200}),
    ("POST", "/api/v1/categories", {"name": "Transport"}, {"anon": 401, "USER": 403, "STAFF": 403, "ADMIN": 201}),
    ("GET", "/api/v1/sla/rules", None, {"anon": 401, "USER": 403, "STAFF": 403, "ADMIN": 200}),
    ("POST", "/api/v1/sla/check", None, {"anon": 401, "USER": 403, "STAFF": 403, "ADMIN": 200}),
    ("GET", "/api/v1/users", None, {"anon": 401, "USER": 403, "STAFF": 403, "ADMIN": 200}),
    ("POST", "/api/v1/users", {"name": "X Y", "email": "xy@test.example.com", "password": "Strong123", "role": "STAFF"},
     {"anon": 401, "USER": 403, "STAFF": 403, "ADMIN": 201}),
    ("GET", "/api/v1/reports/summary", None, {"anon": 401, "USER": 403, "STAFF": 200, "ADMIN": 200}),
    ("GET", "/api/v1/reports/complaints", None, {"anon": 401, "USER": 403, "STAFF": 403, "ADMIN": 200}),
    ("GET", "/api/v1/reports/complaints.csv", None, {"anon": 401, "USER": 403, "STAFF": 403, "ADMIN": 200}),
    ("GET", "/api/v1/notifications", None, {"anon": 401, "USER": 200, "STAFF": 200, "ADMIN": 200}),
    ("GET", "/api/v1/complaints?scope=all", None, {"anon": 401, "USER": 200, "STAFF": 403, "ADMIN": 200}),
    ("POST", f"/api/v1/complaints/{ZERO}/assign", {"staff_id": ZERO}, {"anon": 401, "USER": 403, "STAFF": 404, "ADMIN": 404}),
]


@pytest.mark.parametrize("method,path,body,expected", MATRIX, ids=[f"{m} {p}" for m, p, _, _ in MATRIX])
@pytest.mark.parametrize("role", ["anon", "USER", "STAFF", "ADMIN"])
def test_role_matrix(client, admin, make_user, method, path, body, expected, role):
    headers = {} if role == "anon" else admin.headers if role == "ADMIN" else make_user(role).headers
    res = client.request(method, path, json=body, headers=headers)
    assert res.status_code == expected[role], f"{role} {method} {path}: {res.status_code} {res.text}"


def test_health_is_public(client):
    assert client.get("/api/v1/health").json() == {"status": "ok"}
