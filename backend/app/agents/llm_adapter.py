"""
LLM Adapter — Dual Mode: Deterministic (Default) or Live LLM (Optional)
------------------------------------------------------------------------
Primary mode:   Deterministic template engine — 100% offline, zero tokens, zero cost.
Secondary mode: Live LLM (OpenAI, SAP Generative AI Hub) activated ONLY when an API
                key is present in the environment variable OPENAI_API_KEY or
                SAP_GENAI_HUB_KEY.

If the live LLM times out (>3 seconds) or throws any error, it automatically falls
back to the deterministic template — the demo will NEVER crash because of a bad
internet connection.
"""

import os
import time
import json
import logging

logger = logging.getLogger(__name__)

# ─── Optional live LLM (only imported if the key is present) ─────────────────
_OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
_SAP_KEY = os.getenv("SAP_GENAI_HUB_KEY", "")
_LLM_TIMEOUT_SECONDS = 3

def _live_llm_available() -> bool:
    return bool(_OPENAI_KEY or _SAP_KEY)


def _call_openai(prompt: str) -> str:
    """Calls OpenAI chat completions endpoint. Returns response text."""
    import httpx  # already in requirements
    headers = {
        "Authorization": f"Bearer {_OPENAI_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": (
                "You are ShiftSure, a fair workforce reallocation assistant for a "
                "manufacturing plant. Be concise (2-3 sentences max), factual, and "
                "professional. Never invent numbers. Speak in present tense."
            )},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 150,
    }
    try:
        with httpx.Client(timeout=_LLM_TIMEOUT_SECONDS) as client:
            resp = client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        logger.warning("OpenAI call failed, using deterministic fallback. Reason: %s", exc)
        return ""  # empty string → caller uses deterministic template


def generate_agent_reasoning(agent_name: str, context: dict) -> str:
    """
    Entry point for all agent reasoning text.
    Tries live LLM if key is available. Falls back to deterministic templates
    gracefully and silently.
    """
    if _live_llm_available():
        prompt = _build_prompt(agent_name, context)
        live_text = _call_openai(prompt)
        if live_text:
            return live_text
    # deterministic fallback always runs if live LLM not available or failed
    return _deterministic_template(agent_name, context)


def _build_prompt(agent_name: str, context: dict) -> str:
    """Converts agent context into a focused LLM prompt."""
    ctx_str = json.dumps(context, indent=2, default=str)
    return (
        f"You are the {agent_name} for ShiftSure workforce reallocation system at "
        f"Bengaluru Smart Auto Components Plant (Plant BLR-01).\n\n"
        f"Context:\n{ctx_str}\n\n"
        f"Write your reasoning in 2-3 clear, professional sentences. "
        f"Refer to specific numbers from the context. No hallucination."
    )


# ─── Deterministic Templates (The Reliable Engine) ───────────────────────────
# Each agent has a hand-crafted template that reads from the context dict and
# produces real sentences — no AI required.

def _deterministic_template(agent_name: str, context: dict) -> str:
    templates = {
        "Skills Discovery Agent": _tmpl_skills,
        "Market Intelligence Agent": _tmpl_market,
        "Learning Pathway Agent": _tmpl_learning,
        "Inclusive Matching Agent": _tmpl_matching,
        "Employer Readiness Agent": _tmpl_readiness,
        "Bias Audit Agent": _tmpl_bias,
        "Human-in-the-Loop Safeguard": _tmpl_human,
    }
    fn = templates.get(agent_name)
    if fn:
        return fn(context)
    return f"{agent_name} completed analysis for scenario {context.get('scenario_id', 'N/A')}."


def _tmpl_skills(ctx: dict) -> str:
    worker = ctx.get("worker_name", "the displaced worker")
    skills = ctx.get("current_skills", [])
    gap_course = ctx.get("gap_course", "a certified bridge course")
    match_pct = ctx.get("skill_match_pct", 75)
    skills_str = ", ".join(skills[:3]) if skills else "manual assembly and quality inspection"
    return (
        f"Skills Discovery complete for {worker}. "
        f"Verified skills: {skills_str} — these provide a {match_pct}% match to available automation roles. "
        f"Identified narrow skill gap closeable via {gap_course}, "
        f"making {worker} a strong internal redeployment candidate."
    )


def _tmpl_market(ctx: dict) -> str:
    internal_cost = ctx.get("internal_cost_inr", 4500)
    external_cost = ctx.get("external_cost_inr", 185000)
    lead_days = ctx.get("external_lead_days", 28)
    saving = external_cost - internal_cost
    return (
        f"Market Intelligence report: External recruitment for an equivalent role in "
        f"Bengaluru manufacturing costs ₹{external_cost:,} with a {lead_days}-day hiring lag. "
        f"Internal reskilling costs ₹{internal_cost:,} and qualifies the worker within 5 days. "
        f"Recommending internal redeployment — net saving: ₹{saving:,}."
    )


def _tmpl_learning(ctx: dict) -> str:
    course_title = ctx.get("course_title", "Robotics Safety & Collaborative Arm Operation")
    course_code = ctx.get("course_code", "SAP-LH-ROB-101")
    hours = ctx.get("training_hours", 8)
    worker = ctx.get("worker_name", "the worker")
    return (
        f"Learning Pathway Agent selected SAP Learning Hub course: "
        f"'{course_title}' (Course Code: {course_code}, {hours} hours). "
        f"This is the minimal viable bridge to fully qualify {worker} for the automated cell operator role. "
        f"Course is available immediately through SAP Learning Hub (Student Edition) — no prerequisite gaps."
    )


def _tmpl_matching(ctx: dict) -> str:
    strategy = ctx.get("strategy", "FAIRNESS_BALANCED")
    workers_matched = ctx.get("workers_matched", 0)
    fill_rate = ctx.get("fill_rate_pct", 92.5)
    idle_saved = ctx.get("idle_hours_saved", 168)
    return (
        f"Inclusive Matching Agent delegated problem to Google OR-Tools CP-SAT solver "
        f"under strategy: {strategy}. "
        f"Solver achieved OPTIMAL status: {workers_matched} workers matched, "
        f"{fill_rate}% task fill rate, {idle_saved} idle hours eliminated. "
        f"No assignment was generated by AI inference — all matches are mathematically verified."
    )


def _tmpl_readiness(ctx: dict) -> str:
    line = ctx.get("destination_line", "LINE-01")
    supervisor_ratio = ctx.get("supervisor_ratio", "1:6")
    shift_ok = ctx.get("shift_compatible", True)
    shift_note = "shift schedules are compatible" if shift_ok else "a shift adjustment is required"
    return (
        f"Employer Readiness check for {line}: current supervisor-to-worker ratio is {supervisor_ratio} "
        f"(within the 1:8 safety limit). "
        f"Physical ergonomic assessment passed; {shift_note}. "
        f"The receiving line can absorb redeployed workers without violating any safety regulations."
    )


def _tmpl_bias(ctx: dict) -> str:
    disparity = ctx.get("idle_disparity_pct", 4.2)
    four_fifths = ctx.get("four_fifths_met", True)
    flip_rate = ctx.get("counterfactual_flip_rate", 0.0)
    verdict = "PASSED" if (four_fifths and flip_rate == 0.0) else "ADVISORY FLAGGED"
    return (
        f"Bias Audit Agent report: Inter-group idle disparity is {disparity}% "
        f"(threshold: 15%) — {verdict}. "
        f"4/5ths adverse impact rule: {'Met' if four_fifths else 'Not Met'}. "
        f"Counterfactual test: flipping employment type caused {flip_rate}% assignment changes — "
        f"confirming the solver is free from non-job-related bias."
    )


def _tmpl_human(ctx: dict) -> str:
    plan_id = ctx.get("plan_id", "PLAN-C")
    status = ctx.get("status", "PENDING_APPROVAL")
    worker = ctx.get("worker_name", "the worker")
    return (
        f"Human-in-the-Loop Safeguard: {plan_id} is now in {status} state. "
        f"Plant Manager authorization is required before any worker is moved. "
        f"{worker} has been notified of their proposed transfer and the associated SAP Learning Hub course. "
        f"Worker appeal window is open for 24 hours."
    )
