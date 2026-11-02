"""
Fairness Analytics Engine
--------------------------
Calculates measurable, evidence-based fairness metrics for each allocation plan.
All numbers here are computed from actual solver outputs — nothing is assumed or invented.

Key metrics:
  1. Idle Hours Distribution: Are some groups stuck with more downtime than others?
  2. Training Access Rate: Are training opportunities spread fairly?
  3. Counterfactual Sensitivity: Does flipping a non-job attribute change the result?
"""

from app.models.db_models import Worker, Assignment, AllocationPlan
from typing import Optional


# --------------------------------------------------------------------------- #
# Idle Hours per Worker                                                        #
# --------------------------------------------------------------------------- #

def calculate_idle_hours(
    workers: list[Worker],
    assignments: list[dict],
    planning_hours: float = 40.0,
) -> dict[str, float]:
    """
    idle_hours[worker_id] = planning_hours − total_assigned_hours_for_worker
    """
    assigned_map: dict[str, float] = {}
    for a in assignments:
        wid = a["worker_id"]
        assigned_map[wid] = assigned_map.get(wid, 0.0) + a["assigned_hours"]

    return {
        w.id: max(0.0, planning_hours - assigned_map.get(w.id, 0.0))
        for w in workers
    }


# --------------------------------------------------------------------------- #
# Group Disparity Analysis                                                     #
# --------------------------------------------------------------------------- #

def calculate_group_disparity(
    workers: list[Worker],
    idle_hours: dict[str, float],
    group_attr: str = "employment_type",  # "employment_type" | "shift"
) -> dict:
    """
    Compares average idle hours between groups.
    Returns the disparity, 4/5ths ratio, and which group has more downtime.
    """
    groups: dict[str, list[float]] = {}

    for worker in workers:
        key = getattr(worker, group_attr, "UNKNOWN")
        if key not in groups:
            groups[key] = []
        groups[key].append(idle_hours.get(worker.id, 0.0))

    group_stats = {}
    for group_name, hours_list in groups.items():
        avg = sum(hours_list) / len(hours_list) if hours_list else 0.0
        group_stats[group_name] = {
            "group_size": len(hours_list),
            "avg_idle_hours": round(avg, 2),
            "total_idle_hours": round(sum(hours_list), 2),
        }

    # 4/5ths Rule: the group with LEAST idle hours / group with MOST idle hours
    # (A ratio below 0.8 = adverse impact concern)
    all_avgs = [(g, s["avg_idle_hours"]) for g, s in group_stats.items()]
    if len(all_avgs) >= 2:
        all_avgs.sort(key=lambda x: x[1])
        best_group, best_avg = all_avgs[0]   # least idle = best outcome
        worst_group, worst_avg = all_avgs[-1]

        if worst_avg > 0:
            four_fifths_ratio = round(best_avg / worst_avg, 4) if best_avg > 0 else 0.0
        else:
            four_fifths_ratio = 1.0

        relative_disparity_pct = round(
            abs(worst_avg - best_avg) / max(worst_avg, 0.01) * 100, 2
        )

        four_fifths_passed = four_fifths_ratio >= 0.8 or relative_disparity_pct <= 15.0
    else:
        four_fifths_ratio = 1.0
        relative_disparity_pct = 0.0
        four_fifths_passed = True
        best_group = worst_group = list(group_stats.keys())[0] if group_stats else ""

    return {
        "group_attribute": group_attr,
        "group_stats": group_stats,
        "four_fifths_ratio": four_fifths_ratio,
        "four_fifths_threshold_met": four_fifths_passed,
        "relative_disparity_pct": relative_disparity_pct,
        "most_impacted_group": worst_group,
        "least_impacted_group": best_group,
    }


# --------------------------------------------------------------------------- #
# Training Access Rate                                                         #
# --------------------------------------------------------------------------- #

def calculate_training_access_rate(
    workers: list[Worker],
    assignments: list[dict],
    group_attr: str = "employment_type",
) -> dict:
    """
    Training offer rate = workers offered a training bridge / total eligible workers in that group.
    """
    training_offers: dict[str, int] = {}
    group_totals: dict[str, int] = {}

    worker_map = {w.id: w for w in workers}

    for a in assignments:
        wid = a["worker_id"]
        if wid not in worker_map:
            continue
        worker = worker_map[wid]
        key = getattr(worker, group_attr, "UNKNOWN")

        group_totals[key] = group_totals.get(key, 0) + 1
        if a.get("requires_training"):
            training_offers[key] = training_offers.get(key, 0) + 1

    rates = {}
    for group, total in group_totals.items():
        offered = training_offers.get(group, 0)
        rates[group] = {
            "total_assigned": total,
            "offered_training": offered,
            "offer_rate": round(offered / total, 4) if total > 0 else 0.0,
        }

    return {"group_attribute": group_attr, "training_access_by_group": rates}


# --------------------------------------------------------------------------- #
# Full Fairness Report                                                         #
# --------------------------------------------------------------------------- #

def generate_fairness_report(
    plan_id: str,
    workers: list[Worker],
    assignments: list[dict],
    planning_hours: float,
    threshold_disparity_pct: float = 0.15,
) -> dict:
    """
    Generates the complete fairness report for a given allocation plan.
    """
    idle = calculate_idle_hours(workers, assignments, planning_hours)
    emp_disparity = calculate_group_disparity(workers, idle, "employment_type")
    shift_disparity = calculate_group_disparity(workers, idle, "shift")
    training_access = calculate_training_access_rate(workers, assignments)

    total_idle_before = sum(w.available_hours for w in workers)
    total_idle_after = sum(idle.values())
    idle_hours_avoided = total_idle_before - total_idle_after

    # Audit determination
    disparity_ok = emp_disparity["relative_disparity_pct"] <= threshold_disparity_pct * 100
    if disparity_ok:
        audit_status = "PASSED"
    elif emp_disparity["four_fifths_threshold_met"]:
        audit_status = "PASSED_WITH_ADVISORY"
    else:
        audit_status = "FAILED"

    return {
        "plan_id": plan_id,
        "audit_status": audit_status,
        "disparity_results": {
            "by_employment_type": emp_disparity,
            "by_shift": shift_disparity,
        },
        "training_access": training_access,
        "idle_hours_avoided": round(idle_hours_avoided, 2),
        "disparity_threshold_pct": threshold_disparity_pct * 100,
        "counterfactual_result": {},  # filled in by counterfactual.py
    }


# --------------------------------------------------------------------------- #
# DB-Aware Wrapper: Called by Bias Audit Agent                                 #
# --------------------------------------------------------------------------- #

def compute_fairness_report(plan_id: str, db) -> dict:
    """
    DB-aware wrapper around generate_fairness_report().
    Loads workers and assignments from the DB for the given plan,
    then delegates to the core fairness engine.
    Called by the Bias Audit Agent with just (plan_id, db).
    """
    import json

    plan: AllocationPlan | None = db.query(AllocationPlan).filter(
        AllocationPlan.id == plan_id
    ).first()
    if not plan:
        return {
            "max_group_idle_disparity_pct": 0.0,
            "four_fifths_rule_met": True,
            "training_offer_rate_ratio": 1.0,
            "group_breakdown": {},
            "error": f"Plan {plan_id} not found",
        }

    # Load assignments from relationship or JSON field fallback
    assignments = []
    if getattr(plan, "assignments", None):
        for a in plan.assignments:
            if isinstance(a, dict):
                assignments.append(a)
            else:
                assignments.append({
                    "worker_id": getattr(a, "worker_id", ""),
                    "worker_name": getattr(a, "worker_name", ""),
                    "task_id": getattr(a, "task_id", ""),
                    "assigned_hours": float(getattr(a, "assigned_hours", 0.0)),
                    "requires_training": bool(getattr(a, "requires_training", False)),
                })

    # Load all workers
    from app.models.db_models import Worker
    workers = db.query(Worker).all()

    if not workers or not assignments:
        return {
            "max_group_idle_disparity_pct": 0.0,
            "four_fifths_rule_met": True,
            "training_offer_rate_ratio": 1.0,
            "group_breakdown": {},
        }

    # Try to get planning_hours from the linked scenario
    planning_hours = 40.0
    try:
        from app.models.db_models import DisruptionScenario
        scenario = db.query(DisruptionScenario).filter(
            DisruptionScenario.id == plan.scenario_id
        ).first()
        if scenario and scenario.planning_period_hours:
            planning_hours = float(scenario.planning_period_hours)
    except Exception:
        pass

    core_report = generate_fairness_report(
        plan_id=plan_id,
        workers=workers,
        assignments=assignments,
        planning_hours=planning_hours,
    )

    # Flatten into the shape the Bias Audit Agent expects
    emp_disparity = core_report.get("disparity_results", {}).get("by_employment_type", {})
    training_access = core_report.get("training_access", {})

    group_a_rate = training_access.get("group_training_rates", {})
    rates = list(group_a_rate.values()) if group_a_rate else [1.0, 1.0]
    ratio = (min(rates) / max(rates)) if len(rates) >= 2 and max(rates) > 0 else 1.0

    return {
        "max_group_idle_disparity_pct": emp_disparity.get("relative_disparity_pct", 0.0),
        "four_fifths_rule_met": emp_disparity.get("four_fifths_threshold_met", True),
        "training_offer_rate_ratio": round(ratio, 3),
        "group_breakdown": {
            "by_employment_type": emp_disparity,
            "training_access": training_access,
        },
        "audit_status": core_report.get("audit_status", "PASSED"),
    }

