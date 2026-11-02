"""
Simulated Factory Workforce & Task Dataset
Plant: Bengaluru Smart Auto Components Plant (Plant BLR-01)
Workers: 60 (across 3 production lines and 3 shifts)
Lines: LINE-01 (Assembly), LINE-02 (Quality & Maintenance), LINE-03 (Packaging — disrupted)

This module seeds the database with realistic, fictional worker data.
NO real employee information is used or implied.
"""

import uuid
from sqlalchemy.orm import Session
from app.models.db_models import (
    Worker, WorkerSkill, WorkerCertification,
    ProductionLine, Task
)

# --------------------------------------------------------------------------- #
# Production Lines                                                             #
# --------------------------------------------------------------------------- #

LINES = [
    {"id": "LINE-01", "name": "Assembly Line (Smart Components)", "supervisor_capacity": 8},
    {"id": "LINE-02", "name": "Quality & Maintenance Line", "supervisor_capacity": 8},
    {"id": "LINE-03", "name": "Packaging Line (DISRUPTED — Automated)", "supervisor_capacity": 8},
]

# --------------------------------------------------------------------------- #
# Open Tasks (jobs available AFTER disruption on LINE-03)                     #
# --------------------------------------------------------------------------- #

TASKS = [
    # Assembly Line — 3 open roles after surge demand
    {
        "id": "TASK-ASM-01",
        "line_id": "LINE-01",
        "title": "Automated Pick-and-Place Quality Checker",
        "required_headcount": 3,
        "required_hours": 32.0,
        "shift": "MORNING",
        "required_skills": ["Manual Assembly", "Quality Inspection"],
        "mandatory_certs": ["ROBOTICS_SAFETY_L1"],
        "training_bridge_permitted": True,
        "training_bridge_cert": "SAP-LH-ROB-101",
    },
    {
        "id": "TASK-ASM-02",
        "line_id": "LINE-01",
        "title": "Component Sub-Assembly Specialist",
        "required_headcount": 2,
        "required_hours": 40.0,
        "shift": "MORNING",
        "required_skills": ["Manual Assembly"],
        "mandatory_certs": [],
        "training_bridge_permitted": False,
        "training_bridge_cert": None,
    },
    {
        "id": "TASK-ASM-03",
        "line_id": "LINE-01",
        "title": "Evening Shift Assembly Operator",
        "required_headcount": 2,
        "required_hours": 40.0,
        "shift": "EVENING",
        "required_skills": ["Manual Assembly"],
        "mandatory_certs": [],
        "training_bridge_permitted": False,
        "training_bridge_cert": None,
    },
    # Quality Line — 4 open technical roles
    {
        "id": "TASK-QC-01",
        "line_id": "LINE-02",
        "title": "Vision System Quality Inspector",
        "required_headcount": 2,
        "required_hours": 32.0,
        "shift": "MORNING",
        "required_skills": ["Quality Inspection"],
        "mandatory_certs": ["AUTO_QC_OPERATOR"],
        "training_bridge_permitted": True,
        "training_bridge_cert": "SAP-LH-QC-201",
    },
    {
        "id": "TASK-QC-02",
        "line_id": "LINE-02",
        "title": "Manual Quality Spot Check (No Cert Required)",
        "required_headcount": 3,
        "required_hours": 24.0,
        "shift": "MORNING",
        "required_skills": ["Quality Inspection"],
        "mandatory_certs": [],
        "training_bridge_permitted": False,
        "training_bridge_cert": None,
    },
    {
        "id": "TASK-QC-03",
        "line_id": "LINE-02",
        "title": "Night Shift Quality Monitor",
        "required_headcount": 2,
        "required_hours": 40.0,
        "shift": "NIGHT",
        "required_skills": ["Quality Inspection"],
        "mandatory_certs": [],
        "training_bridge_permitted": False,
        "training_bridge_cert": None,
    },
    {
        "id": "TASK-MAINT-01",
        "line_id": "LINE-02",
        "title": "Preventive Maintenance Technician",
        "required_headcount": 2,
        "required_hours": 40.0,
        "shift": "MORNING",
        "required_skills": ["Machine Operation", "Basic Maintenance"],
        "mandatory_certs": ["MAINT_TECH_L1"],
        "training_bridge_permitted": True,
        "training_bridge_cert": "SAP-LH-MAINT-101",
    },
]

# --------------------------------------------------------------------------- #
# Workers (60 fictional workers)                                               #
# --------------------------------------------------------------------------- #

def _build_workers() -> list[dict]:
    workers = []

    # ── LINE-03 Packaging Line: 20 workers (DISRUPTED) ──────────────────── #
    # 5 key workers for demo, 15 additional for dataset realism

    line3_key = [
        # Our primary demo persona
        {
            "id": "W-104",
            "name": "Priya Sharma",
            "role": "Senior Packaging & Assembly Specialist",
            "line_id": "LINE-03",
            "shift": "MORNING",
            "employment_type": "PERMANENT",
            "available_hours": 40.0,
            "tenure_years": 5.2,
            "skills": [
                ("Manual Assembly", 4),
                ("Quality Inspection", 3),
                ("Packaging Operations", 5),
            ],
            "certs": [],  # Missing ROBOTICS_SAFETY_L1 — needs SAP-LH-ROB-101 bridge
        },
        {
            "id": "W-105",
            "name": "Ravi Kumar",
            "role": "Packaging Operator",
            "line_id": "LINE-03",
            "shift": "MORNING",
            "employment_type": "PERMANENT",
            "available_hours": 40.0,
            "tenure_years": 3.8,
            "skills": [
                ("Packaging Operations", 4),
                ("Manual Assembly", 2),
            ],
            "certs": [],
        },
        {
            "id": "W-106",
            "name": "Sunita Bai",
            "role": "Packaging Operator",
            "line_id": "LINE-03",
            "shift": "MORNING",
            "employment_type": "CONTRACT",
            "available_hours": 40.0,
            "tenure_years": 1.1,
            "skills": [
                ("Packaging Operations", 3),
                ("Quality Inspection", 2),
            ],
            "certs": [],
        },
        {
            "id": "W-107",
            "name": "Deepak Nair",
            "role": "Senior Packaging Technician",
            "line_id": "LINE-03",
            "shift": "EVENING",
            "employment_type": "PERMANENT",
            "available_hours": 40.0,
            "tenure_years": 7.4,
            "skills": [
                ("Packaging Operations", 5),
                ("Machine Operation", 3),
                ("Basic Maintenance", 2),
            ],
            "certs": [],
        },
        {
            "id": "W-108",
            "name": "Kavitha Reddy",
            "role": "Packaging Operator",
            "line_id": "LINE-03",
            "shift": "EVENING",
            "employment_type": "CONTRACT",
            "available_hours": 40.0,
            "tenure_years": 0.8,
            "skills": [
                ("Packaging Operations", 3),
            ],
            "certs": [],
        },
    ]

    # 15 more LINE-03 workers
    for i in range(1, 16):
        emp = "PERMANENT" if i % 3 != 0 else "CONTRACT"
        shift = ["MORNING", "EVENING", "NIGHT"][i % 3]
        skill_lvl = (i % 4) + 1
        line3_key.append({
            "id": f"W-1{10 + i}",
            "name": f"Worker LINE3-{i:02d}",
            "role": "Packaging Operator",
            "line_id": "LINE-03",
            "shift": shift,
            "employment_type": emp,
            "available_hours": 40.0,
            "tenure_years": round(i * 0.6, 1),
            "skills": [("Packaging Operations", skill_lvl)],
            "certs": [],
        })

    # ── LINE-01 Assembly Line: 20 workers ───────────────────────────────── #
    line1_workers = []
    for i in range(1, 21):
        emp = "PERMANENT" if i <= 14 else "CONTRACT"
        shift = ["MORNING", "EVENING", "NIGHT"][i % 3]
        has_robot_cert = i <= 8  # first 8 workers have the robotics cert
        certs = [("ROBOTICS_SAFETY_L1", True)] if has_robot_cert else []
        line1_workers.append({
            "id": f"W-2{i:02d}",
            "name": f"Assembly Worker A-{i:02d}",
            "role": "Assembly Technician",
            "line_id": "LINE-01",
            "shift": shift,
            "employment_type": emp,
            "available_hours": 32.0 if i % 5 == 0 else 40.0,
            "tenure_years": round(i * 0.8, 1),
            "skills": [
                ("Manual Assembly", min((i % 5) + 1, 5)),
                ("Quality Inspection", min((i % 3) + 1, 5)),
            ],
            "certs": certs,
        })

    # ── LINE-02 Quality & Maintenance: 20 workers ───────────────────────── #
    line2_workers = []
    for i in range(1, 21):
        emp = "PERMANENT" if i <= 15 else "CONTRACT"
        shift = ["MORNING", "EVENING", "NIGHT"][i % 3]
        has_qc_cert = i <= 6
        has_maint_cert = i in [7, 8, 9]
        certs = []
        if has_qc_cert:
            certs.append(("AUTO_QC_OPERATOR", True))
        if has_maint_cert:
            certs.append(("MAINT_TECH_L1", True))
        line2_workers.append({
            "id": f"W-3{i:02d}",
            "name": f"Quality Worker Q-{i:02d}",
            "role": "Quality Inspector",
            "line_id": "LINE-02",
            "shift": shift,
            "employment_type": emp,
            "available_hours": 40.0,
            "tenure_years": round(i * 1.1, 1),
            "skills": [
                ("Quality Inspection", min((i % 5) + 1, 5)),
                ("Basic Maintenance", min((i % 3) + 1, 5)),
                ("Machine Operation", min((i % 4) + 1, 5)),
            ],
            "certs": certs,
        })

    workers.extend(line3_key)
    workers.extend(line1_workers)
    workers.extend(line2_workers)
    return workers


# --------------------------------------------------------------------------- #
# Seeding Function                                                             #
# --------------------------------------------------------------------------- #

def seed_database(db: Session, force: bool = False) -> None:
    """
    Loads all workers, lines, and tasks into the database.
    Runs only once unless force=True (which clears and reseeds).
    """
    if force:
        # Clear existing data in the right dependency order
        db.query(WorkerSkill).delete()
        db.query(WorkerCertification).delete()
        db.query(Worker).delete()
        db.query(Task).delete()
        db.query(ProductionLine).delete()
        db.commit()

    # Skip if already seeded
    if db.query(Worker).count() > 0:
        return

    # 1. Insert production lines
    for line_data in LINES:
        db.add(ProductionLine(**line_data))

    # 2. Insert tasks
    for task_data in TASKS:
        db.add(Task(**task_data))

    # 3. Insert workers with skills and certifications
    for w in _build_workers():
        worker = Worker(
            id=w["id"],
            name=w["name"],
            role=w["role"],
            line_id=w["line_id"],
            shift=w["shift"],
            employment_type=w["employment_type"],
            available_hours=w["available_hours"],
            tenure_years=w["tenure_years"],
        )
        db.add(worker)
        db.flush()  # get the worker.id into DB before adding relations

        for skill_name, proficiency in w.get("skills", []):
            db.add(WorkerSkill(
                worker_id=worker.id,
                skill_name=skill_name,
                proficiency=proficiency,
                verified=True,
            ))

        for cert_code, is_valid in w.get("certs", []):
            db.add(WorkerCertification(
                worker_id=worker.id,
                cert_code=cert_code,
                is_valid=is_valid,
            ))

    db.commit()
    print(f"✅ Seed complete: {len(_build_workers())} workers, {len(TASKS)} tasks, {len(LINES)} lines")
