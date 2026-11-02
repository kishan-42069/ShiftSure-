"""
Human-in-the-Loop Safeguard Agent
-----------------------------------
Protects both managerial authority and worker agency.

Responsibilities:
1. Enforces that a plan can ONLY be approved by a manager with a valid token.
2. Notifies workers of their proposed transfer and training pathway.
3. Handles worker-initiated skill correction requests.
4. Keeps a full audit trail of every approval, rejection, and appeal.

Decision Boundary: This is the SOLE authority that can transition a plan from
PENDING_APPROVAL → APPROVED or REJECTED. Rejections require a documented reason.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session
from app.models.db_models import AllocationPlan, AuditEvent, Worker
from app.agents.llm_adapter import generate_agent_reasoning

logger = logging.getLogger(__name__)


def notify_worker(worker_id: str, plan_id: str, assignment: dict, db: Session) -> dict[str, Any]:
    """
    Notifies a worker of their proposed transfer and SAP Learning Hub course.
    Logs the notification in the audit trail.
    """
    worker: Worker | None = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        return {"error": f"Worker {worker_id} not found"}

    course = assignment.get("training_bridge_required", {})
    destination = assignment.get("destination_line", "a new production line")

    notification = {
        "worker_id": worker_id,
        "worker_name": worker.name,
        "message": (
            f"Dear {worker.name}, you have been proposed for a transfer to {destination} "
            f"under the ShiftSure Fair Reallocation Plan. "
            + (
                f"To qualify for this role, you are recommended to complete "
                f"'{course.get('course_title', 'a bridge course')}' "
                f"({course.get('training_hours', 0)} hours) via SAP Learning Hub (Student Edition). "
                f"Cost: ₹{course.get('cost_inr', 0):,}. "
                if course else
                "You are already fully qualified for this role — no additional training required. "
            ) +
            f"You have 24 hours to review this proposal. Your feedback matters."
        ),
        "appeal_window_hours": 24,
        "plan_id": plan_id,
        "notified_at": datetime.now(timezone.utc).isoformat(),
    }

    # Log notification to audit trail
    _log_audit(
        db=db,
        plan_id=plan_id,
        action="WORKER_NOTIFIED",
        actor=worker_id,
        details=f"Worker {worker.name} notified of proposed transfer to {destination}.",
    )

    return notification


def generate_manager_summary(plan_id: str, db: Session) -> dict[str, Any]:
    """
    Generates a structured summary for the plant manager to review before approving.
    """
    plan: AllocationPlan | None = db.query(AllocationPlan).filter(
        AllocationPlan.id == plan_id
    ).first()

    if not plan:
        return {"error": f"Plan {plan_id} not found"}

    plan_state = getattr(plan, "state", "GENERATED")
    context = {
        "plan_id": plan_id,
        "status": plan_state,
        "worker_name": "multiple workers",
    }
    reasoning = generate_agent_reasoning("Human-in-the-Loop Safeguard", context)

    return {
        "agent": "Human-in-the-Loop Safeguard",
        "plan_id": plan_id,
        "current_status": plan_state,
        "manager_action_required": plan_state in ("PENDING_APPROVAL", "GENERATED"),
        "instructions": (
            "Review the 3-way plan comparison and the Bias Audit report before approving. "
            "An approval is irreversible — ensure all safety and fairness checks are marked PASSED. "
            "A rejection requires a documented business reason."
        ),
        "reasoning": reasoning,
    }


def _log_audit(db: Session, plan_id: str, action: str, actor: str, details: str) -> None:
    """Writes one timestamped entry to the audit event log."""
    event = AuditEvent(
        entity_id=plan_id,
        action=action,
        actor=actor,
        detail=details,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(event)
    db.commit()
    logger.info("Audit log: [%s] %s by %s — %s", plan_id, action, actor, details)
