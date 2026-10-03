from datetime import datetime, timedelta, timezone

import pytest

from backend.app.services.sla_service import SLAState, compute_deadline, sla_state

T0 = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)


@pytest.mark.req("FR-16", "BR-06")
def test_deadline_is_creation_plus_target():
    assert compute_deadline(T0, 240) == T0 + timedelta(hours=4)


@pytest.mark.req("FR-16")
def test_naive_datetimes_are_treated_as_utc():
    assert compute_deadline(T0.replace(tzinfo=None), 60) == T0 + timedelta(hours=1)


def state(now_minutes, status="IN_PROGRESS", resolved_minutes=None, percent=80):
    deadline = T0 + timedelta(minutes=100)
    return sla_state(
        status=status,
        created_at=T0,
        deadline=deadline,
        approaching_percent=percent,
        now=T0 + timedelta(minutes=now_minutes),
        resolved_at=None if resolved_minutes is None else T0 + timedelta(minutes=resolved_minutes),
    )


@pytest.mark.req("FR-17")
@pytest.mark.parametrize(
    "minutes,expected",
    [(0, SLAState.ON_TRACK), (79, SLAState.ON_TRACK), (80, SLAState.APPROACHING), (100, SLAState.APPROACHING), (101, SLAState.OVERDUE)],
)
def test_open_complaint_state_boundaries(minutes, expected):
    assert state(minutes) == expected


@pytest.mark.req("FR-17")
def test_threshold_is_configurable():
    assert state(50, percent=50) == SLAState.APPROACHING
    assert state(49, percent=50) == SLAState.ON_TRACK


@pytest.mark.req("FR-24")
def test_resolved_before_deadline_is_met_after_is_breached():
    assert state(500, status="RESOLVED", resolved_minutes=90) == SLAState.MET
    assert state(500, status="CLOSED", resolved_minutes=120) == SLAState.BREACHED
