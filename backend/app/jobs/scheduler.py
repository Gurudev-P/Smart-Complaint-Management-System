"""Background Scheduler: periodic SLA monitoring (SDD §6.3)."""
import asyncio
import logging

from backend.app.core.config import settings
from backend.app.db.session import SessionLocal
from backend.app.services.auth_service import AuthService
from backend.app.services.sla_service import SLAService

log = logging.getLogger(__name__)


def run_sla_check_once() -> dict:
    db = SessionLocal()
    try:
        system = AuthService(db).ensure_system_user()
        return SLAService(db).run_check(system.user_id)
    finally:
        db.close()


async def sla_loop() -> None:
    while True:
        try:
            await asyncio.to_thread(run_sla_check_once)
        except Exception:  # keep the scheduler alive after a failed run
            log.exception("SLA check failed")
        await asyncio.sleep(settings.SLA_CHECK_INTERVAL_SECONDS)
