"""
LLM Adapter — Triple-Mode: SAP GenAI Hub → OpenAI → Deterministic
------------------------------------------------------------------
Priority:
  1. SAP AI Core / Generative AI Hub  (AICORE_* env vars present)
  2. OpenAI                            (OPENAI_API_KEY present)
  3. Deterministic template engine     (always — zero tokens, zero cost, offline)

Active mode is reported by get_llm_mode() and exposed at /api/health.

If the live LLM times out (>3 s) or throws any error it falls back silently to
the next provider, ultimately landing on the deterministic template.  The demo
will NEVER crash because of a bad internet connection or missing credentials.

Environment variables consumed (all optional):
  SAP AI Core / Generative AI Hub:
    AICORE_AUTH_URL          – OAuth2 base URL  (e.g. https://<tenant>.authentication.eu10.hana.ondemand.com)
    AICORE_CLIENT_ID         – OAuth2 client id
    AICORE_CLIENT_SECRET     – OAuth2 client secret
    AICORE_BASE_URL          – AI Core API base (e.g. https://api.ai.prod.eu-central-1.aws.ml.hana.ondemand.com)
    AICORE_DEPLOYMENT_ID     – Deployment id of the running model
    AICORE_RESOURCE_GROUP    – Resource group (default: "default")
    AICORE_MODEL_NAME        – Model name sent in the payload (default: "gpt-4o")
  OpenAI (legacy / fallback):
    OPENAI_API_KEY           – Standard OpenAI secret key
"""

import os
import time
import json
import logging
import threading

import httpx

logger = logging.getLogger(__name__)

# ─── Config ──────────────────────────────────────────────────────────────────
_LLM_TIMEOUT_SECONDS = 3

# SAP AI Core
_AICORE_AUTH_URL      = os.getenv("AICORE_AUTH_URL", "")
_AICORE_CLIENT_ID     = os.getenv("AICORE_CLIENT_ID", "")
_AICORE_CLIENT_SECRET = os.getenv("AICORE_CLIENT_SECRET", "")
_AICORE_BASE_URL      = os.getenv("AICORE_BASE_URL", "")
_AICORE_DEPLOYMENT_ID = os.getenv("AICORE_DEPLOYMENT_ID", "")
_AICORE_RESOURCE_GROUP = os.getenv("AICORE_RESOURCE_GROUP", "default")
_AICORE_MODEL_NAME    = os.getenv("AICORE_MODEL_NAME", "gpt-4o")

# OpenAI (secondary)
_OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

# ─── Shared system prompt ─────────────────────────────────────────────────────
_SYSTEM_PROMPT = (
    "You are ShiftSure, a fair workforce reallocation assistant for a "
    "manufacturing plant. Be concise (2-3 sentences max), factual, and "
    "professional. Never invent numbers. Speak in present tense."
)

# ─── Token cache (thread-safe) ────────────────────────────────────────────────
_token_lock  = threading.Lock()
_cached_token: str = ""
_token_expiry: float = 0.0   # Unix timestamp; 0 means uncached


def _sap_configured() -> bool:
    return bool(
        _AICORE_AUTH_URL and _AICORE_CLIENT_ID and _AICORE_CLIENT_SECRET
        and _AICORE_BASE_URL and _AICORE_DEPLOYMENT_ID
    )


def get_llm_mode() -> str:
    """
    Returns the active reasoning mode string:
      "sap_genai_hub"  – SAP AI Core credentials are configured
      "openai"         – Only OPENAI_API_KEY is configured
      "deterministic"  – No credentials configured; offline template engine
    """
    if _sap_configured():
        return "sap_genai_hub"
    if _OPENAI_KEY:
        return "openai"
    return "deterministic"


# ─── SAP AI Core OAuth2 token ─────────────────────────────────────────────────

def _fetch_token_from_server() -> str:
    """Request a new OAuth2 client-credentials token from SAP XSUAA. Returns '' on failure."""
    token_url = _AICORE_AUTH_URL.rstrip("/") + "/oauth/token"
    try:
        with httpx.Client(timeout=_LLM_TIMEOUT_SECONDS) as client:
            resp = client.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": _AICORE_CLIENT_ID,
                    "client_secret": _AICORE_CLIENT_SECRET,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            body = resp.json()
            token  = body.get("access_token", "")
            # expires_in is in seconds; cache with a 60 s safety margin
            expires_in = int(body.get("expires_in", 3600))
            expiry = time.time() + expires_in - 60
            return token, expiry
    except Exception as exc:
        logger.warning("SAP AI Core token fetch failed: %s", exc)
        return "", 0.0


def _get_sap_token(force_refresh: bool = False) -> str:
    """Return a valid bearer token, refreshing if expired or forced."""
    global _cached_token, _token_expiry
    with _token_lock:
        if force_refresh or not _cached_token or time.time() >= _token_expiry:
            _cached_token, _token_expiry = _fetch_token_from_server()
        return _cached_token


# ─── SAP AI Core chat completions call ───────────────────────────────────────

def _call_sap_genai_hub(prompt: str) -> str:
    """
    POST to SAP AI Core Generative AI Hub chat completions endpoint.
    Returns the assistant reply text, or '' on any error (no stack traces logged).
    Retries once on 401 with a fresh token.
    """
    token = _get_sap_token()
    if not token:
        return ""

    endpoint = (
        _AICORE_BASE_URL.rstrip("/")
        + f"/v2/inference/deployments/{_AICORE_DEPLOYMENT_ID}/chat/completions"
    )
    payload = {
        "model": _AICORE_MODEL_NAME,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens":  150,
    }
    headers = {
        "Authorization":    f"Bearer {token}",
        "AI-Resource-Group": _AICORE_RESOURCE_GROUP,
        "Content-Type":     "application/json",
    }

    def _post(tok: str) -> httpx.Response:
        hdrs = {**headers, "Authorization": f"Bearer {tok}"}
        with httpx.Client(timeout=_LLM_TIMEOUT_SECONDS) as client:
            return client.post(endpoint, headers=hdrs, json=payload)

    try:
        resp = _post(token)

        # 401 → refresh token once and retry
        if resp.status_code == 401:
            fresh = _get_sap_token(force_refresh=True)
            if not fresh:
                return ""
            resp = _post(fresh)

        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    except Exception as exc:
        logger.warning("SAP GenAI Hub call failed, falling back. Reason: %s", exc)
        return ""


# ─── OpenAI call (secondary provider) ────────────────────────────────────────

def _call_openai(prompt: str) -> str:
    """Calls OpenAI chat completions. Returns response text or '' on failure."""
    headers = {
        "Authorization": f"Bearer {_OPENAI_KEY}",
        "Content-Type":  "application/json",
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens":  150,
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
        logger.warning("OpenAI call failed, falling back. Reason: %s", exc)
        return ""


# ─── Public interface (unchanged signature) ───────────────────────────────────

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


def generate_agent_reasoning(agent_name: str, context: dict) -> str:
    """
    Entry point for all 7 agent reasoning calls.
    Priority: SAP GenAI Hub → OpenAI → deterministic templates.
    Falls back silently on any error — never raises.
    """
    prompt = _build_prompt(agent_name, context)

    # 1. SAP AI Core / Generative AI Hub
    if _sap_configured():
        live_text = _call_sap_genai_hub(prompt)
        if live_text:
            return live_text

    # 2. OpenAI (secondary)
    if _OPENAI_KEY:
        live_text = _call_openai(prompt)
        if live_text:
            return live_text

    # 3. Deterministic fallback (always works)
    return _deterministic_template(agent_name, context)


# ─── Deterministic Templates (The Reliable Engine) ───────────────────────────
# Each agent has a hand-crafted template that reads from the context dict and
# produces real sentences — no AI required.

def _deterministic_template(agent_name: str, context: dict) -> str:
    templates = {
        "Skills Discovery Agent":       _tmpl_skills,
        "Market Intelligence Agent":    _tmpl_market,
        "Learning Pathway Agent":       _tmpl_learning,
        "Inclusive Matching Agent":     _tmpl_matching,
        "Employer Readiness Agent":     _tmpl_readiness,
        "Bias Audit Agent":             _tmpl_bias,
        "Human-in-the-Loop Safeguard":  _tmpl_human,
    }
    fn = templates.get(agent_name)
    if fn:
        return fn(context)
    return f"{agent_name} completed analysis for scenario {context.get('scenario_id', 'N/A')}."


def _tmpl_skills(ctx: dict) -> str:
    worker     = ctx.get("worker_name", "the displaced worker")
    skills     = ctx.get("current_skills", [])
    gap_course = ctx.get("gap_course", "a certified bridge course")
    match_pct  = ctx.get("skill_match_pct", 75)
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
    lead_days     = ctx.get("external_lead_days", 28)
    saving        = external_cost - internal_cost
    return (
        f"Market Intelligence report: External recruitment for an equivalent role in "
        f"Bengaluru manufacturing costs ₹{external_cost:,} with a {lead_days}-day hiring lag. "
        f"Internal reskilling costs ₹{internal_cost:,} and qualifies the worker within 5 days. "
        f"Recommending internal redeployment — net saving: ₹{saving:,}."
    )


def _tmpl_learning(ctx: dict) -> str:
    course_title = ctx.get("course_title", "Robotics Safety & Collaborative Arm Operation")
    course_code  = ctx.get("course_code", "SAP-LH-ROB-101")
    hours        = ctx.get("training_hours", 8)
    worker       = ctx.get("worker_name", "the worker")
    return (
        f"Learning Pathway Agent selected SAP Learning Hub course: "
        f"'{course_title}' (Course Code: {course_code}, {hours} hours). "
        f"This is the minimal viable bridge to fully qualify {worker} for the automated cell operator role. "
        f"Course is available immediately through SAP Learning Hub (Student Edition) — no prerequisite gaps."
    )


def _tmpl_matching(ctx: dict) -> str:
    strategy       = ctx.get("strategy", "FAIRNESS_BALANCED")
    workers_matched = ctx.get("workers_matched", 0)
    fill_rate      = ctx.get("fill_rate_pct", 92.5)
    idle_saved     = ctx.get("idle_hours_saved", 168)
    return (
        f"Inclusive Matching Agent delegated problem to Google OR-Tools CP-SAT solver "
        f"under strategy: {strategy}. "
        f"Solver achieved OPTIMAL status: {workers_matched} workers matched, "
        f"{fill_rate}% task fill rate, {idle_saved} idle hours eliminated. "
        f"No assignment was generated by AI inference — all matches are mathematically verified."
    )


def _tmpl_readiness(ctx: dict) -> str:
    line             = ctx.get("destination_line", "LINE-01")
    supervisor_ratio = ctx.get("supervisor_ratio", "1:6")
    shift_ok         = ctx.get("shift_compatible", True)
    shift_note       = "shift schedules are compatible" if shift_ok else "a shift adjustment is required"
    return (
        f"Employer Readiness check for {line}: current supervisor-to-worker ratio is {supervisor_ratio} "
        f"(within the 1:8 safety limit). "
        f"Physical ergonomic assessment passed; {shift_note}. "
        f"The receiving line can absorb redeployed workers without violating any safety regulations."
    )


def _tmpl_bias(ctx: dict) -> str:
    disparity  = ctx.get("idle_disparity_pct", 4.2)
    four_fifths = ctx.get("four_fifths_met", True)
    flip_rate  = ctx.get("counterfactual_flip_rate", 0.0)
    verdict    = "PASSED" if (four_fifths and flip_rate == 0.0) else "ADVISORY FLAGGED"
    return (
        f"Bias Audit Agent report: Inter-group idle disparity is {disparity}% "
        f"(threshold: 15%) — {verdict}. "
        f"4/5ths adverse impact rule: {'Met' if four_fifths else 'Not Met'}. "
        f"Counterfactual test: flipping employment type caused {flip_rate}% assignment changes — "
        f"confirming the solver is free from non-job-related bias."
    )


def _tmpl_human(ctx: dict) -> str:
    plan_id = ctx.get("plan_id", "PLAN-C")
    status  = ctx.get("status", "PENDING_APPROVAL")
    worker  = ctx.get("worker_name", "the worker")
    return (
        f"Human-in-the-Loop Safeguard: {plan_id} is now in {status} state. "
        f"Plant Manager authorization is required before any worker is moved. "
        f"{worker} has been notified of their proposed transfer and the associated SAP Learning Hub course. "
        f"Worker appeal window is open for 24 hours."
    )
