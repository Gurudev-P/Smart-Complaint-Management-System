import pytest

from backend.app.jobs import scheduler
from backend.app.services import notification_service


@pytest.mark.req("FR-17", "FR-18")
def test_scheduler_entry_point_runs_check(client, user, submit):
    submit(user)
    assert scheduler.run_sla_check_once() == {"checked": 1, "approaching_notified": 0, "escalated": 0}


class RecordingAdapter:
    channel = "EMAIL"

    def __init__(self, fail=False):
        self.sent, self.fail = [], fail

    def send(self, recipient, message):
        if self.fail:
            raise RuntimeError("provider down")
        self.sent.append((recipient.email, message))


@pytest.mark.req("FR-21")
def test_external_channel_adapters_receive_events_and_failures_are_isolated(client, user, submit, monkeypatch):
    ok, broken = RecordingAdapter(), RecordingAdapter(fail=True)
    monkeypatch.setattr(notification_service, "_external_adapters", [broken, ok])
    c = submit(user)  # must still succeed although one provider fails
    assert ok.sent and ok.sent[0][0] == user.user.email and c["reference"] in ok.sent[0][1]
