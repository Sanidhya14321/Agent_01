"""
apps/agent-hub/agents/harvester.py

Self-Correcting Harvester — LangGraph state machine with:
  • Recursion limit (max_iterations=5)
  • Purification Node (tool-output validation + PII scrubbing)
  • Confidence scoring + HITL routing
  • MemorySaver checkpointer (Rewind support)
  • Exponential back-off retries on rate limits
"""

from __future__ import annotations

import os
import json
import time
import hashlib
import asyncio
import logging
from typing import TypedDict, Annotated, Optional, Literal
from datetime import datetime

# LangGraph
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import GraphRecursionError

# LangChain
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Internal packages
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../packages"))
from security.src.pii_masker import mask_text, check_safe
from observability.src.tracer import (
    tracer, record_tokens, record_iterations,
    record_tool_error, record_hitl,
)

logger = logging.getLogger("continuum.harvester")

MAX_ITERATIONS: int = int(os.getenv("AGENT_MAX_ITERATIONS", "5"))
CONFIDENCE_THRESHOLD: float = float(os.getenv("AGENT_CONFIDENCE_THRESHOLD", "0.7"))
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

# ── State Schema ──────────────────────────────────────────────────────────────

class HarvesterState(TypedDict):
    user_id: str
    source: str                        # 'github' | 'gmail' | 'youtube'
    raw_tool_output: Optional[str]
    masked_text: Optional[str]
    token_map: dict                    # server-side only, never to LLM
    synthesis: Optional[str]
    confidence: float
    iteration: int
    error: Optional[str]
    status: str                        # 'running'|'completed'|'failed'|'hitl'
    checkpoint_id: Optional[str]
    pii_entities_found: list[str]
    tokens_used: int


# ── Tool Stubs (replaced with real API calls via Connection Hub) ──────────────

async def _call_github_api(user_id: str) -> str:
    """Fetch recent GitHub repo metadata for user."""
    # TODO: use stored OAuth token from UserPermissions
    return json.dumps({
        "repos": [
            {"name": "my-saas", "language": "TypeScript", "stars": 42,
             "last_commit": "2026-02-28", "description": "My SaaS product"},
            {"name": "ml-experiments", "language": "Python", "stars": 8,
             "last_commit": "2026-03-01", "description": "ML research"},
        ]
    })


async def _call_gmail_api(user_id: str) -> str:
    """Fetch Gmail message metadata (subjects + senders only — no body)."""
    return json.dumps({
        "messages": [
            {"subject": "Receipt from AWS - $24.50", "from": "billing@aws.amazon.com",
             "date": "2026-02-28"},
            {"subject": "Your GitHub Copilot invoice", "from": "noreply@github.com",
             "date": "2026-03-01"},
        ]
    })


async def _call_youtube_api(user_id: str) -> str:
    """Fetch YouTube watch history titles."""
    return json.dumps({
        "liked_videos": [
            {"title": "Building RAG with LangGraph", "channel": "AI Jason"},
            {"title": "Supabase Full-Stack Deep Dive", "channel": "Supabase"},
        ]
    })


_TOOL_MAP = {
    "github": _call_github_api,
    "gmail": _call_gmail_api,
    "youtube": _call_youtube_api,
}

RATE_LIMIT_ERRORS = {"rate_limit_exceeded", "429", "RateLimitError"}


# ── Node 1: Ingest ────────────────────────────────────────────────────────────

async def ingest_node(state: HarvesterState) -> dict:
    """
    Calls the appropriate platform API tool.
    Implements exponential back-off (3 attempts) on rate limits.
    """
    with tracer.start_as_current_span("agent.ingest") as span:
        span.set_attribute("source", state["source"])
        span.set_attribute("user_id", state["user_id"])
        span.set_attribute("iteration", state["iteration"])

        tool_fn = _TOOL_MAP.get(state["source"])
        if not tool_fn:
            return {"error": f"Unknown source: {state['source']}", "status": "failed"}

        max_retries = 3
        for attempt in range(max_retries):
            try:
                raw = await tool_fn(state["user_id"])
                logger.info("Ingest OK [source=%s user=%s]", state["source"], state["user_id"])
                return {
                    "raw_tool_output": raw,
                    "error": None,
                    "iteration": state["iteration"] + 1,
                }
            except Exception as exc:
                err_str = str(exc)
                is_rate_limit = any(e in err_str for e in RATE_LIMIT_ERRORS)
                if is_rate_limit and attempt < max_retries - 1:
                    wait_secs = 2 ** attempt      # 1, 2, 4 seconds
                    logger.warning("Rate limit hit, retrying in %ds …", wait_secs)
                    record_tool_error(state["source"], "rate_limit")
                    await asyncio.sleep(wait_secs)
                else:
                    record_tool_error(state["source"], type(exc).__name__)
                    span.record_exception(exc)
                    return {"error": err_str, "status": "failed"}

        return {"error": "Max retries exceeded", "status": "failed"}


# ── Node 2: Purification ──────────────────────────────────────────────────────

async def purification_node(state: HarvesterState) -> dict:
    """
    Validates tool output and scrubs PII before any LLM call.
    Blocks processing if:
      • Tool returned an error string
      • Output contains residual sensitive PII after masking

    Returns masked_text + token_map (token_map stays server-side).
    """
    with tracer.start_as_current_span("agent.purify") as span:
        raw = state.get("raw_tool_output", "")

        # 1. Error check
        if not raw or state.get("error"):
            return {"status": "failed", "error": state.get("error", "Empty tool output")}

        # 2. PII masking
        mask_result = mask_text(raw, reversible=True)
        span.set_attribute("pii_entities", str(mask_result.entities_found))

        if mask_result.entities_found:
            logger.info("PII masked [types=%s]", mask_result.entities_found)
            record_tool_error("purification", f"pii:{','.join(mask_result.entities_found)}")

        # 3. Post-masking safety check
        is_safe, residual = check_safe(mask_result.masked_text)
        if not is_safe:
            logger.error("Residual PII after masking: %s — blocking", residual)
            return {
                "status": "failed",
                "error": f"Residual PII detected post-masking: {residual}",
            }

        return {
            "masked_text": mask_result.masked_text,
            "token_map": mask_result.token_map,
            "pii_entities_found": mask_result.entities_found,
        }


# ── Node 3: Synthesiser ───────────────────────────────────────────────────────

async def synthesiser_node(state: HarvesterState) -> dict:
    """
    Sends masked text to GPT-4o for synthesis.
    Extracts a confidence score from the JSON response.
    """
    with tracer.start_as_current_span("agent.synthesise") as span:
        llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0.2, max_tokens=1024)

        system_prompt = """You are Continuum's Knowledge Synthesiser.
Given structured data from a user's digital integrations, produce:
1. A concise insight title (≤12 words)
2. A 2-3 sentence synthesis
3. Tags (3-5 keywords)
4. A confidence score (0.0–1.0) reflecting how certain you are about the insight.

Respond ONLY in valid JSON with this schema:
{
  "title": "string",
  "synthesis": "string",
  "tags": ["string"],
  "confidence": float
}"""

        user_msg = f"Data source: {state['source']}\n\nData:\n{state['masked_text']}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_msg),
        ]

        try:
            response = await llm.ainvoke(messages)
            content = response.content
            tokens = response.usage_metadata.get("total_tokens", 0) if response.usage_metadata else 0

            record_tokens(tokens, "synthesiser", state["user_id"])

            parsed = json.loads(content)
            confidence = float(parsed.get("confidence", 0.0))
            synthesis = json.dumps(parsed)

            span.set_attribute("confidence", confidence)
            span.set_attribute("tokens_used", tokens)

            return {
                "synthesis": synthesis,
                "confidence": confidence,
                "tokens_used": state.get("tokens_used", 0) + tokens,
            }

        except json.JSONDecodeError as exc:
            logger.error("LLM returned non-JSON: %s", exc)
            return {"confidence": 0.0, "error": "LLM response parse error"}
        except Exception as exc:
            logger.error("Synthesiser error: %s", exc)
            span.record_exception(exc)
            return {"confidence": 0.0, "error": str(exc)}


# ── Node 4a: HITL Queue ───────────────────────────────────────────────────────

async def hitl_node(state: HarvesterState) -> dict:
    """
    Routes low-confidence results to the human-in-the-loop queue.
    In production, this would enqueue a task in BullMQ / Temporal.
    """
    with tracer.start_as_current_span("agent.hitl") as span:
        record_hitl("synthesiser", f"confidence<{CONFIDENCE_THRESHOLD}")
        span.set_attribute("confidence", state["confidence"])
        logger.warning(
            "HITL escalation [user=%s source=%s confidence=%.2f]",
            state["user_id"], state["source"], state["confidence"],
        )
        # TODO: enqueue to BullMQ HITL queue
        return {"status": "hitl"}


# ── Node 4b: Emit ─────────────────────────────────────────────────────────────

async def emit_node(state: HarvesterState) -> dict:
    """
    Writes the synthesised KnowledgeNode to the user's vector namespace.
    In production, embeds text via OpenAI and upserts to pgvector.
    """
    with tracer.start_as_current_span("agent.emit") as span:
        namespace = f"user_{state['user_id']}"
        span.set_attribute("namespace", namespace)
        span.set_attribute("confidence", state["confidence"])

        # TODO: embed synthesis + upsert to Supabase pgvector
        logger.info(
            "Emitting KnowledgeNode [namespace=%s source=%s]",
            namespace, state["source"],
        )
        record_iterations(state["iteration"], "self_correcting_harvester")
        return {"status": "completed"}


# ── Routing Functions ─────────────────────────────────────────────────────────

def route_after_ingest(state: HarvesterState) -> Literal["purify", "end"]:
    if state.get("error") or state.get("status") == "failed":
        return "end"
    return "purify"


def route_after_purify(state: HarvesterState) -> Literal["synthesise", "end"]:
    if state.get("error") or state.get("status") == "failed":
        return "end"
    return "synthesise"


def route_after_synthesise(state: HarvesterState) -> Literal["emit", "hitl", "end"]:
    if state.get("error"):
        return "end"
    if state["confidence"] < CONFIDENCE_THRESHOLD:
        return "hitl"
    return "emit"


# ── Graph Assembly ────────────────────────────────────────────────────────────

def build_harvester_graph() -> StateGraph:
    """Build and compile the Self-Correcting Harvester LangGraph."""

    builder = StateGraph(HarvesterState)

    # Register nodes
    builder.add_node("ingest",     ingest_node)
    builder.add_node("purify",     purification_node)
    builder.add_node("synthesise", synthesiser_node)
    builder.add_node("hitl",       hitl_node)
    builder.add_node("emit",       emit_node)

    # Entry point
    builder.set_entry_point("ingest")

    # Edges
    builder.add_conditional_edges("ingest",     route_after_ingest,     {"purify": "purify",     "end": END})
    builder.add_conditional_edges("purify",     route_after_purify,     {"synthesise": "synthesise", "end": END})
    builder.add_conditional_edges("synthesise", route_after_synthesise, {"emit": "emit", "hitl": "hitl", "end": END})
    builder.add_edge("hitl", END)
    builder.add_edge("emit", END)

    # Checkpointer for Rewind support
    checkpointer = MemorySaver()

    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=[],    # could add "emit" for human approval before writing
    )


# ── Public API ────────────────────────────────────────────────────────────────

_graph = build_harvester_graph()


async def run_harvester(
    user_id: str,
    source: str,
    job_id: str,
) -> HarvesterState:
    """
    Run the Self-Correcting Harvester for a given user + source.

    Args:
        user_id : Continuum user ID
        source  : 'github' | 'gmail' | 'youtube'
        job_id  : BullMQ job ID (used as thread_id for checkpointing)

    Returns:
        Final HarvesterState after graph execution.

    Raises:
        GraphRecursionError if max_iterations exceeded.
    """
    initial_state: HarvesterState = {
        "user_id": user_id,
        "source": source,
        "raw_tool_output": None,
        "masked_text": None,
        "token_map": {},
        "synthesis": None,
        "confidence": 0.0,
        "iteration": 0,
        "error": None,
        "status": "running",
        "checkpoint_id": None,
        "pii_entities_found": [],
        "tokens_used": 0,
    }

    config = {
        "configurable": {"thread_id": job_id},
        "recursion_limit": MAX_ITERATIONS,
    }

    try:
        final_state = await _graph.ainvoke(initial_state, config=config)
        logger.info(
            "Harvester complete [job=%s status=%s confidence=%.2f tokens=%d]",
            job_id, final_state["status"], final_state["confidence"],
            final_state["tokens_used"],
        )
        return final_state

    except GraphRecursionError:
        logger.error("Recursion limit (%d) exceeded for job %s", MAX_ITERATIONS, job_id)
        return {**initial_state, "status": "failed",
                "error": f"Recursion limit ({MAX_ITERATIONS}) exceeded"}


async def rewind_to_checkpoint(job_id: str, checkpoint_id: str) -> Optional[HarvesterState]:
    """
    Restore a previous LangGraph state for a given job/checkpoint.
    Returns the rewound state or None if checkpoint not found.
    """
    config = {"configurable": {"thread_id": job_id}}
    history = list(_graph.get_state_history(config))
    for snapshot in history:
        if snapshot.config["configurable"].get("checkpoint_id") == checkpoint_id:
            logger.info("Rewinding job %s to checkpoint %s", job_id, checkpoint_id)
            return snapshot.values
    logger.warning("Checkpoint %s not found for job %s", checkpoint_id, job_id)
    return None
