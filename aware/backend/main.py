"""Entrypoint for running the FastAPI telemetry service with uvicorn."""

from __future__ import annotations

import uvicorn

from .app import app


def run() -> None:
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)


if __name__ == "__main__":
    run()
