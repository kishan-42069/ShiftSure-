"""
Workers API Router
Handles reading worker profiles and submitting skill correction requests.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.db_models import Worker, CorrectionRequest, AuditEvent
from app.models.schemas import WorkerOut, CorrectionRequestIn, CorrectionRequestOut

router = APIRouter(prefix="/api/workers", tags=["Workers"])


@router.get("/", response_model=list[WorkerOut])
def list_workers(db: Session = Depends(get_db)):
    """Returns all workers in the factory."""
    workers = db.query(Worker).all()
    return workers


@router.get("/{worker_id}", response_model=WorkerOut)
def get_worker(worker_id: str, db: Session = Depends(get_db)):
    """Returns one worker's full profile including skills and certifications."""
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail=f"Worker '{worker_id}' not found.")
    return worker


@router.get("/{worker_id}/corrections", response_model=list[CorrectionRequestOut])
def get_worker_corrections(worker_id: str, db: Session = Depends(get_db)):
    """Returns all skill correction requests submitted by this worker."""
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail=f"Worker '{worker_id}' not found.")
    return worker.correction_requests


@router.post("/corrections", response_model=CorrectionRequestOut, status_code=201)
def submit_correction(payload: CorrectionRequestIn, db: Session = Depends(get_db)):
    """
    Worker submits a request to correct their skills or certifications record.
    The request enters PENDING state until a manager reviews it.
    """
    worker = db.query(Worker).filter(Worker.id == payload.worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail=f"Worker '{payload.worker_id}' not found.")

    correction = CorrectionRequest(
        worker_id=payload.worker_id,
        requested_change=payload.requested_change,
        status="PENDING",
    )
    db.add(correction)

    db.add(AuditEvent(
        actor=f"WORKER:{payload.worker_id}",
        action="SKILL_CORRECTION_SUBMITTED",
        entity_id=str(correction.id) if correction.id else "new",
        detail=payload.requested_change[:200],
    ))

    db.commit()
    db.refresh(correction)
    return correction
