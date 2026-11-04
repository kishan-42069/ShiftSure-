# ShiftSure — How It's Built (Plain English)

> This document explains what ShiftSure is, how it works under the hood,
> every tool we used and why, and what the "deterministic templates" fallback is.
> No jargon. Written for a human.

---

## What is ShiftSure doing?

Imagine a factory. A packaging line gets automated — the robots take over.
**20 workers suddenly have no work to do.**

A manager's gut reaction: hire new people for open roles on other lines.
ShiftSure says: **wait — you already have people. Let's figure out who can move where.**

It runs 7 AI "agents" one after another, checks every worker's skills and certifications,
finds the best new assignments for everyone, proves it's fair (no bias),
and only then asks the manager to click **Approve.**

---

## The Big Picture — Two Engines, Not One

ShiftSure deliberately uses **two separate engines** that do very different things:

```
┌─────────────────────────────────────────────────────────────────┐
│  ENGINE A — The "Explainer" (Language Model / LLM)              │
│  Reads worker data, writes human-friendly explanations.         │
│  Example: "Priya has 82% skill match because she did CNC for    │
│  3 years and the gap can be closed in 8 hours of training."     │
│  → Never makes the actual assignment decision.                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  ENGINE B — The "Decider" (Google OR-Tools Math Solver)         │
│  Pure mathematics. No opinions. No hallucinations.              │
│  Looks at all workers, all tasks, all constraints,              │
│  and finds the mathematically best assignments.                 │
│  → Makes every real assignment decision.                        │
└─────────────────────────────────────────────────────────────────┘
```

**Why separate them?**
Because AI can lie (it's called "hallucination"). You don't want an AI
making up shift assignments. The math solver cannot lie — it either finds
a valid answer or says "impossible." LLMs are only used to explain **why**
the math made a specific decision, in plain English.

---

## The Tech Stack — What We Used and Why

### Backend (the "brain") — Python + FastAPI

| Tool | What it is | Why we used it |
|---|---|---|
| **Python** | Programming language | Most popular for AI/data work; huge library support |
| **FastAPI** | Web framework | Super fast to build APIs; built-in live-streaming support (SSE) |
| **SQLite + SQLAlchemy** | Database | Lightweight; no server needed; perfect for a demo |
| **Google OR-Tools (CP-SAT)** | Math solver | Google's open-source constraint solver; finds optimal assignments |
| **httpx** | HTTP library | Makes API calls to SAP AI Core and OpenAI |
| **pytest** | Testing tool | Runs automated tests to make sure nothing breaks |

### Frontend (what you see) — React + Vite

| Tool | What it is | Why we used it |
|---|---|---|
| **React** | UI library | Build interactive screens efficiently |
| **Vite** | Build tool | Instant hot-reload while developing |
| **Lucide Icons** | Icon library | Clean icons for the dashboard |
| **SSE (Server-Sent Events)** | Streaming protocol | Shows agents running live in real-time on screen |

---

## The 7 Agents — What Each One Does

Think of these like 7 specialists called into a room one by one, each doing
their job and passing notes to the next.

```
 [Scenario Triggered: LINE-03 automated, workers displaced]
         │
         ▼
 Agent 1 ── Skills Discovery Agent
         │   "What skills does this worker actually have?"
         │   Reads certifications, past tasks, skill proficiency levels.
         │
         ▼
 Agent 2 ── Market Intelligence Agent
         │   "Is it cheaper to retrain or hire externally?"
         │   External hire in Bengaluru = ₹1,85,000 + 28-day wait.
         │   Internal reskilling = ₹4,500 + 5 days. Easy call.
         │
         ▼
 Agent 3 ── Learning Pathway Agent
         │   "What exact course closes the skill gap?"
         │   Picks the right SAP Learning Hub course (e.g. 8-hour
         │   Robotics Safety course, code SAP-LH-ROB-101).
         │
         ▼
 Agent 4 ── Inclusive Matching Agent  ← triggers the MATH SOLVER
         │   Runs Google OR-Tools. Generates 3 plans:
         │     Plan A: By seniority (old-school supervisor style)
         │     Plan B: By lowest cost (purely efficient)
         │     Plan C: Fairness-balanced (our recommended plan)
         │
         ▼
 Agent 5 ── Employer Readiness Agent
         │   "Can the receiving line actually absorb these workers?"
         │   Checks supervisor ratios, shift compatibility, safety rules.
         │
         ▼
 Agent 6 ── Bias Audit Agent
         │   "Is the plan treating everyone fairly?"
         │   Runs EEOC 4/5ths Rule check.
         │   Runs Counterfactual Test (flips employment type, re-checks).
         │   Reports: PASSED or ADVISORY FLAGGED.
         │
         ▼
 Agent 7 ── Human-in-the-Loop Safeguard
             "Nothing moves until a human says yes."
             Sends worker a notification. Gives 24-hour appeal window.
             Manager must click Approve before anyone is moved.
```

---

## SAP Tools We Integrated

### 1. SAP AI Core + Generative AI Hub
**What it is:** SAP's cloud service for running Large Language Models (like GPT-4o)
inside the SAP ecosystem, with enterprise security and authentication.

**What we use it for:**
The 7 agents each produce a human-readable "reasoning" paragraph — the
plain-English explanation you see on screen. These paragraphs are generated
by GPT-4o hosted on SAP's AI Core, accessed through the Generative AI Hub.

**How the connection works:**
```
Our backend → asks SAP for a security token (OAuth2)
            → token cached in memory (refreshed every hour automatically)
            → sends the worker's data to AI Core
            → AI Core runs GPT-4o
            → returns the explanation paragraph
            → we show it on screen
```

**How we authenticate:**
Using standard SAP AI Core service key credentials from BTP:
`AICORE_AUTH_URL`, `AICORE_CLIENT_ID`, `AICORE_CLIENT_SECRET`,
`AICORE_BASE_URL`, `AICORE_DEPLOYMENT_ID`

---

### 2. SAP SuccessFactors (Simulated)
**What it is:** SAP's HR system — stores employee records, skills, certifications.

**What we reference:** Worker profiles including skills ontology, tenure,
certification records, and employment type (Permanent vs. Contract).

**In our demo:** The worker data is seeded in our local database to simulate
exactly what would come from a real SuccessFactors OData API call.
60 fictional workers, 3 production lines, real-looking skill sets.

---

### 3. SAP Learning Hub (Referenced)
**What it is:** SAP's online learning platform with certified course catalogues.

**What we use it for:** When Agent 3 (Learning Pathway) finds a skill gap,
it assigns a specific SAP Learning Hub course — real course codes
(e.g. `SAP-LH-ROB-101` = Robotics Safety & Collaborative Arm Operation, 8 hours, ₹4,500).

The course catalogue is baked into our system at `/backend/app/data/courses.py`.
In production, this would be a live API call to SAP Learning Hub.

---

### 4. SAP S/4HANA Manufacturing (Referenced)
**What it is:** SAP's enterprise ERP for factory operations — production planning,
maintenance, work centres.

**What we reference:** Line capacity, task definitions, supervisor ratios,
and shift planning would feed into S/4HANA's Production Planning (PP) module
upon manager approval.

---

### 5. SAP BTP (Business Technology Platform)
**What it is:** The cloud platform where all SAP services run.

**What we use it for:** Hosting SAP AI Core (our LLM provider).
Credentials are managed through BTP service keys.

---

## The Deterministic Templates — What Are They?

This is the most important thing to understand about ShiftSure's reliability.

### The Problem with AI

When you call an AI, three things can go wrong:
1. **No internet** — the API call fails
2. **API is down** — SAP or OpenAI servers are having issues
3. **No credits** — you haven't set up API keys yet

If any of these happen and ShiftSure relied 100% on AI, the demo would
**crash in front of the judges.**

### Our Solution: Pre-Written Smart Templates

We wrote **hand-crafted text templates** for each of the 7 agents.
These templates are just Python functions — no internet, no API, no cost.
They look at the real data (worker name, skill %, cost savings) and
produce a paragraph that looks exactly like what an AI would write.

### Example — How the Template Works

The Skills Discovery Agent template looks like this (simplified):

```python
def skills_template(worker_name, skills, skill_match_pct, gap_course):
    return (
        f"Skills Discovery complete for {worker_name}. "
        f"Verified skills: {skills} — these provide a {skill_match_pct}% match "
        f"to available automation roles. Identified narrow skill gap closeable "
        f"via {gap_course}, making {worker_name} a strong internal candidate."
    )
```

If we pass in real data: `worker_name="Priya S."`, `skill_match_pct=82`,
`gap_course="SAP-LH-ROB-101"` — it produces:

> *"Skills Discovery complete for Priya S. Verified skills: Manual Assembly,
> Quality Inspection — these provide a 82% match to available automation roles.
> Identified narrow skill gap closeable via SAP-LH-ROB-101, making Priya S.
> a strong internal redeployment candidate."*

That's real data, real numbers, meaningful text. Without a single AI call.

### The Fallback Priority Chain

```
When generate_agent_reasoning() is called:

  Step 1 → Try SAP AI Core (GPT-4o via Generative AI Hub)
              ↓ if fails (timeout, no key, server error)
  Step 2 → Try OpenAI directly
              ↓ if fails
  Step 3 → Use deterministic template  ← ALWAYS works, zero cost, offline
```

**This means: the demo can NEVER crash due to AI issues.**
The judges will always see clean, data-filled reasoning paragraphs,
whether SAP AI Core is live or not.

---

## How the Math Solver Works (Simple Version)

The Google OR-Tools CP-SAT solver is essentially solving a puzzle:

**The puzzle:**
- I have 20 displaced workers, each with different skills and shifts
- I have 15 open tasks on other lines, each needing certain skills
- Rules: a worker can't do more hours than they have; can't work the wrong shift;
  can't do a task needing a cert they don't have (unless a bridge course exists)
- Goal: assign workers to tasks so the **maximum work gets done** while
  **idle hours are shared equally between permanent and contract workers**

The solver tries thousands of combinations and finds the mathematically proven
best answer in under 30 seconds.

**Three plans, three philosophies:**

| Plan | Strategy | How it assigns |
|---|---|---|
| Plan A | SUPERVISOR_BASELINE | Most senior worker goes first. Old-school. |
| Plan B | COST_FOCUSED | Minimize cost and idle hours. Pure efficiency. |
| Plan C | FAIRNESS_BALANCED | Efficiency + fairness penalty if contract workers get more idle hours than permanent ones. **This is our recommended plan.** |

---

## The Database

We use a simple **SQLite database** (a single file, no server needed).
On startup, it auto-creates tables and loads 60 fictional workers across
3 production lines with real-looking skills and certifications.

Key tables:
- `workers` — name, shift, skills, certs, employment type, available hours
- `tasks` — what jobs are open, what skills/certs they need, shift, demand
- `allocation_plans` — the 3 plans generated by the solver
- `assignments` — which worker goes to which task in each plan
- `disruption_scenarios` — what triggered the reallocation (e.g. LINE-03 automated)

---

## How the Live Streaming Works

When you click "Run Analysis" in the UI, this is what happens:

```
Browser                     FastAPI Backend              Database / Solver / LLM
   │                              │                              │
   │── POST /api/agents/run ─────►│                              │
   │                              │── load scenario ────────────►│
   │◄── opens SSE stream ─────────│                              │
   │                              │                              │
   │◄── "Agent 1 starting..." ────│                              │
   │                              │── run skills agent ─────────►│
   │◄── "Agent 1 result: ..." ────│◄─────────────────────────────│
   │                              │                              │
   │◄── "Agent 2 starting..." ────│                              │
   │        ... (repeats) ...     │                              │
   │                              │                              │
   │◄── "PIPELINE_COMPLETE" ──────│                              │
```

SSE (Server-Sent Events) is a simple web protocol where the server
keeps the connection open and sends new data chunks as they're ready.
This is why you see agents appearing one-by-one on screen in real-time
instead of everything loading all at once.

---

## File Structure at a Glance

```
SAP/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── llm_adapter.py      ← SAP AI Core + OpenAI + fallback templates
│   │   │   ├── orchestrator.py     ← Runs all 7 agents in sequence
│   │   │   ├── skills_agent.py     ← Agent 1
│   │   │   ├── market_agent.py     ← Agent 2
│   │   │   ├── learning_agent.py   ← Agent 3
│   │   │   ├── matching_agent.py   ← Agent 4 (calls the solver)
│   │   │   ├── readiness_agent.py  ← Agent 5
│   │   │   ├── bias_agent.py       ← Agent 6
│   │   │   └── human_agent.py      ← Agent 7
│   │   ├── core/
│   │   │   ├── solver.py           ← Google OR-Tools math engine
│   │   │   ├── fairness.py         ← Idle hour fairness calculations
│   │   │   └── rules.py            ← Hard safety rules (shift, cert, skill checks)
│   │   ├── data/
│   │   │   ├── seed_data.py        ← 60 simulated workers + tasks
│   │   │   └── courses.py          ← SAP Learning Hub course catalogue
│   │   ├── routers/                ← API endpoints (workers, plans, agents, etc.)
│   │   └── main.py                 ← App startup + /api/health endpoint
│   └── tests/
│       ├── test_backend.py         ← Solver + fairness + rules tests
│       └── test_llm_adapter.py     ← LLM + fallback + token refresh tests
├── frontend/
│   └── src/components/             ← React screens (Dashboard, Architecture, etc.)
├── .env.example                    ← Template for SAP AI Core credentials
├── .gitignore                      ← Prevents secrets from being committed
└── ARCHITECTURE_EXPLAINED.md       ← This file
```

---

## Summary in One Paragraph

ShiftSure is a FastAPI + React application that simulates what happens
when a factory production line gets automated and workers need to be
redeployed. It runs 7 AI agents sequentially — each one analyses
a different aspect of the problem (skills, market costs, learning,
matching, readiness, fairness, human oversight). The actual work
assignment decisions are made by a Google OR-Tools math solver
(zero hallucinations, mathematically proven). The human-readable
explanations for each decision are generated by GPT-4o running on
SAP AI Core's Generative AI Hub — but if that's not available,
pre-written smart templates kick in automatically so the demo
always works, even with no internet and no API keys.

