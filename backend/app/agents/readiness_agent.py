"""
Employer Readiness Agent
-------------------------
Validates that a proposed reallocation plan is physically and operationally safe for
the receiving production lines — before any plan is shown to the manager.

Checks:
1. Supervisor-to-worker safety ratio (max 1:8 per plant safety regulations).
2. Shift schedule compatibility for all proposed cross-line moves.
3. Physical line capacity (seats / workstations available).

Decision Boundary: Can veto any proposed assignment that violates hard operational
limits. Produces advisory warnings for borderline cases (ratio > 1:6).
"""

import logging
from typing import Any
from sqlalchemy.orm import Session
from app.models.db_models import ProductionLine, Worker
from app.agents.llm_adapter import generate_agent_reasoning

logger = logging.getLogger(__name__)

MAX_WORKERS_PER_SUPERVISOR = 8    # Hard regulatory limit
ADVISORY_THRESHOLD         = 6    # Soft warning if ratio > 1:6

# Approximate number of supervisors per line for Plant BLR-01
LINE_SUPERVISORS = {
    "LINE-01": 3,
    "LINE-02": 2,
    "LINE-03": 2,
    "LINE-01-AUTOMATED": 2,
}

# Available physical workstations per line
LINE_CAPACITY = {
    "LINE-01": 20,
    "LINE-02": 12,
    "LINE-03": 8,
    "LINE-01-AUTOMATED": 10,
}


def run(assignments: list[dict], db: Session) -> dict[str, Any]:
    """
    Main entry point for the Employer Readiness Agent.
    Takes a list of proposed assignment dicts (from the solver) and validates each one.
    """
    line_load: dict[str, list[str]] = {}  # destination_line → list of worker_ids

    for a in assignments:
        dest = a.get("destination_line", a.get("task_line", "UNKNOWN"))
        worker_id = a.get("worker_id", "?")
        line_load.setdefault(dest, []).append(worker_id)

    line_results = []
    overall_ok = True
    primary_line = "LINE-01"  # for context building

    for line_id, workers in line_load.items():
        supervisors = LINE_SUPERVISORS.get(line_id, 1)
        capacity = LINE_CAPACITY.get(line_id, 10)
        worker_count = len(workers)
        ratio_str = f"1:{round(worker_count / supervisors)}" if supervisors > 0 else "N/A"
        ratio_ok = (worker_count / supervisors) <= MAX_WORKERS_PER_SUPERVISOR if supervisors else True
        capacity_ok = worker_count <= capacity
        advisory = (
            worker_count / supervisors > ADVISORY_THRESHOLD
        ) if supervisors else False

        status = "OK"
        if not ratio_ok or not capacity_ok:
            status = "BLOCKED"
            overall_ok = False
        elif advisory:
            status = "ADVISORY"

        line_results.append({
            "line_id": line_id,
            "incoming_workers": worker_count,
            "supervisors_available": supervisors,
            "supervisor_ratio": ratio_str,
            "physical_capacity": capacity,
            "ratio_within_limit": ratio_ok,
            "capacity_within_limit": capacity_ok,
            "status": status,
            "advisory_note": "Ratio approaching limit — monitor line throughput." if advisory and ratio_ok else None,
        })
        primary_line = line_id  # last processed line for context

    # Check shift compatibility for all assignments
    shift_checks = _check_shift_compatibility(assignments, db)
    any_shift_blocked = any(not s["shift_compatible"] for s in shift_checks)
    if any_shift_blocked:
        overall_ok = False

    # Build context for reasoning
    primary_result = line_results[0] if line_results else {}
    context = {
        "destination_line": primary_line,
        "supervisor_ratio": primary_result.get("supervisor_ratio", "N/A"),
        "shift_compatible": not any_shift_blocked,
        "overall_ready": overall_ok,
        "lines_checked": len(line_results),
        "total_assignments": len(assignments),
    }

    reasoning = generate_agent_reasoning("Employer Readiness Agent", context)

    logger.info(
        "Employer Readiness: %d lines checked. Overall: %s.",
        len(line_results), "READY" if overall_ok else "BLOCKED",
    )

    return {
        "agent": "Employer Readiness Agent",
        "overall_ready": overall_ok,
        "line_readiness": line_results,
        "shift_compatibility": shift_checks,
        "reasoning": reasoning,
    }


def _check_shift_compatibility(assignments: list[dict], db: Session) -> list[dict]:
    """
    Verifies each worker's shift matches the task's required shift.
    Workers cannot be silently moved to a different shift without authorization.
    """
    results = []
    for a in assignments:
        worker_id = a.get("worker_id")
        task_shift = a.get("task_shift", a.get("shift", None))

        worker = db.query(Worker).filter(Worker.id == worker_id).first() if worker_id else None
        worker_shift = worker.shift if worker else None

        shift_ok = (task_shift is None or worker_shift is None or worker_shift == task_shift)
        results.append({
            "worker_id": worker_id,
            "worker_shift": worker_shift,
            "task_shift": task_shift,
            "shift_compatible": shift_ok,
        })
    return results
