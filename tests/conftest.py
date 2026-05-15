from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from app.main import create_app
from app.core.config import settings


def _sync_database_url(async_url: str) -> str:
    if async_url.startswith("postgresql+asyncpg://"):
        return async_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
    return async_url


def _db_is_reachable() -> bool:
    url = _sync_database_url(os.getenv("DATABASE_URL", settings.DATABASE_URL))
    try:
        engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 2})
        with engine.connect():
            return True
    except OperationalError:
        return False


@pytest.fixture(scope="session", autouse=True)
def _migrate_db() -> None:
    if os.getenv("PYTEST_REQUIRE_DB") != "1" and not _db_is_reachable():
        pytest.skip("Database is not reachable. Start Postgres or run the docker-compose test profile.")
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("script_location", "alembic")
    command.upgrade(cfg, "head")


@pytest.fixture
async def client() -> AsyncClient:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
