"""Shared fixtures.

Tests run against SQLite in memory by default. Set TEST_DATABASE_URL to a PostgreSQL URL to run
the same suite against PostgreSQL (as the Jenkins pipeline does).
"""
import json
import os
import uuid
from collections import defaultdict
from pathlib import Path

os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")
os.environ["ENABLE_SCHEDULER"] = "false"
os.environ["BCRYPT_ROUNDS"] = "4"  # fast hashing for tests only
os.environ["ADMIN_EMAIL"] = "admin@test.example.com"
os.environ["ADMIN_PASSWORD"] = "Admin@1234"
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-long-enough-0123456789")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import backend.app.models  # noqa: E402,F401
from backend.app.core.constants import Role  # noqa: E402
from backend.app.db.base import Base  # noqa: E402
from backend.app.db.session import SessionLocal, engine  # noqa: E402
from backend.app.main import app  # noqa: E402
from backend.app.models import Category  # noqa: E402
from backend.app.services.auth_service import AuthService  # noqa: E402

PASSWORD = "Passw0rd!"


@pytest.fixture()
def db_session():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session):
    with TestClient(app) as c:
        yield c


class Actor:
    def __init__(self, user, token):
        self.user = user
        self.id = str(user.user_id)
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def make_user(client, db_session):
    def _make(role: str = Role.USER, name: str | None = None, email: str | None = None) -> Actor:
        email = email or f"{role.lower()}-{uuid.uuid4().hex[:8]}@test.example.com"
        user = AuthService(db_session).register(name or f"{role.title()} Person", email, PASSWORD, role)
        res = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
        assert res.status_code == 200, res.text
        return Actor(user, res.json()["access_token"])

    return _make


@pytest.fixture()
def admin(client):
    res = client.post("/api/v1/auth/login", json={"email": "admin@test.example.com", "password": "Admin@1234"})
    assert res.status_code == 200, res.text
    from backend.app.repositories.user_repository import UserRepository

    db = SessionLocal()
    try:
        user = UserRepository(db).get_by_email("admin@test.example.com")
    finally:
        db.close()
    return Actor(user, res.json()["access_token"])


@pytest.fixture()
def user(make_user):
    return make_user(Role.USER)


@pytest.fixture()
def staff(make_user):
    return make_user(Role.STAFF, name="Staff One")


@pytest.fixture()
def category(db_session):
    cat = Category(name="IT & Network", description="Wi-Fi, labs", active_flag=True)
    db_session.add(cat)
    db_session.commit()
    return cat


@pytest.fixture()
def submit(client, category):
    def _submit(actor: Actor, priority: str = "MEDIUM", description: str = "Projector in room 204 is not working.", **extra):
        body = {"category_id": str(category.category_id), "priority": priority, "description": description, **extra}
        res = client.post("/api/v1/complaints", json=body, headers=actor.headers)
        assert res.status_code == 201, res.text
        return res.json()

    return _submit


# ----------------------------------------------------------------------------- requirement report
_results: dict[str, list[dict]] = defaultdict(list)


def pytest_runtest_logreport(report):
    if report.when != "call" and not (report.when == "setup" and report.outcome != "passed"):
        return
    reqs = getattr(report, "_reqs", None)
    if reqs:
        for req in reqs:
            _results[req].append({"test": report.nodeid, "outcome": report.outcome})


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    ids = []
    for marker in item.iter_markers("req"):
        ids.extend(marker.args)
    report._reqs = ids


def pytest_sessionfinish(session):
    out = Path(os.environ.get("REQ_REPORT", "reports/requirements_results.json"))
    if not _results:
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if out.exists() and os.environ.get("REQ_REPORT_APPEND"):
        existing = json.loads(out.read_text())
    for req, rows in _results.items():
        existing.setdefault(req, []).extend(rows)
    out.write_text(json.dumps(existing, indent=2, sort_keys=True))
