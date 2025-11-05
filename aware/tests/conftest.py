from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from aware.backend.app import app
from aware.backend.db import get_engine


@pytest.fixture()
def client(tmp_path, monkeypatch) -> Generator[TestClient, None, None]:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    get_engine(force_init=True)
    with TestClient(app) as test_client:
        yield test_client
