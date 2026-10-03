"""Starts the real application (uvicorn + SQLite file DB + seeded demo data) for browser tests."""
import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[2]


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def live_server(tmp_path_factory):
    db = tmp_path_factory.mktemp("e2e") / "e2e.db"
    port = _free_port()
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{db}",
        "ENABLE_SCHEDULER": "false",
        "BCRYPT_ROUNDS": "4",
        "SECRET_KEY": "e2e-secret-key-that-is-long-enough-0123456789",
        "NO_PROXY": "127.0.0.1,localhost",
    }
    setup = (
        "from backend.app.db.base import Base; from backend.app.db.session import engine; "
        "import backend.app.models; Base.metadata.create_all(engine); "
        "from backend.app.seed import seed; seed()"
    )
    subprocess.run([sys.executable, "-c", setup], cwd=ROOT, env=env, check=True, capture_output=True)
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--port", str(port), "--log-level", "warning"],
        cwd=ROOT, env=env,
    )
    url = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            if httpx.get(f"{url}/api/v1/health", timeout=1).status_code == 200:
                break
        except httpx.HTTPError:
            time.sleep(0.1)
    else:
        proc.kill()
        raise RuntimeError("live server did not start")
    yield url
    proc.terminate()
    proc.wait(timeout=10)


@pytest.fixture(scope="session")
def base_url(live_server):
    return live_server


@pytest.fixture()
def page(page):
    page.set_default_timeout(10_000)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    yield page
    assert not errors, f"JavaScript errors: {errors}"
    text = page.locator("body").inner_text()
    assert not re.search(r"\b(undefined|null|NaN|\[object Object\])\b", text), "Rendering artefact on page"
