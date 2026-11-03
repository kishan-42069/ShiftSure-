"""
ShiftSure Backend — Main Application Entry Point
Bengaluru Smart Auto Components Plant (Plant BLR-01)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, SessionLocal
from app.data.seed_data import seed_database
from app.routers import workers, scenarios, plans, agents
from app.agents.llm_adapter import get_llm_mode

app = FastAPI(
    title="ShiftSure API",
    description=(
        "Fair Workforce Reallocation During Automation and Disruption. "
        "SAP Hackfest Bengaluru 2026 — Theme 2: Inclusive Workforce. "
        "All data is simulated. No real workforce actions are performed."
    ),
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Allow the React frontend (running on localhost:5173) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all route groups
app.include_router(workers.router)
app.include_router(scenarios.router)
app.include_router(plans.router)
app.include_router(agents.router)


@app.on_event("startup")
def on_startup():
    """Runs once when the server starts: creates tables and seeds initial data."""
    init_db()
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


@app.get("/api/health")
def health_check():
    """Quick health check — confirms the server is running and reports the active LLM mode."""
    return {
        "status": "online",
        "plant": "Bengaluru Smart Auto Components Plant (Plant BLR-01)",
        "reasoning_mode": get_llm_mode(),
        "note": "All workforce data is simulated. LLM output is explanation-only.",
    }


@app.get("/")
def root():
    return {"message": "ShiftSure API is running. Visit /api/docs for interactive documentation."}
