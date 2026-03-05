"""
apps/agent-hub/routers/harvest.py

POST /harvest  — Enqueues a new Harvesting job for a user.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Literal

from tasks.bullmq_client import queue_client

router = APIRouter()


class HarvestRequest(BaseModel):
    user_id: str = Field(..., description="Continuum user ID")
    source: Literal["github", "gmail", "youtube"] = Field(
        ..., description="Data source to harvest"
    )


class HarvestResponse(BaseModel):
    job_id: str
    status: str
    message: str


@router.post("", response_model=HarvestResponse, status_code=202)
async def trigger_harvest(body: HarvestRequest):
    """
    Enqueue a new harvest job.  Returns immediately with job_id.
    Poll /status/{job_id} for progress.
    """
    try:
        job = await queue_client.enqueue(
            user_id=body.user_id,
            source=body.source,
        )
        return HarvestResponse(
            job_id=job.job_id,
            status=job.status,
            message=f"Harvest job enqueued for {body.source}. "
                    f"Poll /status/{job.job_id} for progress.",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
