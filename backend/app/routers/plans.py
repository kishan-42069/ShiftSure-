"""
Plans API Router
Handles running the solver, comparing the 3 plans, and manager approval/rejection.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.db_models import (
    DisruptionScenario, AllocationPlan, Assignment,
    Worker, Task, FairnessReport, AuditEvent
)
from app.models.schemas import PlanOut, PlanComparisonOut, ApproveIn, RejectIn, FairnessReportOut
from app.core.solver import run_solver
from app.core.fairness import generate_fairness_report
from app.core.rules import validate_plan_assignments
from app.core.counterfactual import run_counterfactual

router = APIRouter(prefix="/api", tags=["Plans"])


# --------------------------------------------------------------------------- #
# Run Solver & Generate All 3 Plans                                           #
# --------------------------------------------------------------------------- #

@router.post("/scenarios/{scenario_id}/solve", status_code=201)
def solve_scenario(scenario_id: str, db: Session = Depends(get_db)):
    """
    Triggers the math solver for a given disruption scenario.
    Generates all 3 allocation plans (Baseline, Cost-Focused, Fairness-Balanced).
    Runs post-solve validation to confirm no safety rules were broken.
    """
    scenario = db.query(DisruptionScenario).filter(DisruptionScenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")

    # Get ALL workers from the disrupted line (displaced workers needing reallocation)
    displaced_workers = db.query(Worker).filter(Worker.line_id == scenario.affected_line_id).all()

    if not displaced_workers:
        raise HTTPException(
            status_code=400,
            detail=f"No workers found on line '{scenario.affected_line_id}'."
        )

    # Get all open tasks on OTHER lines (where we want to redeploy workers)
    open_tasks = db.query(Task).filter(Task.line_id != scenario.affected_line_id).all()

    if not open_tasks:
        raise HTTPException(status_code=400, detail="No open tasks found on other lines.")

    created_plan_ids = []

    for strategy in ["SUPERVISOR_BASELINE", "COST_FOCUSED", "FAIRNESS_BALANCED"]:
        result = run_solver(
            workers=displaced_workers,
            tasks=open_tasks,
            planning_hours=scenario.planning_period_hours,
            max_training_hours=scenario.max_training_hours,
            fairness_weight=scenario.fairness_weight,
            strategy=strategy,
        )

        # Independent post-solve validation — second safety net
        is_valid, violations = validate_plan_assignments(
            result["assignments"], displaced_workers, open_tasks, scenario.max_training_hours
        )

        if not is_valid:
            # Log the violation but don't crash — mark plan as unsafe
            result["solver_status"] = "INFEASIBLE"
            result["assignments"] = []

        plan_id = f"PLAN-{strategy[:4]}-{uuid.uuid4().hex[:6].upper()}"
        plan = AllocationPlan(
            id=plan_id,
            scenario_id=scenario_id,
            strategy=strategy,
            solver_status=result["solver_status"],
            state="GENERATED",
            objective_value=result.get("objective_value"),
            metrics=result.get("metrics", {}),
        )
        db.add(plan)
        db.flush()

        # Save each individual assignment to the DB
        for a in result["assignments"]:
            db.add(Assignment(
                plan_id=plan_id,
                worker_id=a["worker_id"],
                worker_name=a["worker_name"],
                task_id=a["task_id"],
                assigned_hours=a["assigned_hours"],
                requires_training=a["requires_training"],
                training_course_id=a.get("training_course_id"),
                training_hours=a.get("training_hours", 0.0),
                training_cost_inr=a.get("training_cost_inr", 0.0),
                eligibility_proof=a.get("eligibility_proof", {}),
            ))

        # Run fairness report for this plan
        fairness = generate_fairness_report(
            plan_id=plan_id,
            workers=displaced_workers,
            assignments=result["assignments"],
            planning_hours=scenario.planning_period_hours,
            threshold_disparity_pct=scenario.idle_disparity_threshold,
        )
        db.add(FairnessReport(
            plan_id=plan_id,
            audit_status=fairness["audit_status"],
            disparity_results=fairness["disparity_results"],
            counterfactual_result={},
        ))

        db.add(AuditEvent(
            actor="SYSTEM",
            action=f"PLAN_GENERATED_{strategy}",
            entity_id=plan_id,
            detail=f"Solver status: {result['solver_status']}. "
                   f"Assignments: {len(result['assignments'])}. "
                   f"Violations: {len(violations)}.",
        ))

        created_plan_ids.append(plan_id)

    scenario.status = "COMPLETE"
    db.commit()

    return {
        "message": "All 3 allocation plans generated successfully.",
        "scenario_id": scenario_id,
        "plan_ids": created_plan_ids,
    }


# --------------------------------------------------------------------------- #
# Compare Plans                                                               #
# --------------------------------------------------------------------------- #

@router.get("/scenarios/{scenario_id}/compare", response_model=PlanComparisonOut)
def compare_plans(scenario_id: str, db: Session = Depends(get_db)):
    """Returns all 3 plans side-by-side for the manager comparison dashboard."""
    scenario = db.query(DisruptionScenario).filter(DisruptionScenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")

    plans = db.query(AllocationPlan).filter(AllocationPlan.scenario_id == scenario_id).all()
    if not plans:
        raise HTTPException(
            status_code=400,
            detail="No plans found. Run /solve first to generate plans."
        )

    return PlanComparisonOut(scenario_id=scenario_id, plans=plans)


# --------------------------------------------------------------------------- #
# Get One Plan                                                                #
# --------------------------------------------------------------------------- #

@router.get("/plans/{plan_id}", response_model=PlanOut)
def get_plan(plan_id: str, db: Session = Depends(get_db)):
    """Returns full details of one allocation plan including all assignments."""
    plan = db.query(AllocationPlan).filter(AllocationPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan '{plan_id}' not found.")
    return plan


# --------------------------------------------------------------------------- #
# Fairness Report for a Plan                                                  #
# --------------------------------------------------------------------------- #

@router.get("/plans/{plan_id}/fairness", response_model=FairnessReportOut)
def get_fairness_report(plan_id: str, db: Session = Depends(get_db)):
    """Returns the fairness audit report for a given plan."""
    report = db.query(FairnessReport).filter(FairnessReport.plan_id == plan_id).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"No fairness report for plan '{plan_id}'.")
    return report


# --------------------------------------------------------------------------- #
# Counterfactual What-If                                                      #
# --------------------------------------------------------------------------- #

@router.post("/plans/{plan_id}/counterfactual")
def run_counterfactual_test(
    plan_id: str,
    target_worker_id: str,
    flip_attribute: str = "employment_type",
    flip_from: str = "CONTRACT",
    flip_to: str = "PERMANENT",
    db: Session = Depends(get_db),
):
    """
    Runs a what-if test: flips one attribute of one worker and checks if the assignment changes.
    Proves (or flags) that non-job attributes don't bias the solver.
    """
    plan = db.query(AllocationPlan).filter(AllocationPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan '{plan_id}' not found.")

    scenario = plan.scenario
    workers = db.query(Worker).filter(Worker.line_id == scenario.affected_line_id).all()
    tasks = db.query(Task).filter(Task.line_id != scenario.affected_line_id).all()

    result = run_counterfactual(
        original_workers=workers,
        tasks=tasks,
        target_worker_id=target_worker_id,
        flip_attribute=flip_attribute,
        flip_from=flip_from,
        flip_to=flip_to,
        planning_hours=scenario.planning_period_hours,
        max_training_hours=scenario.max_training_hours,
        fairness_weight=scenario.fairness_weight,
        strategy=plan.strategy,
    )

    # Update the fairness report with counterfactual result
    report = db.query(FairnessReport).filter(FairnessReport.plan_id == plan_id).first()
    if report:
        report.counterfactual_result = result
        db.commit()

    return result


# --------------------------------------------------------------------------- #
# Manager Approval                                                            #
# --------------------------------------------------------------------------- #

@router.post("/plans/{plan_id}/submit")
def submit_for_approval(plan_id: str, db: Session = Depends(get_db)):
    """Manager submits a plan for final approval review."""
    plan = db.query(AllocationPlan).filter(AllocationPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan '{plan_id}' not found.")
    if plan.state != "GENERATED":
        raise HTTPException(
            status_code=400,
            detail=f"Plan is in state '{plan.state}'. Only GENERATED plans can be submitted."
        )
    plan.state = "PENDING_APPROVAL"
    db.add(AuditEvent(actor="MANAGER", action="PLAN_SUBMITTED", entity_id=plan_id, detail="Submitted for approval."))
    db.commit()
    return {"message": f"Plan '{plan_id}' submitted for approval.", "state": plan.state}


@router.post("/plans/{plan_id}/approve")
def approve_plan(plan_id: str, payload: ApproveIn, db: Session = Depends(get_db)):
    """
    Authorized manager approves a plan.
    Changes prototype status only — does NOT execute real-world worker transfers.
    """
    plan = db.query(AllocationPlan).filter(AllocationPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan '{plan_id}' not found.")
    if plan.state != "PENDING_APPROVAL":
        raise HTTPException(
            status_code=400,
            detail=f"Plan must be in PENDING_APPROVAL state to approve. Current state: {plan.state}."
        )

    plan.state = "APPROVED"
    plan.approved_by = payload.manager_id
    db.add(AuditEvent(
        actor=f"MANAGER:{payload.manager_id}",
        action="PLAN_APPROVED",
        entity_id=plan_id,
        detail=f"Approved by manager {payload.manager_id}. Prototype status change only — no real transfers.",
    ))
    db.commit()
    return {"message": f"Plan '{plan_id}' approved.", "approved_by": payload.manager_id}


@router.post("/plans/{plan_id}/reject")
def reject_plan(plan_id: str, payload: RejectIn, db: Session = Depends(get_db)):
    """Authorized manager rejects a plan with a mandatory documented reason."""
    plan = db.query(AllocationPlan).filter(AllocationPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan '{plan_id}' not found.")
    if plan.state != "PENDING_APPROVAL":
        raise HTTPException(
            status_code=400,
            detail=f"Plan must be in PENDING_APPROVAL state to reject. Current state: {plan.state}."
        )

    plan.state = "REJECTED"
    plan.rejection_reason = payload.reason
    db.add(AuditEvent(
        actor=f"MANAGER:{payload.manager_id}",
        action="PLAN_REJECTED",
        entity_id=plan_id,
        detail=f"Rejected. Reason: {payload.reason}",
    ))
    db.commit()
    return {"message": f"Plan '{plan_id}' rejected.", "reason": payload.reason}


# --------------------------------------------------------------------------- #
# Audit History                                                               #
# --------------------------------------------------------------------------- #

@router.get("/audit")
def get_audit_log(db: Session = Depends(get_db)):
    """Returns the full audit trail of all actions taken in the system."""
    events = db.query(AuditEvent).order_by(AuditEvent.timestamp.desc()).limit(200).all()
    return [
        {
            "id": e.id,
            "actor": e.actor,
            "action": e.action,
            "entity_id": e.entity_id,
            "detail": e.detail,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
        }
        for e in events
    ]
