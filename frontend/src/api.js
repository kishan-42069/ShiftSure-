/**
 * ShiftSure API Client
 * Uses relative URLs — Vite proxies /api → http://localhost:8000/api
 */

const BASE_URL = "/api";

// ── Scenarios ──────────────────────────────────────────────────────────────

export async function getScenarios() {
  const res = await fetch(`${BASE_URL}/scenarios/`);
  if (!res.ok) throw new Error("Failed to fetch scenarios");
  return res.json();
}

export async function createScenario(payload) {
  const res = await fetch(`${BASE_URL}/scenarios/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to create scenario");
  }
  return res.json();
}

// ── Workers ────────────────────────────────────────────────────────────────

export async function getWorkers() {
  const res = await fetch(`${BASE_URL}/workers/`);
  if (!res.ok) throw new Error("Failed to fetch workers");
  return res.json();
}

export async function getWorker(workerId) {
  const res = await fetch(`${BASE_URL}/workers/${workerId}`);
  if (!res.ok) throw new Error("Failed to fetch worker");
  return res.json();
}

// ── Agents (Sync run — returns full event list) ────────────────────────────

export async function runAgentPipeline(scenarioId) {
  const res = await fetch(`${BASE_URL}/agents/run/${scenarioId}`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Pipeline error");
  }
  return res.json();
}

// ── Plans ──────────────────────────────────────────────────────────────────

export async function getPlansForScenario(scenarioId) {
  const res = await fetch(`${BASE_URL}/plans/${scenarioId}`);
  if (!res.ok) throw new Error("Failed to fetch plans");
  return res.json();
}

export async function approvePlan(planId, approvedBy = "MANAGER") {
  const res = await fetch(`${BASE_URL}/plans/${planId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ approved_by: approvedBy }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to approve plan");
  }
  return res.json();
}

// ── Health ─────────────────────────────────────────────────────────────────

export async function getHealth() {
  try {
    const res = await fetch(`${BASE_URL}/health`);
    return res.json();
  } catch {
    return { status: "offline" };
  }
}

export async function getAgentHealth() {
  try {
    const res = await fetch(`${BASE_URL}/agents/health`);
    return res.json();
  } catch {
    return { status: "offline", agents_ready: 0 };
  }
}

// ── SSE Stream URL (used directly by EventSource) ─────────────────────────

export function getStreamUrl(scenarioId) {
  return `${BASE_URL}/agents/stream/${scenarioId}`;
}
