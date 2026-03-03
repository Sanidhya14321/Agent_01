"""
apps/agent-hub/routers/status.py

GET /status/{job_id}  — Returns current job status + metrics.
GET /status/stream/{job_id}  — SSE stream of status updates.
"""

import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from queue.bullmq_client import queue_client

router = APIRouter()


class JobStatusResponse(BaseModel):
    job_id: str
    user_id: str
    source: str
    status: str
    tokens_used: int
    iterations: int
    error_msg: Optional[str] = None
    started_at: Optional[float] = None
    finished_at: Optional[float] = None


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_status(job_id: str):
    """Fetch current status of a harvest job."""
    job = await queue_client.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return JobStatusResponse(
        job_id=job.job_id,
        user_id=job.user_id,
        source=job.source,
        status=job.status,
        tokens_used=job.tokens_used,
        iterations=job.iterations,
        error_msg=job.error_msg,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


@router.get("/stream/{job_id}")
async def stream_status(job_id: str):
    """
    Server-Sent Events stream of job status.
    Frontend polls this during harvest to show live progress.
    """
    async def event_generator():
        import json
        while True:
            job = await queue_client.get_job(job_id)
            if not job:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break

            payload = {
                "job_id": job.job_id,
                "status": job.status,
                "tokens_used": job.tokens_used,
                "iterations": job.iterations,
            }
            yield f"data: {json.dumps(payload)}\n\n"

            if job.status in ("COMPLETED", "FAILED", "HITL_PENDING"):
                break
            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
