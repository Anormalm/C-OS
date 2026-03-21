from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from cos.core.models import IngestionRequest
from cos.runtime import COSRuntime


@dataclass
class AsyncIngestionQueue:
    runtime: COSRuntime
    queue: asyncio.Queue[tuple[str, IngestionRequest]] | None = None
    jobs: dict[str, dict[str, Any]] = field(default_factory=dict)
    _worker_task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._worker_task and not self._worker_task.done():
            return
        self.queue = asyncio.Queue()
        self._worker_task = asyncio.create_task(
            self._worker(self.queue),
            name="cos-ingestion-worker",
        )

    async def stop(self) -> None:
        if self._worker_task:
            self._worker_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._worker_task
            self._worker_task = None
        self.queue = None

    async def submit(self, request: IngestionRequest) -> str:
        if self.queue is None:
            self.queue = asyncio.Queue()
        job_id = str(uuid4())
        self.jobs[job_id] = {
            "status": "queued",
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "result": None,
            "error": None,
        }
        await self.queue.put((job_id, request))
        return job_id

    def get(self, job_id: str) -> dict[str, Any] | None:
        return self.jobs.get(job_id)

    async def _worker(self, queue: asyncio.Queue[tuple[str, IngestionRequest]]) -> None:
        while True:
            job_id, request = await queue.get()
            self.jobs[job_id]["status"] = "running"
            try:
                result = await asyncio.to_thread(self.runtime.ingest_text, request)
                self.jobs[job_id]["status"] = "completed"
                self.jobs[job_id]["result"] = result.model_dump(mode="json")
            except Exception as exc:  # pragma: no cover
                self.jobs[job_id]["status"] = "failed"
                self.jobs[job_id]["error"] = str(exc)
            finally:
                self.jobs[job_id]["finished_at"] = datetime.now(timezone.utc).isoformat()
                queue.task_done()
