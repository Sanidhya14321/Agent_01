"""
apps/agent-hub/main.py

Continuum Agent Hub — FastAPI application entrypoint.
Mounts all routers and manages BullMQ worker lifecycle.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import harvest, rewind, status, admin as admin_router
from tasks.bullmq_client import queue_client, run_worker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("continuum.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    await queue_client.connect()
    worker_task = asyncio.create_task(run_worker(queue_client))
    logger.info("Agent Hub started ✓")
    yield
    # ── Shutdown ──────────────────────────────────────────────────────────────
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
    await queue_client.close()
    logger.info("Agent Hub shut down ✓")


app = FastAPI(
    title="Continuum Agent Hub",
    version="1.0.0",
    description="Self-Correcting Harvester API — the autonomous knowledge engine behind Continuum.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(harvest.router,       prefix="/harvest",  tags=["Harvest"])
app.include_router(rewind.router,        prefix="/rewind",   tags=["Rewind"])
app.include_router(status.router,        prefix="/status",   tags=["Status"])
app.include_router(admin_router.router,  prefix="/admin",    tags=["Admin"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "continuum-agent-hub"}
