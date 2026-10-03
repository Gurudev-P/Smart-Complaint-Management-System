import pytest

from backend.app.core.constants import TRANSITIONS, Status, can_transition

pytestmark = pytest.mark.req("FR-13", "FR-15", "BR-04")

ALLOWED = [
    ("SUBMITTED", "ASSIGNED"),
    ("ASSIGNED", "IN_PROGRESS"),
    ("IN_PROGRESS", "IN_PROGRESS"),
    ("IN_PROGRESS", "ESCALATED"),
    ("ESCALATED", "IN_PROGRESS"),
    ("IN_PROGRESS", "RESOLVED"),
    ("RESOLVED", "CLOSED"),
]
FORBIDDEN = [
    ("SUBMITTED", "RESOLVED"),
    ("SUBMITTED", "IN_PROGRESS"),
    ("ASSIGNED", "RESOLVED"),
    ("RESOLVED", "IN_PROGRESS"),
    ("CLOSED", "IN_PROGRESS"),
    ("CLOSED", "SUBMITTED"),
    ("ESCALATED", "RESOLVED"),
]


@pytest.mark.parametrize("current,new", ALLOWED)
def test_design_transitions_are_allowed(current, new):
    assert can_transition(current, new)


@pytest.mark.parametrize("current,new", FORBIDDEN)
def test_undefined_transitions_are_rejected(current, new):
    assert not can_transition(current, new)


def test_closed_is_final():
    assert TRANSITIONS[Status.CLOSED] == set()


def test_every_status_has_a_rule():
    assert set(TRANSITIONS) == set(Status.ALL)
