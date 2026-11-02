"""
Learning Pathway Agent
-----------------------
Selects the minimal, precise SAP Learning Hub course sequence to close a worker's
skill gap for a target automation role.

Real SAP Learning Hub (Student Edition) course codes are used.
Syllabus links point to genuine SAP Learning Hub URLs.

Decision Boundary: Only proposes courses from the verified catalog. Cannot waive
mandatory safety certifications — training completion is required, no shortcuts.
"""

import logging
from typing import Any
from sqlalchemy.orm import Session
from app.models.db_models import Worker, WorkerCertification
from app.data.courses import COURSE_CATALOG
from app.agents.llm_adapter import generate_agent_reasoning

logger = logging.getLogger(__name__)

# Maps target automation roles to the required certifications for that role
ROLE_CERT_REQUIREMENTS = {
    "Automated Cell Operation":     ["ROBOTICS_SAFETY_L1"],
    "Automated QC Monitoring":      ["AUTO_QC_OPERATOR"],
    "Automated Packaging Line Ops": ["ROBOTICS_SAFETY_L1"],
    "Predictive Maintenance Ops":   ["MAINT_TECH_L1"],
    "Robotic Welding Cell Oversight": ["ROBOTICS_SAFETY_L1"],
    "AGV Supervision":              ["AGV_OPERATOR"],
}


def run(worker_id: str, target_role: str, db: Session) -> dict[str, Any]:
    """
    Main entry point for the Learning Pathway Agent.
    Returns the full learning pathway for a worker to qualify for a target role.
    """
    worker: Worker | None = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        return {"error": f"Worker {worker_id} not found", "agent": "Learning Pathway Agent"}

    # Certifications the worker already holds
    existing_certs = {
        getattr(c, "cert_code", getattr(c, "cert_name", "")) for c in db.query(WorkerCertification).filter(
            WorkerCertification.worker_id == worker_id
        ).all()
    }

    # Required certs for the target role
    required_certs = set(ROLE_CERT_REQUIREMENTS.get(target_role, []))

    # Gap = what's required but not yet held
    cert_gaps = required_certs - existing_certs

    # Build the learning pathway: find catalog courses that award the missing certs
    pathway = []
    total_hours = 0.0
    total_cost = 0.0

    for cert_gap in cert_gaps:
        course = _find_course_for_cert(cert_gap)
        if course:
            # Validate prerequisites
            prereqs = course.get("prerequisites", [])
            prereqs_met = all(p in existing_certs for p in prereqs)
            pathway.append({
                "step": len(pathway) + 1,
                "course_code": course["code"],
                "course_title": course["title"],
                "duration_hours": course["duration_hours"],
                "cost_inr": course["cost_inr"],
                "cert_awarded": course["cert_awarded"],
                "syllabus_url": course.get("syllabus_url", ""),
                "provider": "SAP Learning Hub (Student Edition)",
                "prerequisites_met": prereqs_met,
                "prerequisites": prereqs,
            })
            total_hours += course["duration_hours"]
            total_cost += course["cost_inr"]

    already_qualified = len(cert_gaps) == 0

    # Pick primary course for reasoning context
    primary = pathway[0] if pathway else {}

    context = {
        "worker_name": worker.name,
        "target_role": target_role,
        "existing_certs": list(existing_certs),
        "missing_certs": list(cert_gaps),
        "course_code": primary.get("course_code", "N/A"),
        "course_title": primary.get("course_title", "N/A"),
        "training_hours": total_hours,
        "total_cost_inr": total_cost,
        "already_qualified": already_qualified,
    }

    reasoning = generate_agent_reasoning("Learning Pathway Agent", context)

    logger.info(
        "Learning Pathway for %s → %s: %d courses, %.0f hrs, ₹%.0f.",
        worker_id, target_role, len(pathway), total_hours, total_cost,
    )

    return {
        "agent": "Learning Pathway Agent",
        "worker_id": worker_id,
        "worker_name": worker.name,
        "target_role": target_role,
        "already_fully_qualified": already_qualified,
        "existing_certifications": list(existing_certs),
        "certification_gaps": list(cert_gaps),
        "learning_pathway": pathway,
        "summary": {
            "total_courses": len(pathway),
            "total_training_hours": total_hours,
            "total_cost_inr": total_cost,
        },
        "reasoning": reasoning,
    }


def _find_course_for_cert(cert_name: str) -> dict | None:
    """Scans the SAP Learning Hub catalog for the course that awards a specific cert."""
    for code, course in COURSE_CATALOG.items():
        if course.get("cert_awarded") == cert_name:
            return {"code": code, **course}
    return None
