"""
Skills Discovery Agent
-----------------------
Examines a worker's recorded profile (skills, certifications, line history) and
identifies both direct qualifications and adjacent transferable capabilities.

Decision Boundary: Can suggest adjacent skills with a confidence score, but CANNOT
mark a mandatory safety certification as active without a verified database record.
"""

import logging
from typing import Any
from sqlalchemy.orm import Session
from app.models.db_models import Worker, WorkerSkill, WorkerCertification
from app.data.courses import COURSE_CATALOG
from app.agents.llm_adapter import generate_agent_reasoning

logger = logging.getLogger(__name__)

# Skills that transfer well into robotics / automation roles, with transferability %
ADJACENT_SKILL_MAP = {
    "Manual Assembly I":        {"target": "Automated Cell Operation",     "transfer_pct": 65},
    "Manual Assembly II":       {"target": "Automated Cell Operation",     "transfer_pct": 75},
    "Quality Inspection":       {"target": "Automated QC Monitoring",      "transfer_pct": 80},
    "Machine Operation":        {"target": "Automated Cell Operation",     "transfer_pct": 85},
    "Packaging Operations":     {"target": "Automated Packaging Line Ops", "transfer_pct": 60},
    "Forklift Operation":       {"target": "AGV Supervision",              "transfer_pct": 55},
    "Maintenance Technician":   {"target": "Predictive Maintenance Ops",   "transfer_pct": 90},
    "Welding":                  {"target": "Robotic Welding Cell Oversight","transfer_pct": 70},
}

# If a worker has ≥ this % transferability, they are a bridge candidate
BRIDGE_ELIGIBLE_THRESHOLD = 55


def run(worker_id: str, db: Session) -> dict[str, Any]:
    """
    Main entry point for the Skills Discovery Agent.
    Returns a structured findings dict consumed by the Career Orchestrator.
    """
    worker: Worker | None = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        return {"error": f"Worker {worker_id} not found", "agent": "Skills Discovery Agent"}

    # 1. Pull verified skills from DB
    skills = [s.skill_name for s in db.query(WorkerSkill).filter(
        WorkerSkill.worker_id == worker_id
    ).all()]

    # 2. Pull verified certifications
    certs = [getattr(c, "cert_code", getattr(c, "cert_name", "")) for c in db.query(WorkerCertification).filter(
        WorkerCertification.worker_id == worker_id
    ).all()]

    # 3. Discover adjacent capabilities
    adjacent = []
    best_match_pct = 0
    for skill in skills:
        if skill in ADJACENT_SKILL_MAP:
            mapping = ADJACENT_SKILL_MAP[skill]
            if mapping["transfer_pct"] >= BRIDGE_ELIGIBLE_THRESHOLD:
                adjacent.append({
                    "source_skill": skill,
                    "target_role": mapping["target"],
                    "transferability_pct": mapping["transfer_pct"],
                })
                best_match_pct = max(best_match_pct, mapping["transfer_pct"])

    # 4. Find the best bridge course that closes any remaining gap
    gap_course = _find_best_bridge_course(skills, certs)

    # 5. Build context for reasoning text
    context = {
        "worker_name": worker.name,
        "worker_id": worker_id,
        "current_skills": skills,
        "certifications": certs,
        "adjacent_roles": adjacent,
        "skill_match_pct": best_match_pct or 0,
        "gap_course": gap_course.get("title", "a certified bridge course") if gap_course else "none required",
        "bridge_eligible": len(adjacent) > 0,
    }

    reasoning = generate_agent_reasoning("Skills Discovery Agent", context)

    logger.info("Skills Discovery complete for %s: %d adjacent roles found.", worker_id, len(adjacent))

    return {
        "agent": "Skills Discovery Agent",
        "worker_id": worker_id,
        "worker_name": worker.name,
        "verified_skills": skills,
        "verified_certifications": certs,
        "adjacent_capabilities": adjacent,
        "best_transferability_pct": best_match_pct,
        "recommended_bridge_course": gap_course,
        "bridge_eligible": len(adjacent) > 0,
        "reasoning": reasoning,
    }


def _find_best_bridge_course(skills: list[str], certs: list[str]) -> dict | None:
    """
    From the SAP Learning Hub catalog, picks the minimal course that:
    - is NOT already covered by an existing certification
    - addresses the most common skill gap for automation readiness
    """
    covered = set(certs)
    for course_code, course in COURSE_CATALOG.items():
        cert_awarded = course.get("cert_awarded", "")
        if cert_awarded and cert_awarded not in covered:
            # Prefer robotics safety as the canonical bridge for this plant scenario
            if "Robotics" in course["title"] or "Safety" in course["title"]:
                return {
                    "course_code": course_code,
                    "title": course["title"],
                    "hours": course["duration_hours"],
                    "cost_inr": course["cost_inr"],
                    "cert_awarded": cert_awarded,
                    "provider": "SAP Learning Hub (Student Edition)",
                }
    # fallback: return first uncovered course
    for course_code, course in COURSE_CATALOG.items():
        cert_awarded = course.get("cert_awarded", "")
        if cert_awarded and cert_awarded not in covered:
            return {
                "course_code": course_code,
                "title": course["title"],
                "hours": course["duration_hours"],
                "cost_inr": course["cost_inr"],
                "cert_awarded": cert_awarded,
                "provider": "SAP Learning Hub (Student Edition)",
            }
    return None
