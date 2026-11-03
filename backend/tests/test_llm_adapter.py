"""
Tests for backend/app/agents/llm_adapter.py

Covers:
  1. No credentials → deterministic output
  2. SAP token success + chat success → live text returned
  3. SAP token failure → deterministic fallback
  4. SAP chat HTTP 500 → deterministic fallback
  5. Token cache expiry triggers a fresh fetch (refresh path)
  6. OpenAI success when only OPENAI_API_KEY is set
  7. get_llm_mode() reports correctly for each configuration

Run with:  cd backend && source venv/bin/activate && pytest -q
"""

import importlib
import time
import json
import pytest
import httpx
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_AGENT_NAME = "Skills Discovery Agent"
_CTX = {
    "worker_name": "Priya S.",
    "current_skills": ["Manual Assembly", "Quality Inspection"],
    "gap_course": "SAP-LH-ROB-101",
    "skill_match_pct": 82,
}

_SAP_ENV = {
    "AICORE_AUTH_URL":       "https://auth.example.com",
    "AICORE_CLIENT_ID":      "client-id",
    "AICORE_CLIENT_SECRET":  "client-secret",
    "AICORE_BASE_URL":       "https://api.ai.example.com",
    "AICORE_DEPLOYMENT_ID":  "dep1",
}


def _reload(monkeypatch, env: dict):
    """Reload llm_adapter with a specific env and reset the token cache."""
    for k in ("AICORE_AUTH_URL", "AICORE_CLIENT_ID", "AICORE_CLIENT_SECRET",
              "AICORE_BASE_URL", "AICORE_DEPLOYMENT_ID", "AICORE_RESOURCE_GROUP",
              "AICORE_MODEL_NAME", "OPENAI_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    import app.agents.llm_adapter as mod
    importlib.reload(mod)
    mod._cached_token = ""
    mod._token_expiry = 0.0
    return mod


def _mock_httpx_post(url_responses: dict):
    """
    Returns a context-manager-compatible mock for httpx.Client whose
    .post() dispatches based on partial URL match.

    url_responses: {partial_url_fragment: httpx.Response}
    """
    class _MockClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def post(self, url, **kwargs):
            for fragment, response in url_responses.items():
                if fragment in url:
                    return response
            raise ValueError(f"No mock configured for URL: {url}")

    return _MockClient


# ---------------------------------------------------------------------------
# 1. No credentials → deterministic
# ---------------------------------------------------------------------------

class TestNoCreds:

    def test_generate_returns_deterministic_when_no_keys(self, monkeypatch):
        mod = _reload(monkeypatch, {})
        result = mod.generate_agent_reasoning(_AGENT_NAME, _CTX)
        assert "Priya S." in result
        assert "82%" in result

    def test_get_llm_mode_deterministic(self, monkeypatch):
        mod = _reload(monkeypatch, {})
        assert mod.get_llm_mode() == "deterministic"


# ---------------------------------------------------------------------------
# 2. SAP token success + chat success → live text returned
# ---------------------------------------------------------------------------

class TestSapSuccess:

    def test_live_text_returned(self, monkeypatch):
        mod = _reload(monkeypatch, _SAP_ENV)

        token_resp = httpx.Response(
            200,
            json={"access_token": "tok-123", "expires_in": 3600},
            request=httpx.Request("POST", "https://auth.example.com/oauth/token"),
        )
        chat_resp = httpx.Response(
            200,
            json={"choices": [{"message": {"content": "SAP GenAI Hub says: all good."}}]},
            request=httpx.Request("POST", "https://api.ai.example.com/chat/completions"),
        )

        MockClient = _mock_httpx_post({"/oauth/token": token_resp, "/chat/completions": chat_resp})
        monkeypatch.setattr(mod.httpx, "Client", MockClient)

        result = mod.generate_agent_reasoning(_AGENT_NAME, _CTX)
        assert result == "SAP GenAI Hub says: all good."

    def test_get_llm_mode_sap(self, monkeypatch):
        mod = _reload(monkeypatch, _SAP_ENV)
        assert mod.get_llm_mode() == "sap_genai_hub"


# ---------------------------------------------------------------------------
# 3. SAP token failure → deterministic
# ---------------------------------------------------------------------------

class TestSapTokenFailure:

    def test_falls_back_when_token_fails(self, monkeypatch):
        mod = _reload(monkeypatch, _SAP_ENV)

        token_resp = httpx.Response(
            401,
            json={"error": "unauthorized"},
            request=httpx.Request("POST", "https://auth.example.com/oauth/token"),
        )
        MockClient = _mock_httpx_post({"/oauth/token": token_resp})
        monkeypatch.setattr(mod.httpx, "Client", MockClient)

        result = mod.generate_agent_reasoning(_AGENT_NAME, _CTX)
        # Should fall through to deterministic (token call raises on raise_for_status)
        assert "Priya S." in result


# ---------------------------------------------------------------------------
# 4. SAP chat HTTP 500 → deterministic
# ---------------------------------------------------------------------------

class TestSapChatError:

    def test_falls_back_on_chat_500(self, monkeypatch):
        mod = _reload(monkeypatch, _SAP_ENV)

        token_resp = httpx.Response(
            200,
            json={"access_token": "tok-abc", "expires_in": 3600},
            request=httpx.Request("POST", "https://auth.example.com/oauth/token"),
        )
        chat_resp = httpx.Response(
            500,
            json={"error": "internal server error"},
            request=httpx.Request("POST", "https://api.ai.example.com/chat/completions"),
        )

        MockClient = _mock_httpx_post({"/oauth/token": token_resp, "/chat/completions": chat_resp})
        monkeypatch.setattr(mod.httpx, "Client", MockClient)

        result = mod.generate_agent_reasoning(_AGENT_NAME, _CTX)
        assert "Priya S." in result


# ---------------------------------------------------------------------------
# 5. Token cache expiry triggers a fresh fetch (refresh path)
# ---------------------------------------------------------------------------

class TestTokenRefresh:

    def test_expired_token_triggers_fresh_fetch(self, monkeypatch):
        mod = _reload(monkeypatch, _SAP_ENV)

        fetch_count = {"n": 0}

        class _CountingClient:
            def __init__(self, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def post(self, url, **kwargs):
                if "/oauth/token" in url:
                    fetch_count["n"] += 1
                    return httpx.Response(
                        200,
                        json={"access_token": f"token-{fetch_count['n']}", "expires_in": 3600},
                        request=httpx.Request("POST", url),
                    )
                raise ValueError("unexpected call")

        monkeypatch.setattr(mod.httpx, "Client", _CountingClient)

        # First call — fetches token
        mod._get_sap_token()
        assert fetch_count["n"] == 1

        # Simulate token expiry
        mod._token_expiry = time.time() - 1

        # Second call — must re-fetch
        mod._get_sap_token()
        assert fetch_count["n"] == 2

    def test_401_on_chat_triggers_token_refresh(self, monkeypatch):
        mod = _reload(monkeypatch, _SAP_ENV)

        token_fetches = {"n": 0}
        chat_attempts = {"n": 0}

        class _RetryClient:
            def __init__(self, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def post(self, url, **kwargs):
                if "/oauth/token" in url:
                    token_fetches["n"] += 1
                    return httpx.Response(
                        200,
                        json={"access_token": f"tok{token_fetches['n']}", "expires_in": 3600},
                        request=httpx.Request("POST", url),
                    )
                chat_attempts["n"] += 1
                if chat_attempts["n"] == 1:
                    return httpx.Response(401, json={"error": "unauthorized"}, request=httpx.Request("POST", url))
                return httpx.Response(
                    200,
                    json={"choices": [{"message": {"content": "retry success"}}]},
                    request=httpx.Request("POST", url),
                )

        monkeypatch.setattr(mod.httpx, "Client", _RetryClient)

        result = mod.generate_agent_reasoning(_AGENT_NAME, _CTX)
        assert result == "retry success"
        assert token_fetches["n"] >= 2  # initial + refresh


# ---------------------------------------------------------------------------
# 6. OpenAI success (only OPENAI_API_KEY set)
# ---------------------------------------------------------------------------

class TestOpenAIFallback:

    def test_openai_used_when_sap_not_configured(self, monkeypatch):
        mod = _reload(monkeypatch, {"OPENAI_API_KEY": "sk-test"})

        openai_resp = httpx.Response(
            200,
            json={"choices": [{"message": {"content": "OpenAI answer here."}}]},
            request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"),
        )
        MockClient = _mock_httpx_post({"openai.com": openai_resp})
        monkeypatch.setattr(mod.httpx, "Client", MockClient)

        result = mod.generate_agent_reasoning(_AGENT_NAME, _CTX)
        assert result == "OpenAI answer here."

    def test_get_llm_mode_openai(self, monkeypatch):
        mod = _reload(monkeypatch, {"OPENAI_API_KEY": "sk-test"})
        assert mod.get_llm_mode() == "openai"

    def test_openai_failure_falls_to_deterministic(self, monkeypatch):
        mod = _reload(monkeypatch, {"OPENAI_API_KEY": "sk-test"})

        error_resp = httpx.Response(
            500,
            json={"error": "server error"},
            request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"),
        )
        MockClient = _mock_httpx_post({"openai.com": error_resp})
        monkeypatch.setattr(mod.httpx, "Client", MockClient)

        result = mod.generate_agent_reasoning(_AGENT_NAME, _CTX)
        assert "Priya S." in result


# ---------------------------------------------------------------------------
# 7. Deterministic template spot-checks
# ---------------------------------------------------------------------------

class TestDeterministicTemplates:

    @pytest.fixture(autouse=True)
    def no_keys(self, monkeypatch):
        self.mod = _reload(monkeypatch, {})

    def test_market_template(self):
        ctx = {"internal_cost_inr": 5000, "external_cost_inr": 200000, "external_lead_days": 30}
        out = self.mod.generate_agent_reasoning("Market Intelligence Agent", ctx)
        assert "₹200,000" in out
        assert "₹195,000" in out  # net saving

    def test_bias_template_passed(self):
        ctx = {"idle_disparity_pct": 3.1, "four_fifths_met": True, "counterfactual_flip_rate": 0.0}
        out = self.mod.generate_agent_reasoning("Bias Audit Agent", ctx)
        assert "PASSED" in out

    def test_bias_template_advisory(self):
        ctx = {"idle_disparity_pct": 20.0, "four_fifths_met": False, "counterfactual_flip_rate": 5.0}
        out = self.mod.generate_agent_reasoning("Bias Audit Agent", ctx)
        assert "ADVISORY FLAGGED" in out

    def test_unknown_agent_returns_fallback(self):
        out = self.mod.generate_agent_reasoning("Ghost Agent", {"scenario_id": "S-99"})
        assert "S-99" in out
