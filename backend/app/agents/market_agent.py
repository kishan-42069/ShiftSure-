"""
Market Intelligence Agent
--------------------------
Benchmarks the cost and time of INTERNAL reskilling versus EXTERNAL hiring for the
roles that need to be filled after an automation disruption.

All benchmark figures are based on real Bengaluru/Karnataka manufacturing labor
market data (represented here as curated synthetic benchmarks — no live scraping
is performed in the prototype).

Decision Boundary: Advisory only. Cannot commit company budget or post jobs.
"""

import logging
from typing import Any
from app.agents.llm_adapter import generate_agent_reasoning

logger = logging.getLogger(__name__)

# ─── Bengaluru Manufacturing Labor Market Benchmarks ─────────────────────────
# Source basis: KPMG India Salary Benchmark 2024 (manufacturing), Karnataka
# Labour Department average recruitment timeline data, SAP Learning Hub pricing.
# These are synthetic values representative of the real range for demo purposes.

EXTERNAL_BENCHMARKS = {
    "Automated Cell Operator": {
        "avg_hiring_cost_inr": 185_000,   # includes agency fee, background check, onboarding
        "avg_lead_time_days":  28,
        "market_scarcity": "HIGH",         # certified automation operators are scarce in BLR
        "avg_monthly_salary_inr": 42_000,
    },
    "Automated QC Monitoring": {
        "avg_hiring_cost_inr": 145_000,
        "avg_lead_time_days":  21,
        "market_scarcity": "MEDIUM",
        "avg_monthly_salary_inr": 38_000,
    },
    "Automated Packaging Line Ops": {
        "avg_hiring_cost_inr": 95_000,
        "avg_lead_time_days":  14,
        "market_scarcity": "LOW",
        "avg_monthly_salary_inr": 28_000,
    },
    "Predictive Maintenance Ops": {
        "avg_hiring_cost_inr": 220_000,
        "avg_lead_time_days":  35,
        "market_scarcity": "VERY HIGH",
        "avg_monthly_salary_inr": 55_000,
    },
    "DEFAULT": {
        "avg_hiring_cost_inr": 150_000,
        "avg_lead_time_days":  21,
        "market_scarcity": "MEDIUM",
        "avg_monthly_salary_inr": 35_000,
    },
}

INTERNAL_RESKILLING_OVERHEAD_DAYS = 5   # average days worker is off the floor during training
INTERNAL_DAILY_WAGE_APPROX_INR   = 1_500  # conservative daily wage for downtime costing


def run(
    target_role: str,
    bridge_course_cost_inr: float,
    bridge_course_hours: float,
    displaced_worker_count: int = 1,
) -> dict[str, Any]:
    """
    Main entry point for the Market Intelligence Agent.
    Returns a detailed cost-comparison analysis.
    """
    benchmark = EXTERNAL_BENCHMARKS.get(target_role, EXTERNAL_BENCHMARKS["DEFAULT"])

    # Internal cost = training cost + lost productivity during training
    training_days = max(1, round(bridge_course_hours / 8))
    productivity_loss = training_days * INTERNAL_DAILY_WAGE_APPROX_INR
    internal_total = bridge_course_cost_inr + productivity_loss

    # External cost
    external_total = benchmark["avg_hiring_cost_inr"]
    lead_days = benchmark["avg_lead_time_days"]

    # Savings & ROI
    saving_per_worker = external_total - internal_total
    total_saving = saving_per_worker * displaced_worker_count
    roi_pct = round((saving_per_worker / external_total) * 100, 1) if external_total else 0

    context = {
        "target_role": target_role,
        "internal_cost_inr": round(internal_total),
        "external_cost_inr": external_total,
        "external_lead_days": lead_days,
        "saving_per_worker_inr": round(saving_per_worker),
        "total_saving_inr": round(total_saving),
        "market_scarcity": benchmark["market_scarcity"],
        "roi_pct": roi_pct,
        "displaced_worker_count": displaced_worker_count,
    }

    reasoning = generate_agent_reasoning("Market Intelligence Agent", context)

    logger.info(
        "Market Intelligence: Internal cost ₹%s vs External ₹%s — saving ₹%s per worker.",
        round(internal_total), external_total, round(saving_per_worker),
    )

    return {
        "agent": "Market Intelligence Agent",
        "target_role": target_role,
        "analysis": {
            "internal_reskilling": {
                "training_cost_inr": bridge_course_cost_inr,
                "productivity_loss_inr": productivity_loss,
                "total_cost_inr": round(internal_total),
                "training_days": training_days,
            },
            "external_hiring": {
                "total_cost_inr": external_total,
                "lead_time_days": lead_days,
                "market_scarcity": benchmark["market_scarcity"],
                "avg_monthly_salary_inr": benchmark["avg_monthly_salary_inr"],
            },
            "comparison": {
                "saving_per_worker_inr": round(saving_per_worker),
                "total_saving_for_all_displaced_inr": round(total_saving),
                "roi_pct": roi_pct,
                "recommendation": "INTERNAL_RESKILLING" if saving_per_worker > 0 else "EXTERNAL_HIRING",
            },
        },
        "reasoning": reasoning,
    }
