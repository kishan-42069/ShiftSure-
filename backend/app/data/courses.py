"""
SAP Learning Hub course catalog — curated for manufacturing reskilling.
These are the bridge courses workers can take to qualify for new roles.
All course codes follow SAP Learning Hub (Student Edition) naming conventions.
"""

# Each entry is one training course available to workers who are close to qualifying for a task.
COURSE_CATALOG = {
    "SAP-LH-ROB-101": {
        "id": "SAP-LH-ROB-101",
        "title": "Robotics Safety & Collaborative Arm Operation",
        "cert_awarded": "ROBOTICS_SAFETY_L1",
        "duration_hours": 8,
        "cost_inr": 4500,
        "provider": "SAP Learning Hub (Student Edition)",
        "syllabus_url": "https://learning.sap.com/courses/robotics-safety-collaborative",
        "description": (
            "Covers safe working procedures alongside industrial robotic arms, "
            "emergency stop protocols, and basic co-bot programming using SAP MII integration."
        ),
    },
    "SAP-LH-QC-201": {
        "id": "SAP-LH-QC-201",
        "title": "Automated Quality Control & Vision System Operation",
        "cert_awarded": "AUTO_QC_OPERATOR",
        "duration_hours": 12,
        "cost_inr": 6500,
        "provider": "SAP Learning Hub (Student Edition)",
        "syllabus_url": "https://learning.sap.com/courses/automated-qc-vision",
        "description": (
            "Trains operators to monitor automated vision-based quality inspection lines, "
            "interpret defect reports, and escalate anomalies using SAP Digital Manufacturing."
        ),
    },
    "SAP-LH-MAINT-101": {
        "id": "SAP-LH-MAINT-101",
        "title": "Preventive Maintenance for Automated Assembly Lines",
        "cert_awarded": "MAINT_TECH_L1",
        "duration_hours": 16,
        "cost_inr": 8000,
        "provider": "SAP Learning Hub (Student Edition)",
        "syllabus_url": "https://learning.sap.com/courses/preventive-maintenance-assembly",
        "description": (
            "Foundational preventive maintenance procedures for automated assembly machines, "
            "lubrication cycles, sensor calibration, and SAP PM work order integration."
        ),
    },
    "SAP-LH-FORKLIFT-101": {
        "id": "SAP-LH-FORKLIFT-101",
        "title": "Automated Guided Vehicle (AGV) & Forklift Safety",
        "cert_awarded": "AGV_OPERATOR",
        "duration_hours": 6,
        "cost_inr": 3000,
        "provider": "SAP Learning Hub (Student Edition)",
        "syllabus_url": "https://learning.sap.com/courses/agv-forklift-safety",
        "description": (
            "Certifies workers to safely operate and oversee Automated Guided Vehicles "
            "in a smart warehouse or production floor environment."
        ),
    },
    "SAP-LH-WELD-101": {
        "id": "SAP-LH-WELD-101",
        "title": "Robotic Welding Cell Safety & Basic Operation",
        "cert_awarded": "ROBO_WELD_SAFE",
        "duration_hours": 10,
        "cost_inr": 5500,
        "provider": "SAP Learning Hub (Student Edition)",
        "syllabus_url": "https://learning.sap.com/courses/robotic-welding-cell",
        "description": (
            "Safety procedures for working near robotic welding cells, fume exposure limits, "
            "arc flash protection, and basic cell parameter monitoring."
        ),
    },
}


def get_course(course_id: str) -> dict | None:
    """Returns course details for a given course ID, or None if not found."""
    return COURSE_CATALOG.get(course_id)


def list_courses() -> list[dict]:
    """Returns all available courses."""
    return list(COURSE_CATALOG.values())
