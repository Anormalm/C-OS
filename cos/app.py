from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from cos.configs.settings import get_settings
from cos.ingestion.async_queue import AsyncIngestionQueue
from cos.runtime import COSRuntime
from cos.ui.api import create_router
from cos.ui.web import create_web_router

settings = get_settings()
runtime = COSRuntime(settings)
async_queue = AsyncIngestionQueue(runtime)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await async_queue.start()
    yield
    await async_queue.stop()


app = FastAPI(
    title=settings.app_name,
    description="Cognitive Operating System API",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(create_router(runtime, async_queue))
app.include_router(create_web_router())
app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).resolve().parent / "ui" / "static")),
    name="static",
)
