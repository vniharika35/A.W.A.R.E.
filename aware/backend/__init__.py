"""Backend package exposing FastAPI app and database helpers."""

from __future__ import annotations

from .app import app
from .db import get_engine
from .db import get_session
from .db import session_scope


__all__ = ["app", "get_engine", "get_session", "session_scope"]
