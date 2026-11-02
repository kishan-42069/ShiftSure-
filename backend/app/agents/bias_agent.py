"""
Bias Audit Agent
-----------------
Audits the proposed allocation plans for systemic bias and disparate impact.

What this agent checks:
1. Inter-group idle hour disparity (contract vs permanent, shift A vs shift B, etc.)
2. The EEOC 4/5ths (80%) adverse impact rule for training offer rates.
3. Counterfactual "what-if" test: flipping one non-job attribute should NOT change
   a worker's assignment — if it does, the solver has a hidden sensitivity.

Decision Boundary: Flags plans that exceed configurable thresholds. Issues
actionable warnings to the manager. Cannot suppress or modify solver output.
"""

import logging
from typing import Any
from sqlalchemy.orm import Session
from app.core.fairness import compute_fairness_report
from app.core.counterfactual import run_counterfactual_test
from app.agents.llm_adapter import generate_agent_reasoning

logger = logging.getLogger(__name__)

IDLE_DISPARITY_ALERT_THRESHOLD_PCT = 15.0  # configurable — flag if gap > 15%
FOUR_FIFTHS_THRESHOLD = 0.80               # EEOC standard


def run(plan_id: str, scenario_id: str, db: Session) -> dict[str, Any]:
    """
    Main entry point for the Bias Audit Agent.
    Runs fairness analytics and counterfactual test for the given plan.
    """
    # 1. Compute full fairness report using the deterministic fairness engine
    fairness_report = compute_fairness_report(plan_id=plan_id, db=db)

    # 2. Extract key metrics
    disparity_pct = fairness_report.get("max_group_idle_disparity_pct", 0.0)
    four_fifths_met = fairness_report.get("four_fifths_rule_met", True)
    training_rate_ratio = fairness_report.get("training_offer_rate_ratio", 1.0)

    # 3. Run counterfactual test (flips employment_type for all workers in scenario)
    cf_result = run_counterfactual_test(scenario_id=scenario_id, db=db)
    flip_rate = cf_result.get("assignment_flip_rate_pct", 0.0)
    cf_stable = cf_result.get("solver_stability_verified", True)

    # 4. Determine overall audit verdict
    flagged = False
    warnings = []

    if disparity_pct > IDLE_DISPARITY_ALERT_THRESHOLD_PCT:
        flagged = True
        warnings.append(
            f"Idle hour disparity ({disparity_pct:.1f}%) exceeds {IDLE_DISPARITY_ALERT_THRESHOLD_PCT}% threshold."
        )
    if not four_fifths_met:
        flagged = True
        warnings.append(
            f"4/5ths adverse impact rule NOT met — training offer ratio: {training_rate_ratio:.3f} (min: {FOUR_FIFTHS_THRESHOLD})."
        )
    if flip_rate > 0:
        flagged = True
        warnings.append(
            f"Counterfactual test detected {flip_rate:.1f}% assignment changes when non-job attribute was flipped."
        )

    audit_status = "PASSED_WITH_WARNINGS" if (flagged and not (disparity_pct > IDLE_DISPARITY_ALERT_THRESHOLD_PCT and not four_fifths_met)) else (
        "FAILED" if flagged else "PASSED"
    )

    context = {
        "plan_id": plan_id,
        "idle_disparity_pct": round(disparity_pct, 1),
        "four_fifths_met": four_fifths_met,
        "counterfactual_flip_rate": round(flip_rate, 1),
        "audit_status": audit_status,
    }

    reasoning = generate_agent_reasoning("Bias Audit Agent", context)

    logger.info(
        "Bias Audit for plan %s: status=%s, disparity=%.1f%%, counterfactual_flip=%.1f%%.",
        plan_id, audit_status, disparity_pct, flip_rate,
    )

    return {
        "agent": "Bias Audit Agent",
        "plan_id": plan_id,
        "audit_status": audit_status,
        "warnings": warnings,
        "disparity_analysis": {
            "max_idle_disparity_pct": round(disparity_pct, 1),
            "threshold_pct": IDLE_DISPARITY_ALERT_THRESHOLD_PCT,
            "disparity_within_threshold": disparity_pct <= IDLE_DISPARITY_ALERT_THRESHOLD_PCT,
            "group_breakdown": fairness_report.get("group_breakdown", {}),
        },
        "adverse_impact": {
            "four_fifths_rule_met": four_fifths_met,
            "training_offer_rate_ratio": round(training_rate_ratio, 3),
            "threshold": FOUR_FIFTHS_THRESHOLD,
        },
        "counterfactual_test": {
            "attribute_flipped": "employment_type (Contract → Permanent)",
            "assignment_flip_rate_pct": round(flip_rate, 1),
            "solver_stability_verified": cf_stable,
            "verdict": "No bias detected" if flip_rate == 0.0 else "Sensitivity detected — review required",
        },
        "audit_verdict": (
            "No protected or contract status bias detected. Ready for managerial review."
            if not flagged else
            f"Audit advisory: {' '.join(warnings)}"
        ),
        "reasoning": reasoning,
    }
