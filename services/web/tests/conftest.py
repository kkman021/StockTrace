"""共用測試 fixtures：in-memory SQLite + FastAPI TestClient。

注意：backtest_runs / backtest_results 使用 PG-only 型別（ARRAY、JSONB），
此 fixture 不建立這兩張表。涉及它們的測試請改用實體 PG 整合測試。
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401  register tables on Base.metadata
from app.database import Base, get_db
from app.main import app


SQLITE_COMPATIBLE_TABLES = (
    "etf_list",
    "holding_records",
    "consensus_scores",
    "signal_records",
    "system_config",
    "crawl_logs",
)


@pytest.fixture
def engine():
    # StaticPool keeps a single connection so all sessions see the same in-memory DB.
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    tables = [Base.metadata.tables[name] for name in SQLITE_COMPATIBLE_TABLES]
    Base.metadata.create_all(eng, tables=tables)
    yield eng
    eng.dispose()


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@pytest.fixture
def db(session_factory):
    s = session_factory()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture
def client(session_factory):
    def override_get_db():
        s = session_factory()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
