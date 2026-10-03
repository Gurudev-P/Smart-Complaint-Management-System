import asyncio
import contextlib
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.v1 import api_router
from backend.app.core.config import settings
from backend.app.core.errors import DomainError
from backend.app.db.session import SessionLocal
from backend.app.jobs.scheduler import sla_loop
from backend.app.repositories.sla_rule_repository import SLARuleRepository
from backend.app.services.auth_service import AuthService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("scms")
for noisy in ("httpx", "httpx2"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


def bootstrap() -> None:
    db = SessionLocal()
    try:
        SLARuleRepository(db).ensure_defaults()
        db.commit()
        auth = AuthService(db)
        auth.ensure_system_user()
        if auth.bootstrap_admin():
            log.info("Bootstrap administrator account created")
    finally:
        db.close()


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    bootstrap()
    task = asyncio.create_task(sla_loop()) if settings.ENABLE_SCHEDULER else None
    yield
    if task:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


app = FastAPI(
    title="Smart Complaint Management System",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(DomainError)
async def domain_error_handler(_: Request, exc: DomainError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        field = ".".join(str(p) for p in err.get("loc", []) if p not in ("body", "query", "path"))
        message = err.get("msg", "Invalid value").removeprefix("Value error, ")
        errors.append({"field": field, "message": message})
    summary = "; ".join(f"{e['field']}: {e['message']}" if e["field"] else e["message"] for e in errors)
    return JSONResponse(status_code=422, content={"detail": summary, "errors": errors})


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    return response


@app.get("/api/v1/health")
def health_check():
    return {"status": "ok"}


app.include_router(api_router)

if settings.SERVE_FRONTEND and FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(FRONTEND_DIR / "index.html")
