"""
apps/agent-hub/routers/rewind.py

POST /rewind/{job_id}  — Rewinds a synthesised insight to a given checkpoint.
GET  /rewind/{job_id}/history  — Lists available checkpoints for a job.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from agents.harvester import rewind_to_checkpoint, _graph

router = APIRouter()


class RewindRequest(BaseModel):
    checkpoint_id: str


class CheckpointSummary(BaseModel):
    checkpoint_id: str
    node_reached: str
    confidence: Optional[float]
    iteration: int
    status: str


@router.post("/{job_id}")
async def rewind_job(job_id: str, body: RewindRequest):
    """
    Restore a harvest job to a previous checkpoint.
    The rewound state is returned so the frontend can display
    what the agent believed at that point in time.
    """
    state = await rewind_to_checkpoint(job_id, body.checkpoint_id)
    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"Checkpoint {body.checkpoint_id} not found for job {job_id}",
        )
    # Sanitise: strip token_map before returning to client
    safe_state = {k: v for k, v in state.items() if k != "token_map"}
    return {"job_id": job_id, "checkpoint_id": body.checkpoint_id, "state": safe_state}


@router.get("/{job_id}/history", response_model=list[CheckpointSummary])
async def get_checkpoint_history(job_id: str):
    """
    List all available checkpoints for a job (for the Rewind UI).
    """
    config = {"configurable": {"thread_id": job_id}}
    history = list(_graph.get_state_history(config))

    result = []
    for snapshot in history:
        values = snapshot.values
        checkpoint_id = snapshot.config["configurable"].get("checkpoint_id", "")
        result.append(CheckpointSummary(
            checkpoint_id=checkpoint_id,
            node_reached=values.get("status", "unknown"),
            confidence=values.get("confidence"),
            iteration=values.get("iteration", 0),
            status=values.get("status", "unknown"),
        ))
    return result
