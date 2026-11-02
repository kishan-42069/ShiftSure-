"""
Agents API Router
------------------
Exposes the Career Orchestrator pipeline via:
1. Server-Sent Events (SSE) stream at GET /api/agents/stream/{scenario_id}
   → Frontend connects and receives live agent events as they happen.
2. POST /api/agents/run/{scenario_id}
   → Runs the full pipeline synchronously and returns all events as a list.
   → Useful for testing and for the frontend's initial page load.
"""

import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.database import get_db
from app.agents.orchestrator import orchestrate

router = APIRouter(prefix="/api/agents", tags=["agents"])


# ─── 1. Live Server-Sent Events Stream ───────────────────────────────────────

@router.get("/stream/{scenario_id}", summary="Live agent reasoning stream (SSE)")
async def stream_agent_pipeline(scenario_id: str, db: Session = Depends(get_db)):
    """
    Connect to this endpoint to receive live agent events as the Career Orchestrator
    runs the 7-agent pipeline for a given disruption scenario.

    The browser (or EventSource JS client) will receive one JSON event per agent step,
    each looking like:
    {
      "event_type": "AGENT_RESULT",
      "agent": "Skills Discovery Agent",
      "timestamp": "...",
      "data": { ... },
      "reasoning": "..."
    }
    """
    async def event_generator():
        q: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def run_sync():
            try:
                for event in orchestrate(scenario_id=scenario_id, db=db):
                    loop.call_soon_threadsafe(q.put_nowait, event)
                loop.call_soon_threadsafe(q.put_nowait, None)
            except Exception as exc:
                loop.call_soon_threadsafe(q.put_nowait, exc)

        loop.run_in_executor(None, run_sync)

        while True:
            item = await q.get()
            if item is None:
                break
            if isinstance(item, Exception):
                yield {
                    "event": "ORCHESTRATOR_ERROR",
                    "data": json.dumps({"error": str(item)}),
                }
                break
            yield {
                "event": item.get("event_type", "agent_event"),
                "data": json.dumps(item),
            }

    return EventSourceResponse(event_generator())


# ─── 2. Synchronous Run (Returns All Events as JSON List) ─────────────────────

@router.post("/run/{scenario_id}", summary="Run full agent pipeline (synchronous)")
def run_agent_pipeline(scenario_id: str, db: Session = Depends(get_db)):
    """
    Runs the complete 7-agent Career Orchestrator pipeline for the given scenario
    and returns ALL events at once as a JSON array.

    Use this for:
    - Testing without SSE
    - Frontend initial render (show full timeline on page load)
    - Hackathon Q&A demo where you need to skip the live stream
    """
    try:
        events = list(orchestrate(scenario_id=scenario_id, db=db))
        return {
            "scenario_id": scenario_id,
            "total_events": len(events),
            "pipeline_events": events,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {exc}")


# ─── 3. Health Check for Agent Layer ─────────────────────────────────────────

@router.get("/health", summary="Agent layer health check")
def agents_health():
    """Quick check that the agents module is loaded and the LLM adapter is configured."""
    import os
    llm_mode = "LIVE_LLM" if (os.getenv("OPENAI_API_KEY") or os.getenv("SAP_GENAI_HUB_KEY")) else "DETERMINISTIC_OFFLINE"
    return {
        "status": "healthy",
        "agents_ready": 7,
        "llm_mode": llm_mode,
        "note": (
            "Using live LLM with deterministic fallback."
            if llm_mode == "LIVE_LLM"
            else "Running in fully offline deterministic mode. Set OPENAI_API_KEY to enable live LLM."
        ),
    }
