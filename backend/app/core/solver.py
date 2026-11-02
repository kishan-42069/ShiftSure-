"""
Google OR-Tools Constraint Solver — The Core Brain
----------------------------------------------------
Generates 3 distinct allocation plans for a given disruption scenario.
The LLM never touches this file. All assignments are pure math.

Strategy 1 — SUPERVISOR_BASELINE:
  Greedy heuristic: assigns the most senior qualified worker first.
  No training bridges. No fairness balancing. Just seniority.

Strategy 2 — COST_FOCUSED:
  Full OR-Tools CP-SAT solver.
  Objective: maximize coverage and minimize idle hours / training cost.
  No fairness penalty — pure efficiency.

Strategy 3 — FAIRNESS_BALANCED (ShiftSure's signature plan):
  Full OR-Tools CP-SAT solver.
  Same as Strategy 2 PLUS a penalty for unequal idle-hour distribution
  across employment groups (permanent vs. contract workers).
"""

from ortools.sat.python import cp_model
from app.models.db_models import Worker, Task
from app.core.rules import build_eligibility_matrix
from app.data.courses import get_course
from typing import Literal


# --------------------------------------------------------------------------- #
# Strategy Type                                                                #
# --------------------------------------------------------------------------- #

Strategy = Literal["SUPERVISOR_BASELINE", "COST_FOCUSED", "FAIRNESS_BALANCED"]


# --------------------------------------------------------------------------- #
# Main Entry Point                                                             #
# --------------------------------------------------------------------------- #

def run_solver(
    workers: list[Worker],
    tasks: list[Task],
    planning_hours: float = 40.0,
    max_training_hours: float = 20.0,
    fairness_weight: float = 0.35,
    strategy: Strategy = "FAIRNESS_BALANCED",
    seed: int = 42,
) -> dict:
    """
    Runs the selected allocation strategy and returns structured results.

    Returns:
      - solver_status: OPTIMAL | FEASIBLE | INFEASIBLE | TIMEOUT
      - strategy: the strategy used
      - assignments: list of worker-task allocation records
      - metrics: summary statistics (idle hours, fill rate, costs)
      - unfilled_tasks: tasks where demand could not be met
    """
    if strategy == "SUPERVISOR_BASELINE":
        return _run_greedy_baseline(workers, tasks, planning_hours, max_training_hours)

    return _run_ortools(workers, tasks, planning_hours, max_training_hours, fairness_weight, strategy, seed)


# --------------------------------------------------------------------------- #
# Strategy 1: Greedy Supervisor Baseline                                       #
# --------------------------------------------------------------------------- #

def _run_greedy_baseline(
    workers: list[Worker],
    tasks: list[Task],
    planning_hours: float,
    max_training_hours: float,
) -> dict:
    """
    Simple greedy heuristic — assigns workers by seniority (highest tenure first).
    No training bridges. If you don't qualify today, you're skipped.
    Mimics how a traditional supervisor might handle redeployment manually.
    """
    eligibility = build_eligibility_matrix(workers, tasks, max_training_hours=0)  # no training in baseline

    # Sort workers by tenure (most senior first) — the supervisor mindset
    sorted_workers = sorted(workers, key=lambda w: -w.tenure_years)

    assignments = []
    remaining_capacity: dict[str, float] = {w.id: w.available_hours for w in workers}
    remaining_demand: dict[str, float] = {t.id: t.required_hours * t.required_headcount for t in tasks}
    task_map = {t.id: t for t in tasks}

    for task in tasks:
        for worker in sorted_workers:
            elig = eligibility[worker.id][task.id]
            if not elig["eligible_now"]:
                continue
            if remaining_capacity[worker.id] <= 0:
                continue
            if remaining_demand[task.id] <= 0:
                break

            hours_to_assign = min(
                task_map[task.id].required_hours,
                remaining_capacity[worker.id],
                remaining_demand[task.id],
            )

            if hours_to_assign <= 0:
                continue

            assignments.append({
                "worker_id": worker.id,
                "worker_name": worker.name,
                "task_id": task.id,
                "assigned_hours": hours_to_assign,
                "requires_training": False,
                "training_course_id": None,
                "training_hours": 0.0,
                "training_cost_inr": 0.0,
                "eligibility_proof": elig["proof"],
            })
            remaining_capacity[worker.id] -= hours_to_assign
            remaining_demand[task.id] -= hours_to_assign

    unfilled = [tid for tid, rem in remaining_demand.items() if rem > 0.5]
    metrics = _compute_metrics(workers, tasks, assignments, planning_hours)

    return {
        "solver_status": "FEASIBLE",
        "strategy": "SUPERVISOR_BASELINE",
        "assignments": assignments,
        "unfilled_tasks": unfilled,
        "metrics": metrics,
        "objective_value": None,
    }


# --------------------------------------------------------------------------- #
# Strategy 2 & 3: Google OR-Tools CP-SAT Optimizer                            #
# --------------------------------------------------------------------------- #

def _run_ortools(
    workers: list[Worker],
    tasks: list[Task],
    planning_hours: float,
    max_training_hours: float,
    fairness_weight: float,
    strategy: Strategy,
    seed: int,
) -> dict:
    """
    Uses Google OR-Tools CP-SAT (Constraint Programming — Satisfiability) solver.
    All assignments are integers (hours × 10 to keep it integer-safe).
    """
    eligibility = build_eligibility_matrix(workers, tasks, max_training_hours)
    model = cp_model.CpModel()

    SCALE = 10  # scale hours to integers (e.g. 4.5h → 45 units)
    MAX_UNITS = int(planning_hours * SCALE)

    # ── Decision Variables ───────────────────────────────────────────────── #
    # x[w][t] = integer units of time (in SCALE) worker w spends on task t
    x = {}
    for w in workers:
        x[w.id] = {}
        for t in tasks:
            elig = eligibility[w.id][t.id]
            if elig["blocked"]:
                # Hard block: variable is fixed to 0, solver cannot change it
                x[w.id][t.id] = model.NewConstant(0)
            else:
                x[w.id][t.id] = model.NewIntVar(
                    0,
                    int(t.required_hours * SCALE),
                    f"x_{w.id}_{t.id}",
                )

    # ── Hard Constraint 1: Worker Capacity ──────────────────────────────── #
    for w in workers:
        worker_cap = int(w.available_hours * SCALE)
        # Subtract training hours from available time for workers needing training
        for t in tasks:
            elig = eligibility[w.id][t.id]
            if elig.get("training_required"):
                training_h = elig["training_required"]["duration_hours"]
                worker_cap = int((w.available_hours - training_h) * SCALE)
                break  # simplification: at most one training bridge per worker per period

        model.Add(
            sum(x[w.id][t.id] for t in tasks) <= max(0, worker_cap)
        )

    # ── Hard Constraint 2: Task Demand Ceiling ───────────────────────────── #
    for t in tasks:
        demand_units = int(t.required_hours * t.required_headcount * SCALE)
        model.Add(
            sum(x[w.id][t.id] for w in workers) <= demand_units
        )

    # ── Objective Terms ──────────────────────────────────────────────────── #
    # Term A: Maximize total covered task hours (higher = better)
    coverage = sum(
        x[w.id][t.id]
        for w in workers
        for t in tasks
    )

    # Term B: Minimize idle hours (we penalize leftover idle capacity)
    idle_terms = []
    for w in workers:
        assigned = sum(x[w.id][t.id] for t in tasks)
        idle_var = model.NewIntVar(0, MAX_UNITS, f"idle_{w.id}")
        model.Add(idle_var == int(w.available_hours * SCALE) - assigned)
        idle_terms.append(idle_var)

    total_idle = sum(idle_terms)

    # Term C: Minimize total training cost (lower cost = better)
    total_training_cost = 0
    for w in workers:
        for t in tasks:
            elig = eligibility[w.id][t.id]
            if elig.get("training_required"):
                cost_units = int(elig["training_required"]["cost_inr"] / 100)  # scale down
                # If worker is assigned to this task at all, training cost is incurred
                is_assigned = model.NewBoolVar(f"is_assigned_{w.id}_{t.id}")
                model.Add(x[w.id][t.id] > 0).OnlyEnforceIf(is_assigned)
                model.Add(x[w.id][t.id] == 0).OnlyEnforceIf(is_assigned.Not())
                total_training_cost += cost_units * is_assigned

    # Term D: Fairness Penalty (FAIRNESS_BALANCED only)
    # Penalizes large differences in idle hours between permanent and contract workers
    fairness_penalty = 0

    if strategy == "FAIRNESS_BALANCED":
        permanent_workers = [w for w in workers if w.employment_type == "PERMANENT"]
        contract_workers = [w for w in workers if w.employment_type == "CONTRACT"]

        if permanent_workers and contract_workers:
            # Average idle hours proxy (sum / count — we use sums to stay integer)
            perm_idle_sum = sum(
                (model.NewIntVar(0, MAX_UNITS, f"pidle_{w.id}") for w in permanent_workers),
                start=model.NewConstant(0),
            )
            # Simpler formulation: track total idle per group, add penalty for gap
            perm_total_idle = sum(
                int(MAX_UNITS) - sum(x[w.id][t.id] for t in tasks)
                for w in permanent_workers
            )
            cont_total_idle = sum(
                int(MAX_UNITS) - sum(x[w.id][t.id] for t in tasks)
                for w in contract_workers
            )

            # Gap variable — always non-negative
            gap = model.NewIntVar(0, MAX_UNITS * len(workers), "fairness_gap")
            model.AddAbsEquality(gap, perm_total_idle - cont_total_idle)
            fairness_weight_int = int(fairness_weight * 100)
            fairness_penalty = fairness_weight_int * gap

    # ── Combined Objective ────────────────────────────────────────────────── #
    # Maximize: coverage - idle - training_cost - fairness_penalty
    model.Maximize(
        5 * coverage          # coverage is most important
        - 2 * total_idle      # idle hours are costly
        - total_training_cost # training cost is secondary
        - fairness_penalty    # fairness (only in Strategy 3)
    )

    # ── Solve ────────────────────────────────────────────────────────────── #
    solver = cp_model.CpSolver()
    solver.parameters.random_seed = seed
    solver.parameters.max_time_in_seconds = 30.0   # hard timeout for demo
    solver.parameters.num_search_workers = 4

    status_code = solver.Solve(model)

    # ── Map solver status to human-readable string ────────────────────────── #
    status_map = {
        cp_model.OPTIMAL: "OPTIMAL",
        cp_model.FEASIBLE: "FEASIBLE",
        cp_model.INFEASIBLE: "INFEASIBLE",
        cp_model.UNKNOWN: "TIMEOUT",
        cp_model.MODEL_INVALID: "INFEASIBLE",
    }
    solver_status = status_map.get(status_code, "TIMEOUT")

    if solver_status == "INFEASIBLE":
        return {
            "solver_status": "INFEASIBLE",
            "strategy": strategy,
            "assignments": [],
            "unfilled_tasks": [t.id for t in tasks],
            "metrics": {},
            "objective_value": None,
        }

    # ── Extract Assignments from Solver Solution ─────────────────────────── #
    assignments = []
    task_map = {t.id: t for t in tasks}

    for w in workers:
        for t in tasks:
            var = x[w.id][t.id]
            # For constant variables (hard-blocked), skip
            if hasattr(var, 'Index') and not hasattr(var, 'IsConstant'):
                assigned_units = solver.Value(var)
            else:
                try:
                    assigned_units = solver.Value(var)
                except Exception:
                    assigned_units = 0

            if assigned_units <= 0:
                continue

            assigned_hours = assigned_units / SCALE
            elig = eligibility[w.id][t.id]
            needs_training = bool(elig.get("training_required"))
            course = elig.get("training_required") or {}

            assignments.append({
                "worker_id": w.id,
                "worker_name": w.name,
                "task_id": t.id,
                "assigned_hours": assigned_hours,
                "requires_training": needs_training,
                "training_course_id": course.get("id"),
                "training_hours": course.get("duration_hours", 0.0),
                "training_cost_inr": course.get("cost_inr", 0.0),
                "eligibility_proof": elig["proof"],
            })

    unfilled = []
    task_assigned_hours: dict[str, float] = {}
    for a in assignments:
        task_assigned_hours[a["task_id"]] = task_assigned_hours.get(a["task_id"], 0.0) + a["assigned_hours"]

    for t in tasks:
        demand = t.required_hours * t.required_headcount
        if task_assigned_hours.get(t.id, 0.0) < demand * 0.5:
            unfilled.append(t.id)

    metrics = _compute_metrics(workers, tasks, assignments, planning_hours)

    return {
        "solver_status": solver_status,
        "strategy": strategy,
        "assignments": assignments,
        "unfilled_tasks": unfilled,
        "metrics": metrics,
        "objective_value": round(solver.ObjectiveValue(), 2),
    }


# --------------------------------------------------------------------------- #
# Metrics Calculation                                                          #
# --------------------------------------------------------------------------- #

def _compute_metrics(
    workers: list[Worker],
    tasks: list[Task],
    assignments: list[dict],
    planning_hours: float,
) -> dict:
    """
    Calculates the key output numbers shown in the plan comparison dashboard.
    """
    total_possible_hours = sum(w.available_hours for w in workers)
    total_assigned_hours = sum(a["assigned_hours"] for a in assignments)
    total_idle_hours = total_possible_hours - total_assigned_hours
    idle_hours_avoided = max(0.0, total_possible_hours - total_idle_hours)

    total_demand = sum(t.required_hours * t.required_headcount for t in tasks)
    task_covered: dict[str, float] = {}
    for a in assignments:
        task_covered[a["task_id"]] = task_covered.get(a["task_id"], 0.0) + a["assigned_hours"]

    covered_demand = sum(task_covered.values())
    task_coverage_pct = round(covered_demand / total_demand * 100, 1) if total_demand > 0 else 0.0

    # Workers using internal training bridges
    training_assignments = [a for a in assignments if a["requires_training"]]
    training_investment_inr = sum(a["training_cost_inr"] for a in training_assignments)

    # External hiring cost comparison (market benchmark for Bengaluru manufacturing)
    unfilled_count = len([t for t in tasks if task_covered.get(t.id, 0.0) < t.required_hours * 0.5])
    external_hiring_cost_inr = unfilled_count * 18500  # avg cost per external hire

    # Internal fill rate (tasks filled internally vs. total tasks)
    internally_filled = len([t for t in tasks if task_covered.get(t.id, 0.0) >= t.required_hours * 0.5])
    internal_fill_rate_pct = round(internally_filled / len(tasks) * 100, 1) if tasks else 0.0

    return {
        "total_workers": len(workers),
        "total_tasks": len(tasks),
        "total_idle_hours": round(total_idle_hours, 2),
        "idle_hours_avoided": round(idle_hours_avoided, 2),
        "task_coverage_pct": task_coverage_pct,
        "internal_fill_rate_pct": internal_fill_rate_pct,
        "workers_needing_training": len(training_assignments),
        "training_investment_inr": round(training_investment_inr, 2),
        "external_hiring_avoidance_inr": round(external_hiring_cost_inr, 2),
        "net_savings_inr": round(external_hiring_cost_inr - training_investment_inr, 2),
        "net_training_investment_inr": round(training_investment_inr, 2),
        "total_idle_hours_avoided": round(idle_hours_avoided, 2),
    }


# --------------------------------------------------------------------------- #
# DB-Aware Wrapper: Run All 3 Strategies From a Scenario ID                   #
# --------------------------------------------------------------------------- #

def run_all_strategies(scenario_id: str, db) -> list[dict]:
    """
    Loads a disruption scenario from the DB and runs all 3 allocation strategies.
    Returns a list of 3 plan result dicts (one per strategy).
    Used by the Inclusive Matching Agent so it never needs to touch raw DB queries.
    """
    from app.models.db_models import DisruptionScenario, Worker, Task

    scenario = db.query(DisruptionScenario).filter(
        DisruptionScenario.id == scenario_id
    ).first()
    if not scenario:
        return []

    # Workers on the affected line are the ones who need reallocation
    displaced_workers = db.query(Worker).filter(Worker.line_id == scenario.affected_line_id).all()

    # Open tasks on other lines available for reallocation
    open_tasks = db.query(Task).filter(Task.line_id != scenario.affected_line_id).all()

    planning_hours = float(scenario.planning_period_hours or 40.0)
    max_training = float(scenario.max_training_hours or 20.0)
    fairness_w = float(scenario.fairness_weight or 0.35)

    results = []
    for strategy in ("SUPERVISOR_BASELINE", "COST_FOCUSED", "FAIRNESS_BALANCED"):
        result = run_solver(
            workers=displaced_workers,
            tasks=open_tasks,
            planning_hours=planning_hours,
            max_training_hours=max_training,
            fairness_weight=fairness_w,
            strategy=strategy,
        )
        results.append(result)

    return results

