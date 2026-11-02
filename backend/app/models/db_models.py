"""
Database table definitions.
Each class here becomes one table in the SQLite database.
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean,
    ForeignKey, DateTime, Text, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Workers                                                                      #
# --------------------------------------------------------------------------- #

class Worker(Base):
    __tablename__ = "workers"

    id = Column(String, primary_key=True)           # e.g. "W-104"
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)           # e.g. "Assembly Specialist"
    line_id = Column(String, nullable=False)        # current production line
    shift = Column(String, nullable=False)          # "MORNING" | "EVENING" | "NIGHT"
    employment_type = Column(String, nullable=False)# "PERMANENT" | "CONTRACT"
    available_hours = Column(Float, nullable=False) # hours available this planning period
    tenure_years = Column(Float, default=0.0)

    skills = relationship("WorkerSkill", back_populates="worker", cascade="all, delete-orphan")
    certifications = relationship("WorkerCertification", back_populates="worker", cascade="all, delete-orphan")
    correction_requests = relationship("CorrectionRequest", back_populates="worker", cascade="all, delete-orphan")


class WorkerSkill(Base):
    __tablename__ = "worker_skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    worker_id = Column(String, ForeignKey("workers.id"), nullable=False)
    skill_name = Column(String, nullable=False)     # e.g. "Manual Assembly"
    proficiency = Column(Integer, nullable=False)   # 1 (beginner) – 5 (expert)
    verified = Column(Boolean, default=True)

    worker = relationship("Worker", back_populates="skills")


class WorkerCertification(Base):
    __tablename__ = "worker_certifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    worker_id = Column(String, ForeignKey("workers.id"), nullable=False)
    cert_code = Column(String, nullable=False)      # e.g. "ROBOTICS_SAFETY_L1"
    is_valid = Column(Boolean, default=True)
    expiry_date = Column(String, nullable=True)     # ISO date string

    worker = relationship("Worker", back_populates="certifications")


# --------------------------------------------------------------------------- #
# Production Lines & Tasks                                                     #
# --------------------------------------------------------------------------- #

class ProductionLine(Base):
    __tablename__ = "production_lines"

    id = Column(String, primary_key=True)           # e.g. "LINE-01"
    name = Column(String, nullable=False)
    supervisor_capacity = Column(Integer, default=8) # max workers per supervisor
    tasks = relationship("Task", back_populates="line", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True)           # e.g. "TASK-ROB-01"
    line_id = Column(String, ForeignKey("production_lines.id"), nullable=False)
    title = Column(String, nullable=False)
    required_headcount = Column(Integer, nullable=False)
    required_hours = Column(Float, nullable=False)  # hours per worker per period
    shift = Column(String, nullable=False)
    required_skills = Column(JSON, default=list)    # list of skill names
    mandatory_certs = Column(JSON, default=list)    # cert codes that CANNOT be waived
    training_bridge_permitted = Column(Boolean, default=False)
    training_bridge_cert = Column(String, nullable=True)  # cert awarded after bridge course

    line = relationship("ProductionLine", back_populates="tasks")


# --------------------------------------------------------------------------- #
# Disruption Scenarios                                                         #
# --------------------------------------------------------------------------- #

class DisruptionScenario(Base):
    __tablename__ = "disruption_scenarios"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    affected_line_id = Column(String, nullable=False)
    workload_reduction_pct = Column(Float, nullable=False)   # 0.0 – 1.0
    planning_period_hours = Column(Float, default=40.0)
    max_training_hours = Column(Float, default=20.0)
    fairness_weight = Column(Float, default=0.35)            # 0.0 = pure cost, 1.0 = pure fairness
    idle_disparity_threshold = Column(Float, default=0.15)   # 15% max allowed gap
    status = Column(String, default="DRAFT")                 # DRAFT | RUNNING | COMPLETE
    created_at = Column(DateTime, default=utcnow)

    plans = relationship("AllocationPlan", back_populates="scenario", cascade="all, delete-orphan")


# --------------------------------------------------------------------------- #
# Allocation Plans & Assignments                                               #
# --------------------------------------------------------------------------- #

class AllocationPlan(Base):
    __tablename__ = "allocation_plans"

    id = Column(String, primary_key=True)
    scenario_id = Column(String, ForeignKey("disruption_scenarios.id"), nullable=False)
    strategy = Column(String, nullable=False)   # "SUPERVISOR_BASELINE" | "COST_FOCUSED" | "FAIRNESS_BALANCED"
    solver_status = Column(String, nullable=False)  # "OPTIMAL" | "FEASIBLE" | "INFEASIBLE" | "TIMEOUT"
    state = Column(String, default="GENERATED")     # GENERATED | PENDING_APPROVAL | APPROVED | REJECTED
    objective_value = Column(Float, nullable=True)
    metrics = Column(JSON, default=dict)            # idle hours avoided, fill rate, costs, fairness
    created_at = Column(DateTime, default=utcnow)
    approved_by = Column(String, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    scenario = relationship("DisruptionScenario", back_populates="plans")
    assignments = relationship("Assignment", back_populates="plan", cascade="all, delete-orphan")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(String, ForeignKey("allocation_plans.id"), nullable=False)
    worker_id = Column(String, nullable=False)
    worker_name = Column(String, nullable=False)
    task_id = Column(String, nullable=False)
    assigned_hours = Column(Float, nullable=False)
    requires_training = Column(Boolean, default=False)
    training_course_id = Column(String, nullable=True)   # SAP Learning Hub course ID
    training_hours = Column(Float, default=0.0)
    training_cost_inr = Column(Float, default=0.0)
    eligibility_proof = Column(JSON, default=dict)

    plan = relationship("AllocationPlan", back_populates="assignments")


# --------------------------------------------------------------------------- #
# Fairness & Counterfactual Audit Records                                      #
# --------------------------------------------------------------------------- #

class FairnessReport(Base):
    __tablename__ = "fairness_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(String, nullable=False)
    audit_status = Column(String, nullable=False)   # "PASSED" | "PASSED_WITH_ADVISORY" | "FAILED"
    disparity_results = Column(JSON, default=dict)
    counterfactual_result = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor = Column(String, nullable=False)           # "SYSTEM" | "MANAGER:<id>" | "WORKER:<id>"
    action = Column(String, nullable=False)          # "PLAN_APPROVED" | "SKILL_CORRECTED" | ...
    entity_id = Column(String, nullable=False)       # the ID of the thing acted upon
    detail = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utcnow)


# --------------------------------------------------------------------------- #
# Worker Correction Requests                                                   #
# --------------------------------------------------------------------------- #

class CorrectionRequest(Base):
    __tablename__ = "correction_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    worker_id = Column(String, ForeignKey("workers.id"), nullable=False)
    requested_change = Column(Text, nullable=False)  # what the worker claims is wrong
    status = Column(String, default="PENDING")       # PENDING | APPROVED | REJECTED
    reviewer_note = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=utcnow)

    worker = relationship("Worker", back_populates="correction_requests")
