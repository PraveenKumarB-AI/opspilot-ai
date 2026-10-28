"""Production entry point: one service that serves the API under /api and the built React app.

In development, Vite serves the UI and proxies /api to api.main. In production there is no Vite,
so this wraps the same API app and serves frontend/dist from the same origin. api/main.py is unchanged.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.main import app as api_app

DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

app = FastAPI(title="OpsPilot AI", docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/api", api_app)  # /api/health, /api/requests, ... and the API docs at /api/docs

if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str) -> FileResponse:
        """Serve real files (favicon etc.); send every other path to index.html so React Router
        can handle deep links like /queue/3 after a page refresh."""
        file = (DIST / path).resolve()
        if path and file.is_file() and DIST.resolve() in file.parents:
            return FileResponse(file)
        return FileResponse(DIST / "index.html")
