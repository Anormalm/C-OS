from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse


def create_web_router() -> APIRouter:
    router = APIRouter(include_in_schema=False)
    static_dir = Path(__file__).resolve().parent / "static"

    @router.get("/")
    def home() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    return router
