"""
apps/agent-hub/queue/bullmq_client.py

BullMQ-compatible task queue using Redis.
Provides a thin Python wrapper around Redis streams / sorted sets
that mirrors the BullMQ job lifecycle used by the Next.js admin UI.
"""

import os
import json
import uuid
import time
import logging
import asyncio
from dataclasses import dataclass, asdict
from typing import Optional, Literal
import redis.asyncio as aioredis

logger = logging.getLogger("continuum.queue")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
QUEUE_NAME = "harvest-jobs"

JobStatus = Literal["QUEUED", "RUNNING", "COMPLETED", "FAILED", "HITL_PENDING"]


@dataclass
class HarvestJobPayload:
    user_id: str
    source: str          # 'github' | 'gmail' | 'youtube'
    job_id: str = ""
    status: JobStatus = "QUEUED"
    created_at: float = 0.0
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    tokens_used: int = 0
    iterations: int = 0
    error_msg: Optional[str] = None

    def __post_init__(self):
        if not self.job_id:
            self.job_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = time.time()


class BullMQClient:
    """
    Async Redis-backed job queue mirroring BullMQ semantics.
    Jobs are stored as Redis hashes keyed by job_id.
    The queue is a Redis list (LPUSH / BRPOP pattern).
    """

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        self._redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
        logger.info("BullMQ client connected to Redis: %s", REDIS_URL)

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()

    async def enqueue(self, user_id: str, source: str) -> HarvestJobPayload:
        """Add a new harvest job to the queue."""
        job = HarvestJobPayload(user_id=user_id, source=source)
        job_key = f"job:{job.job_id}"

        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.hset(job_key, mapping={k: json.dumps(v) for k, v in asdict(job).items()})
            pipe.lpush(QUEUE_NAME, job.job_id)
            pipe.expire(job_key, 86400 * 7)  # 7-day TTL
            await pipe.execute()

        logger.info("Enqueued job %s [user=%s source=%s]", job.job_id, user_id, source)
        return job

    async def get_job(self, job_id: str) -> Optional[HarvestJobPayload]:
        """Fetch job state from Redis."""
        data = await self._redis.hgetall(f"job:{job_id}")
        if not data:
            return None
        decoded = {k: json.loads(v) for k, v in data.items()}
        return HarvestJobPayload(**decoded)

    async def update_job(self, job_id: str, **kwargs) -> None:
        """Update job fields atomically."""
        job_key = f"job:{job_id}"
        updates = {k: json.dumps(v) for k, v in kwargs.items()}
        await self._redis.hset(job_key, mapping=updates)

    async def mark_running(self, job_id: str) -> None:
        await self.update_job(job_id, status="RUNNING", started_at=time.time())

    async def mark_completed(self, job_id: str, tokens: int, iterations: int) -> None:
        await self.update_job(
            job_id, status="COMPLETED",
            finished_at=time.time(),
            tokens_used=tokens,
            iterations=iterations,
        )

    async def mark_failed(self, job_id: str, error: str) -> None:
        await self.update_job(
            job_id, status="FAILED",
            finished_at=time.time(), error_msg=error,
        )

    async def mark_hitl(self, job_id: str) -> None:
        await self.update_job(job_id, status="HITL_PENDING")

    async def list_jobs_for_user(self, user_id: str, limit: int = 20) -> list[HarvestJobPayload]:
        """Scan recent jobs for a user (admin use)."""
        # In production, maintain a sorted set per user for O(log N) lookup
        keys = await self._redis.keys(f"job:*")
        jobs = []
        for key in keys[:100]:  # cap scan at 100
            data = await self._redis.hgetall(key)
            if data and json.loads(data.get("user_id", '""')) == user_id:
                decoded = {k: json.loads(v) for k, v in data.items()}
                jobs.append(HarvestJobPayload(**decoded))
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]

    async def admin_all_jobs(self, limit: int = 100) -> list[HarvestJobPayload]:
        """Admin: fetch all recent jobs (for heatmap + health table)."""
        keys = await self._redis.keys("job:*")
        jobs = []
        for key in keys[:limit]:
            data = await self._redis.hgetall(key)
            if data:
                decoded = {k: json.loads(v) for k, v in data.items()}
                try:
                    jobs.append(HarvestJobPayload(**decoded))
                except TypeError:
                    pass
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs


# ── Worker (runs in background task) ─────────────────────────────────────────

async def run_worker(client: BullMQClient) -> None:
    """
    Blocking worker loop — pops jobs from queue and runs the harvester.
    Run this as an asyncio background task or separate process.
    """
    from agents.harvester import run_harvester

    logger.info("BullMQ worker started, listening on queue: %s", QUEUE_NAME)
    while True:
        try:
            # BRPOP blocks up to 5s waiting for a job
            result = await client._redis.brpop(QUEUE_NAME, timeout=5)
            if not result:
                continue

            _, job_id = result
            job = await client.get_job(job_id)
            if not job:
                continue

            logger.info("Processing job %s [source=%s]", job_id, job.source)
            await client.mark_running(job_id)

            final_state = await run_harvester(
                user_id=job.user_id,
                source=job.source,
                job_id=job_id,
            )

            if final_state["status"] == "completed":
                await client.mark_completed(
                    job_id,
                    tokens=final_state["tokens_used"],
                    iterations=final_state["iteration"],
                )
            elif final_state["status"] == "hitl":
                await client.mark_hitl(job_id)
            else:
                await client.mark_failed(
                    job_id, final_state.get("error", "Unknown error")
                )

        except asyncio.CancelledError:
            logger.info("Worker cancelled, shutting down.")
            break
        except Exception as exc:
            logger.exception("Worker error: %s", exc)
            await asyncio.sleep(1)


# ── Singleton ─────────────────────────────────────────────────────────────────

queue_client = BullMQClient()
