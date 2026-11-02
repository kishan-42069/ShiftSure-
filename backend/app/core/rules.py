"""
Hard Safety & Eligibility Rules
--------------------------------
These checks run BEFORE the math solver ever sees a worker-task pair.
A worker that fails a hard rule can NEVER be assigned — the solver cannot override this.
"""

from app.models.db_models import Worker, Task, WorkerSkill, WorkerCertification
from app.data.courses import get_course
from sqlalchemy.orm import Session


# --------------------------------------------------------------------------- #
# Rule Checking                                                                #
# --------------------------------------------------------------------------- #

def get_worker_skill_names(worker: Worker) -> set[str]:
    return {s.skill_name for s in worker.skills if s.verified}


def get_worker_valid_certs(worker: Worker) -> set[str]:
    return {c.cert_code for c in worker.certifications if c.is_valid}


def check_eligibility(
    worker: Worker,
    task: Task,
    max_training_hours: float = 20.0,
) -> dict:
    """
    Returns a structured eligibility result for a worker-task pair.

    Result fields:
      - eligible_now (bool): Can work this task TODAY, no training needed.
      - eligible_after_training (bool): Can qualify if given the bridge course.
      - training_required (dict | None): Course details if training is needed.
      - blocked (bool): Hard block — cannot assign regardless of training.
      - block_reasons (list[str]): Exactly why this worker is blocked.
      - proof (dict): Record of which checks passed/failed.
    """
    result = {
        "eligible_now": False,
        "eligible_after_training": False,
        "training_required": None,
        "blocked": False,
        "block_reasons": [],
        "proof": {},
    }

    worker_skills = get_worker_skill_names(worker)
    worker_certs = get_worker_valid_certs(worker)

    # ── Rule 1: Shift Compatibility ──────────────────────────────────────── #
    shift_ok = worker.shift == task.shift
    result["proof"]["shift_match"] = shift_ok
    if not shift_ok:
        result["blocked"] = True
        result["block_reasons"].append(
            f"Worker shift ({worker.shift}) does not match task shift ({task.shift})."
        )

    # ── Rule 2: Required Skills ──────────────────────────────────────────── #
    required_skills = set(task.required_skills)
    missing_skills = required_skills - worker_skills
    result["proof"]["required_skills"] = list(required_skills)
    result["proof"]["worker_skills"] = list(worker_skills)
    result["proof"]["missing_skills"] = list(missing_skills)

    skills_ok = len(missing_skills) == 0
    if not skills_ok:
        result["blocked"] = True
        result["block_reasons"].append(
            f"Missing required skills: {', '.join(missing_skills)}."
        )

    # ── Rule 3: Mandatory Safety Certifications ──────────────────────────── #
    mandatory_certs = set(task.mandatory_certs)
    missing_certs = mandatory_certs - worker_certs

    result["proof"]["mandatory_certs"] = list(mandatory_certs)
    result["proof"]["worker_certs"] = list(worker_certs)
    result["proof"]["missing_certs"] = list(missing_certs)

    if missing_certs:
        # Check if a training bridge is allowed and available for this task
        if task.training_bridge_permitted and task.training_bridge_cert:
            course = get_course(task.training_bridge_cert)
            if course and course["duration_hours"] <= max_training_hours:
                # Worker CAN qualify after completing this course
                result["training_required"] = course
                result["proof"]["training_bridge"] = {
                    "course_id": course["id"],
                    "title": course["title"],
                    "hours": course["duration_hours"],
                    "cost_inr": course["cost_inr"],
                    "cert_awarded": course["cert_awarded"],
                }
                # This is NOT a hard block — just needs training first
                if not result["blocked"]:  # skills and shift must still be okay
                    result["eligible_after_training"] = True
            else:
                # Course too long or not found — hard block
                result["blocked"] = True
                result["block_reasons"].append(
                    f"Missing mandatory certification(s): {', '.join(missing_certs)}. "
                    f"No permitted training bridge within {max_training_hours}h limit."
                )
        else:
            # No training bridge allowed — hard block
            result["blocked"] = True
            result["block_reasons"].append(
                f"Missing mandatory certification(s): {', '.join(missing_certs)}. "
                f"Training bridge not permitted for this task."
            )

    # ── Final eligibility determination ─────────────────────────────────── #
    if not result["blocked"] and not missing_certs:
        result["eligible_now"] = True

    return result


def build_eligibility_matrix(
    workers: list[Worker],
    tasks: list[Task],
    max_training_hours: float = 20.0,
) -> dict[str, dict[str, dict]]:
    """
    Checks every worker against every task.
    Returns a nested dict: eligibility[worker_id][task_id] = eligibility_result
    """
    matrix = {}
    for worker in workers:
        matrix[worker.id] = {}
        for task in tasks:
            matrix[worker.id][task.id] = check_eligibility(worker, task, max_training_hours)
    return matrix


def validate_plan_assignments(
    assignments: list[dict],
    workers: list[Worker],
    tasks: list[Task],
    max_training_hours: float = 20.0,
) -> tuple[bool, list[str]]:
    """
    After the solver generates a plan, run a final independent validation pass.
    Returns (all_valid: bool, list of violation messages).
    This is a second safety net — never rely solely on the solver.
    """
    violations = []
    worker_map = {w.id: w for w in workers}
    task_map = {t.id: t for t in tasks}

    # Track assigned hours per worker to detect over-capacity
    hours_per_worker: dict[str, float] = {}

    for a in assignments:
        wid = a["worker_id"]
        tid = a["task_id"]
        hours = a["assigned_hours"]

        if wid not in worker_map:
            violations.append(f"Unknown worker ID in plan: {wid}")
            continue
        if tid not in task_map:
            violations.append(f"Unknown task ID in plan: {tid}")
            continue

        worker = worker_map[wid]
        task = task_map[tid]

        # Check 1: Eligibility (now or after training bridge)
        elig = check_eligibility(worker, task, max_training_hours)
        if elig["blocked"]:
            violations.append(
                f"SAFETY VIOLATION — Worker {worker.name} ({wid}) assigned to task "
                f"'{task.title}' ({tid}) but is blocked: {'; '.join(elig['block_reasons'])}"
            )

        # Check 2: Capacity — worker cannot exceed available hours
        hours_per_worker[wid] = hours_per_worker.get(wid, 0.0) + hours
        if hours_per_worker[wid] > worker.available_hours:
            violations.append(
                f"CAPACITY VIOLATION — Worker {worker.name} ({wid}) assigned "
                f"{hours_per_worker[wid]:.1f}h but only has {worker.available_hours:.1f}h available."
            )

    is_valid = len(violations) == 0
    return is_valid, violations
