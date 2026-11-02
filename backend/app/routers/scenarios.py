"""
Scenarios API Router
Handles creating and viewing automation disruption scenarios.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.db_models import DisruptionScenario, ProductionLine, AuditEvent
from app.models.schemas import ScenarioCreateIn, ScenarioOut

router = APIRouter(prefix="/api/scenarios", tags=["Scenarios"])


@router.get("/", response_model=list[ScenarioOut])
def list_scenarios(db: Session = Depends(get_db)):
    """Returns all disruption scenarios."""
    return db.query(DisruptionScenario).all()


@router.get("/{scenario_id}", response_model=ScenarioOut)
def get_scenario(scenario_id: str, db: Session = Depends(get_db)):
    """Returns details of one disruption scenario."""
    scenario = db.query(DisruptionScenario).filter(DisruptionScenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")
    return scenario


@router.post("/", response_model=ScenarioOut, status_code=201)
def create_scenario(payload: ScenarioCreateIn, db: Session = Depends(get_db)):
    """
    Manager creates a new automation disruption scenario.
    Validates that the affected production line exists before accepting.
    """
    line = db.query(ProductionLine).filter(ProductionLine.id == payload.affected_line_id).first()
    if not line:
        raise HTTPException(
            status_code=400,
            detail=f"Production line '{payload.affected_line_id}' does not exist. "
                   f"Valid lines: LINE-01, LINE-02, LINE-03."
        )

    scenario = DisruptionScenario(
        id=f"SCN-{uuid.uuid4().hex[:8].upper()}",
        name=payload.name,
        affected_line_id=payload.affected_line_id,
        workload_reduction_pct=payload.workload_reduction_pct,
        planning_period_hours=payload.planning_period_hours,
        max_training_hours=payload.max_training_hours,
        fairness_weight=payload.fairness_weight,
        idle_disparity_threshold=payload.idle_disparity_threshold,
        status="DRAFT",
    )
    db.add(scenario)

    db.add(AuditEvent(
        actor="MANAGER:SYSTEM",
        action="SCENARIO_CREATED",
        entity_id=scenario.id,
        detail=f"Disruption: {payload.workload_reduction_pct * 100:.0f}% workload reduction on {payload.affected_line_id}",
    ))

    db.commit()
    db.refresh(scenario)
    return scenario
