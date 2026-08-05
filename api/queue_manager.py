import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable
from uuid import uuid4


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


Processor = Callable[[Any], Awaitable[dict]]


@dataclass
class AnalysisJob:
    payload: Any
    processor: Processor
    id: str = field(default_factory=lambda: str(uuid4()))
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: dict | None = None
    error: str | None = None


class QueueManager:
    """Fila FIFO em memória, consumida por um único worker assíncrono."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[AnalysisJob] = asyncio.Queue()
        self._jobs: dict[str, AnalysisJob] = {}
        self._pending_order: list[str] = []
        self._current_job_id: str | None = None
        self._worker_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self._total_processed = 0

    async def start(self) -> None:
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._worker())

    async def submit(self, payload: Any, processor: Processor) -> dict:
        await self.start()
        job = AnalysisJob(payload=payload, processor=processor)

        async with self._lock:
            self._jobs[job.id] = job
            self._pending_order.append(job.id)
            position = len(self._pending_order)
            queue_size = len(self._pending_order) + (1 if self._current_job_id else 0)

        await self._queue.put(job)

        return {
            "job_id": job.id,
            "status": job.status.value,
            "position": position,
            "queue_size": queue_size,
        }

    async def get_status(self, job_id: str) -> dict | None:
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None

            position = None
            if job.status == JobStatus.PENDING:
                try:
                    position = self._pending_order.index(job_id) + 1
                except ValueError:
                    position = None
            elif job.status == JobStatus.PROCESSING:
                position = 0

            queue_size = len(self._pending_order) + (1 if self._current_job_id else 0)

            response = {
                "job_id": job.id,
                "status": job.status.value,
                "position": position,
                "queue_size": queue_size,
                "pending_jobs": len(self._pending_order),
                "processing_job": self._current_job_id,
                "total_processed": self._total_processed,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "finished_at": job.finished_at.isoformat() if job.finished_at else None,
            }

            if job.status == JobStatus.COMPLETED:
                response["result"] = job.result
            elif job.status == JobStatus.FAILED:
                response["error"] = job.error

            return response

    async def get_queue_status(self) -> dict:
        async with self._lock:
            return {
                "queue_size": len(self._pending_order) + (1 if self._current_job_id else 0),
                "pending_jobs": len(self._pending_order),
                "processing_job": self._current_job_id,
                "total_processed": self._total_processed,
            }

    async def _worker(self) -> None:
        while True:
            job = await self._queue.get()

            async with self._lock:
                if job.id in self._pending_order:
                    self._pending_order.remove(job.id)
                self._current_job_id = job.id
                job.status = JobStatus.PROCESSING
                job.started_at = datetime.now(timezone.utc)

            try:
                job.result = await job.processor(job.payload)
                job.status = JobStatus.COMPLETED
            except Exception as error:
                job.status = JobStatus.FAILED
                job.error = str(error) or "Erro interno durante o processamento"
            finally:
                async with self._lock:
                    job.finished_at = datetime.now(timezone.utc)
                    self._current_job_id = None
                    self._total_processed += 1
                self._queue.task_done()


queue_manager = QueueManager()
