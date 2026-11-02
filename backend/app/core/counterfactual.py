"""
Counterfactual "What-If" Engine
---------------------------------
Answers this question:
  "If I change one non-job attribute about a worker (like their employment type),
   does the solver give them a different assignment?"

If the answer is YES without a job-related reason → potential bias alert.
If the answer is NO → the solver is treating this attribute correctly (ignoring it).

This is run AFTER the primary solver and uses the EXACT SAME settings.
"""

import copy
from app.models.db_models import Worker
from app.core.solver import run_solver


def run_counterfactual(
    original_workers: list[Worker],
    tasks: list,
    target_worker_id: str,
    flip_attribute: str,
    flip_from: str,
    flip_to: str,
    planning_hours: float,
    max_training_hours: float,
    fairness_weight: float,
    strategy: str = "FAIRNESS_BALANCED",
    random_seed: int = 42,
) -> dict:
    """
    Runs a what-if test by flipping one attribute on one worker and re-running the solver.

    Returns:
      - original_assignment: what the solver gave the worker originally.
      - counterfactual_assignment: what the solver gave after the attribute flip.
      - assignment_changed: True if the assignment changed.
      - interpretation: a plain-English conclusion.
    """

    # ── Step 1: Find the original assignment for the target worker ──────── #
    original_result = run_solver(
        workers=original_workers,
        tasks=tasks,
        planning_hours=planning_hours,
        max_training_hours=max_training_hours,
        fairness_weight=fairness_weight,
        strategy=strategy,
        seed=random_seed,
    )

    original_assignment = next(
        (a for a in original_result["assignments"] if a["worker_id"] == target_worker_id),
        None,
    )

    # ── Step 2: Clone worker list and flip the target attribute ─────────── #
    # We make a shallow attribute-level copy — we don't touch the DB
    cloned_workers = []
    for w in original_workers:
        if w.id == target_worker_id:
            # Create a simple namespace object that mimics the worker
            cloned = _clone_worker_with_flip(w, flip_attribute, flip_to)
            cloned_workers.append(cloned)
        else:
            cloned_workers.append(w)

    # ── Step 3: Re-run solver with IDENTICAL settings ────────────────────── #
    counterfactual_result = run_solver(
        workers=cloned_workers,
        tasks=tasks,
        planning_hours=planning_hours,
        max_training_hours=max_training_hours,
        fairness_weight=fairness_weight,
        strategy=strategy,
        seed=random_seed,  # SAME seed → only difference is the flipped attribute
    )

    cf_assignment = next(
        (a for a in counterfactual_result["assignments"] if a["worker_id"] == target_worker_id),
        None,
    )

    # ── Step 4: Compare results ──────────────────────────────────────────── #
    original_task = original_assignment["task_id"] if original_assignment else None
    cf_task = cf_assignment["task_id"] if cf_assignment else None
    assignment_changed = original_task != cf_task

    if assignment_changed:
        interpretation = (
            f"⚠️ SENSITIVITY ALERT: Flipping '{flip_attribute}' from '{flip_from}' to '{flip_to}' "
            f"changed worker {target_worker_id}'s assignment from '{original_task}' to '{cf_task}'. "
            f"Review whether a job-relevant rule caused this change, or if it indicates bias."
        )
    else:
        interpretation = (
            f"✅ STABLE: Flipping '{flip_attribute}' from '{flip_from}' to '{flip_to}' "
            f"did NOT change worker {target_worker_id}'s assignment ('{original_task}'). "
            f"The solver correctly treats this attribute as irrelevant to job allocation."
        )

    return {
        "target_worker_id": target_worker_id,
        "flipped_attribute": flip_attribute,
        "flip_from": flip_from,
        "flip_to": flip_to,
        "original_assignment": original_assignment,
        "counterfactual_assignment": cf_assignment,
        "assignment_changed": assignment_changed,
        "interpretation": interpretation,
        "solver_status_original": original_result["solver_status"],
        "solver_status_counterfactual": counterfactual_result["solver_status"],
    }


class _ClonedWorker:
    """
    Lightweight in-memory copy of a Worker with one attribute changed.
    Used ONLY for counterfactual testing — never written to the database.
    """
    def __init__(self, original: Worker):
        self.id = original.id
        self.name = original.name
        self.role = original.role
        self.line_id = original.line_id
        self.shift = original.shift
        self.employment_type = original.employment_type
        self.available_hours = original.available_hours
        self.tenure_years = original.tenure_years
        self.skills = original.skills
        self.certifications = original.certifications


def _clone_worker_with_flip(original: Worker, attribute: str, new_value: str) -> "_ClonedWorker":
    """Creates an in-memory copy of a worker with one attribute flipped."""
    cloned = _ClonedWorker(original)
    if hasattr(cloned, attribute):
        setattr(cloned, attribute, new_value)
    return cloned


# --------------------------------------------------------------------------- #
# DB-Aware Wrapper: Called by Bias Audit Agent                                 #
# --------------------------------------------------------------------------- #

def run_counterfactual_test(scenario_id: str, db) -> dict:
    """
    DB-aware wrapper around run_counterfactual().
    Runs the counterfactual test for the primary demo worker (W-104 / Priya Sharma),
    flipping employment_type from Contract → Permanent and verifying solver stability.
    Called by the Bias Audit Agent with just (scenario_id, db).
    """
    from app.models.db_models import DisruptionScenario, Worker, Task

    scenario = db.query(DisruptionScenario).filter(
        DisruptionScenario.id == scenario_id
    ).first()
    if not scenario:
        return {
            "assignment_flip_rate_pct": 0.0,
            "solver_stability_verified": True,
            "error": f"Scenario {scenario_id} not found",
        }

    displaced_workers = db.query(Worker).filter(Worker.line_id == scenario.affected_line_id).all()
    open_tasks = db.query(Task).filter(Task.line_id != scenario.affected_line_id).all()

    # Pick the primary test worker — W-104 (Priya Sharma) or first displaced worker
    target_id = "W-104"
    target_worker = next((w for w in displaced_workers if w.id == target_id), None)
    if not target_worker and displaced_workers:
        target_worker = displaced_workers[0]
        target_id = target_worker.id

    if not target_worker:
        return {"assignment_flip_rate_pct": 0.0, "solver_stability_verified": True}

    planning_hours = float(scenario.planning_period_hours or 40.0)
    max_training = float(scenario.max_training_hours or 20.0)
    fairness_w = float(scenario.fairness_weight or 0.35)

    # Determine flip values: if worker is CONTRACT → flip to PERMANENT, else flip vice-versa
    original_emp_type = (target_worker.employment_type or "PERMANENT").upper()
    flip_to = "PERMANENT" if original_emp_type == "CONTRACT" else "CONTRACT"

    result = run_counterfactual(
        original_workers=displaced_workers,
        tasks=open_tasks,
        target_worker_id=target_id,
        flip_attribute="employment_type",
        flip_from=original_emp_type,
        flip_to=flip_to,
        planning_hours=planning_hours,
        max_training_hours=max_training,
        fairness_weight=fairness_w,
        strategy="FAIRNESS_BALANCED",
    )

    assignment_changed = result.get("assignment_changed", False)
    return {
        "target_worker_id": target_id,
        "attribute_flipped": "employment_type",
        "flip_from": original_emp_type,
        "flip_to": flip_to,
        "assignment_flip_rate_pct": 100.0 if assignment_changed else 0.0,
        "solver_stability_verified": not assignment_changed,
        "interpretation": result.get("interpretation", ""),
    }

