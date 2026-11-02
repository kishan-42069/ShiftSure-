"""
Inclusive Matching Agent
-------------------------
Formulates the workforce reallocation problem as a structured input for the
Google OR-Tools CP-SAT solver and interprets the solver output.

THE CRITICAL RULE: This agent NEVER assigns workers itself. It strictly translates
management objectives into solver parameters, delegates the actual computation to
the deterministic math solver, and then narrates the results.

The LLM (if present) is only used to explain the results AFTER the solver finishes.
It cannot alter, override, or second-guess the mathematical assignments.
"""

import logging
from typing import Any
from sqlalchemy.orm import Session
from app.models.db_models import DisruptionScenario
from app.core.solver import run_all_strategies
from app.agents.llm_adapter import generate_agent_reasoning

logger = logging.getLogger(__name__)


def run(scenario_id: str, db: Session) -> dict[str, Any]:
    """
    Main entry point for the Inclusive Matching Agent.
    Loads scenario, runs the OR-Tools solver for all 3 strategies, and returns results.
    """
    scenario: DisruptionScenario | None = db.query(DisruptionScenario).filter(
        DisruptionScenario.id == scenario_id
    ).first()

    if not scenario:
        return {"error": f"Scenario {scenario_id} not found", "agent": "Inclusive Matching Agent"}

    logger.info("Inclusive Matching Agent: delegating to OR-Tools solver for scenario %s.", scenario_id)

    # Delegate 100% of assignment computation to the deterministic OR-Tools solver
    solver_results = run_all_strategies(scenario_id=scenario_id, db=db)

    # Extract summary metrics for the fairness-balanced plan (Plan C) for reasoning
    plan_c = next(
        (r for r in solver_results if r.get("strategy") == "FAIRNESS_BALANCED"), {}
    )
    assignments = plan_c.get("assignments", [])
    metrics = plan_c.get("metrics", {})

    context = {
        "scenario_id": scenario_id,
        "strategy": "FAIRNESS_BALANCED",
        "workers_matched": len(assignments),
        "fill_rate_pct": metrics.get("internal_fill_rate_pct", 0),
        "idle_hours_saved": metrics.get("total_idle_hours_avoided", 0),
        "solver_status": plan_c.get("solver_status", "UNKNOWN"),
        "unfilled_tasks": len(plan_c.get("unfilled_tasks", [])),
    }

    reasoning = generate_agent_reasoning("Inclusive Matching Agent", context)

    logger.info(
        "Inclusive Matching: %d workers matched across 3 strategies. Status: %s.",
        len(assignments), plan_c.get("solver_status", "UNKNOWN"),
    )

    return {
        "agent": "Inclusive Matching Agent",
        "scenario_id": scenario_id,
        "solver_status": plan_c.get("solver_status", "UNKNOWN"),
        "strategies_generated": [r.get("strategy") for r in solver_results],
        "plan_summary": {
            "workers_matched": len(assignments),
            "fill_rate_pct": metrics.get("internal_fill_rate_pct", 0),
            "idle_hours_saved": metrics.get("total_idle_hours_avoided", 0),
            "net_training_investment_inr": metrics.get("net_training_investment_inr", 0),
            "external_hiring_avoidance_inr": metrics.get("external_hiring_avoidance_inr", 0),
        },
        "all_plans": solver_results,
        "reasoning": reasoning,
    }
