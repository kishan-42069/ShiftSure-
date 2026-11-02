"""
Data shapes (Pydantic schemas) used by the API.
These define what data comes in and what goes out — like typed contracts.
"""

from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Any
from enum import Enum


# --------------------------------------------------------------------------- #
# Enums                                                                        #
# --------------------------------------------------------------------------- #

class Shift(str, Enum):
    MORNING = "MORNING"
    EVENING = "EVENING"
    NIGHT = "NIGHT"


class EmploymentType(str, Enum):
    PERMANENT = "PERMANENT"
    CONTRACT = "CONTRACT"


class Strategy(str, Enum):
    SUPERVISOR_BASELINE = "SUPERVISOR_BASELINE"
    COST_FOCUSED = "COST_FOCUSED"
    FAIRNESS_BALANCED = "FAIRNESS_BALANCED"


class PlanState(str, Enum):
    GENERATED = "GENERATED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class SolverStatus(str, Enum):
    OPTIMAL = "OPTIMAL"
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    TIMEOUT = "TIMEOUT"


# --------------------------------------------------------------------------- #
# Workers                                                                      #
# --------------------------------------------------------------------------- #

class SkillOut(BaseModel):
    skill_name: str
    proficiency: int  # 1–5
    verified: bool

    model_config = {"from_attributes": True}


class CertificationOut(BaseModel):
    cert_code: str
    is_valid: bool
    expiry_date: Optional[str] = None

    model_config = {"from_attributes": True}


class WorkerOut(BaseModel):
    id: str
    name: str
    role: str
    line_id: str
    shift: Shift
    employment_type: EmploymentType
    available_hours: float
    tenure_years: float
    skills: List[SkillOut] = []
    certifications: List[CertificationOut] = []

    model_config = {"from_attributes": True}


class CorrectionRequestIn(BaseModel):
    worker_id: str
    requested_change: str = Field(..., min_length=10)


class CorrectionRequestOut(BaseModel):
    id: int
    worker_id: str
    requested_change: str
    status: str
    reviewer_note: Optional[str] = None

    model_config = {"from_attributes": True}


# --------------------------------------------------------------------------- #
# Disruption Scenarios                                                         #
# --------------------------------------------------------------------------- #

class ScenarioCreateIn(BaseModel):
    name: str
    affected_line_id: str
    workload_reduction_pct: float = Field(..., ge=0.0, le=1.0)
    planning_period_hours: float = Field(40.0, ge=1.0)
    max_training_hours: float = Field(20.0, ge=0.0)
    fairness_weight: float = Field(0.35, ge=0.0, le=1.0)
    idle_disparity_threshold: float = Field(0.15, ge=0.0, le=1.0)

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Accept scenario_name as alias for name
            if "name" not in data and "scenario_name" in data:
                data["name"] = data["scenario_name"]
            # Accept affected_lines (list or string) as alias for affected_line_id
            if "affected_line_id" not in data and "affected_lines" in data:
                lines = data["affected_lines"]
                data["affected_line_id"] = lines[0] if isinstance(lines, list) and lines else str(lines)
        return data


class ScenarioOut(BaseModel):
    id: str
    name: str
    affected_line_id: str
    workload_reduction_pct: float
    planning_period_hours: float
    max_training_hours: float
    fairness_weight: float
    idle_disparity_threshold: float
    status: str

    model_config = {"from_attributes": True}


# --------------------------------------------------------------------------- #
# Allocation Plans & Assignments                                               #
# --------------------------------------------------------------------------- #

class AssignmentOut(BaseModel):
    worker_id: str
    worker_name: str
    task_id: str
    assigned_hours: float
    requires_training: bool
    training_course_id: Optional[str] = None
    training_hours: float
    training_cost_inr: float
    eligibility_proof: dict

    model_config = {"from_attributes": True}


class PlanOut(BaseModel):
    id: str
    scenario_id: str
    strategy: Strategy
    solver_status: SolverStatus
    state: PlanState
    objective_value: Optional[float]
    metrics: dict
    assignments: List[AssignmentOut] = []

    model_config = {"from_attributes": True}


class PlanComparisonOut(BaseModel):
    scenario_id: str
    plans: List[PlanOut]


class ApproveIn(BaseModel):
    manager_id: str = Field(..., description="Authorised manager identifier")


class RejectIn(BaseModel):
    manager_id: str
    reason: str = Field(..., min_length=5)


# --------------------------------------------------------------------------- #
# Fairness Reports                                                             #
# --------------------------------------------------------------------------- #

class FairnessReportOut(BaseModel):
    plan_id: str
    audit_status: str
    disparity_results: dict
    counterfactual_result: dict

    model_config = {"from_attributes": True}
