"""Response time under the expected project workload (NFR-01)."""
import statistics
import time
import uuid

import pytest

from backend.app.core.timeutil import utcnow
from backend.app.models import SLA, Complaint, StatusHistory

pytestmark = pytest.mark.req("NFR-01")


@pytest.fixture()
def bulk(db_session, user, category):
    now = utcnow()
    for i in range(500):
        cid = uuid.uuid4()
        db_session.add(Complaint(complaint_id=cid, user_id=user.user.user_id, category_id=category.category_id,
                                 priority=["LOW", "MEDIUM", "HIGH", "CRITICAL"][i % 4], status="SUBMITTED",
                                 description=f"Bulk complaint number {i}", created_at=now, updated_at=now))
        db_session.add(SLA(complaint_id=cid, target_duration=60, deadline=now, escalation_level=0))
        db_session.add(StatusHistory(complaint_id=cid, old_status="SUBMITTED", new_status="SUBMITTED", changed_by=user.user.user_id, changed_at=now))
    db_session.commit()


def p95(samples):
    return statistics.quantiles(samples, n=20)[-1]


@pytest.mark.parametrize("path", ["/api/v1/complaints?scope=all&limit=20", "/api/v1/reports/summary", "/api/v1/complaints?q=number%201&scope=all"])
def test_p95_under_three_seconds(client, admin, bulk, path):
    samples = []
    for _ in range(20):
        start = time.perf_counter()
        res = client.get(path, headers=admin.headers)
        samples.append(time.perf_counter() - start)
        assert res.status_code == 200
    assert p95(samples) < 3.0, f"p95={p95(samples):.3f}s"
