"""
apps/agent-hub/routers/admin.py

Admin endpoints (role-gated in production via middleware).
Provides data for the Control Plane dashboard and Token Heatmap.
"""

import time
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from queue.bullmq_client import queue_client

router = APIRouter()


class AgentHealthSummary(BaseModel):
    source: str
    total_jobs: int
    completed: int
    failed: int
    hitl_pending: int
    success_rate: float
    avg_tokens: float
    avg_iterations: float


class HeatmapEntry(BaseModel):
    source: str
    total_tokens: int
    pct_of_total: float
    job_count: int


class TokenBurnSummary(BaseModel):
    total_tokens_24h: int
    heatmap: list[HeatmapEntry]


@router.get("/health", response_model=list[AgentHealthSummary])
async def agent_health():
    """
    Returns per-source health metrics for the Admin Control Plane table.
    """
    jobs = await queue_client.admin_all_jobs(limit=500)

    # Group by source
    groups: dict[str, list] = {}
    for job in jobs:
        groups.setdefault(job.source, []).append(job)

    result = []
    for source, group in groups.items():
        completed  = sum(1 for j in group if j.status == "COMPLETED")
        failed     = sum(1 for j in group if j.status == "FAILED")
        hitl       = sum(1 for j in group if j.status == "HITL_PENDING")
        total      = len(group)
        avg_tokens = sum(j.tokens_used for j in group) / total if total else 0
        avg_iter   = sum(j.iterations  for j in group) / total if total else 0

        result.append(AgentHealthSummary(
            source=source,
            total_jobs=total,
            completed=completed,
            failed=failed,
            hitl_pending=hitl,
            success_rate=round(completed / total, 3) if total else 0.0,
            avg_tokens=round(avg_tokens, 1),
            avg_iterations=round(avg_iter, 2),
        ))
    return result


@router.get("/heatmap", response_model=TokenBurnSummary)
async def token_heatmap(hours: int = Query(default=24, le=168)):
    """
    Token burn heatmap for the admin dashboard.
    Returns total tokens by agent/source for the last N hours.
    """
    cutoff = time.time() - (hours * 3600)
    jobs = await queue_client.admin_all_jobs(limit=500)
    recent = [j for j in jobs if (j.started_at or 0) >= cutoff]

    totals: dict[str, int] = {}
    counts: dict[str, int] = {}
    for job in recent:
        totals[job.source] = totals.get(job.source, 0) + job.tokens_used
        counts[job.source] = counts.get(job.source, 0) + 1

    grand_total = sum(totals.values()) or 1

    heatmap = [
        HeatmapEntry(
            source=src,
            total_tokens=tok,
            pct_of_total=round(tok / grand_total * 100, 1),
            job_count=counts[src],
        )
        for src, tok in sorted(totals.items(), key=lambda x: x[1], reverse=True)
    ]

    return TokenBurnSummary(total_tokens_24h=sum(totals.values()), heatmap=heatmap)


@router.get("/users/{user_id}/quota")
async def user_quota(user_id: str):
    """Fetch token quota + spend for a specific user (admin view)."""
    jobs = await queue_client.list_jobs_for_user(user_id, limit=100)
    total_tokens = sum(j.tokens_used for j in jobs)
    return {
        "user_id": user_id,
        "total_jobs": len(jobs),
        "total_tokens": total_tokens,
        "estimated_usd": round(total_tokens / 1_000_000 * 5.00, 4),  # ~$5/M tokens
    }
