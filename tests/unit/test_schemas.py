import uuid

import pytest
from pydantic import ValidationError

from backend.app.schemas.auth import RegisterRequest
from backend.app.schemas.complaint import ComplaintCreateRequest, ResolutionRequest, StatusUpdateRequest

pytestmark = pytest.mark.req("NFR-07")


@pytest.mark.req("FR-01")
@pytest.mark.parametrize("password", ["short1", "allletters", "12345678", ""])
def test_weak_passwords_rejected(password):
    with pytest.raises(ValidationError):
        RegisterRequest(name="Asha", email="a@test.example.com", password=password)


@pytest.mark.req("FR-01")
def test_register_normalises_email_and_name():
    r = RegisterRequest(name="  Asha  ", email="ASHA@Test.Example.com", password="abcdefg1")
    assert r.name == "Asha"
    assert r.email == "asha@test.example.com"


@pytest.mark.req("FR-01")
def test_invalid_email_rejected():
    with pytest.raises(ValidationError):
        RegisterRequest(name="Asha", email="not-an-email", password="abcdefg1")


@pytest.mark.req("FR-08", "BR-02")
@pytest.mark.parametrize(
    "data",
    [
        {"priority": "HIGH", "description": "Long enough text"},  # missing category
        {"category_id": str(uuid.uuid4()), "description": "Long enough text"},  # missing priority
        {"category_id": str(uuid.uuid4()), "priority": "URGENT", "description": "Long enough text"},  # bad enum
        {"category_id": str(uuid.uuid4()), "priority": "HIGH", "description": "   short   "},  # too short after trim
        {"category_id": str(uuid.uuid4()), "priority": "HIGH", "description": "x" * 2001},  # too long
        {"category_id": "not-a-uuid", "priority": "HIGH", "description": "Long enough text"},
    ],
)
def test_invalid_complaint_payloads(data):
    with pytest.raises(ValidationError):
        ComplaintCreateRequest(**data)


@pytest.mark.req("FR-11")
@pytest.mark.parametrize("priority", ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
def test_all_priority_levels_accepted(priority):
    ComplaintCreateRequest(category_id=uuid.uuid4(), priority=priority, description="Valid description text")


@pytest.mark.req("BR-05")
def test_blank_resolution_rejected():
    with pytest.raises(ValidationError):
        ResolutionRequest(resolution_details="    ")


def test_unknown_status_rejected():
    with pytest.raises(ValidationError):
        StatusUpdateRequest(new_status="DONE")
