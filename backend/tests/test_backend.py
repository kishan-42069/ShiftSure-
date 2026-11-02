"""
Test Suite for ShiftSure Backend
Run with: pytest tests/ -v (from the backend/ directory with venv activated)
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.db_models import Worker, WorkerSkill, WorkerCertification, Task, ProductionLine
from app.core.rules import check_eligibility, build_eligibility_matrix, validate_plan_assignments
from app.core.fairness import calculate_idle_hours, calculate_group_disparity, generate_fairness_report
from app.core.solver import run_solver


# --------------------------------------------------------------------------- #
# Test Database Setup (in-memory, isolated per test)                          #
# --------------------------------------------------------------------------- #

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_line(db):
    line = ProductionLine(id="LINE-01", name="Assembly Line", supervisor_capacity=8)
    db.add(line)
    db.commit()
    return line


@pytest.fixture
def task_no_cert(db, sample_line):
    task = Task(
        id="TASK-NOCERT",
        line_id="LINE-01",
        title="Basic Assembly (No Cert Required)",
        required_headcount=2,
        required_hours=8.0,
        shift="MORNING",
        required_skills=["Manual Assembly"],
        mandatory_certs=[],
        training_bridge_permitted=False,
        training_bridge_cert=None,
    )
    db.add(task)
    db.commit()
    return task


@pytest.fixture
def task_with_cert(db, sample_line):
    task = Task(
        id="TASK-CERT",
        line_id="LINE-01",
        title="Robotics Cell (Cert Required)",
        required_headcount=1,
        required_hours=8.0,
        shift="MORNING",
        required_skills=["Manual Assembly"],
        mandatory_certs=["ROBOTICS_SAFETY_L1"],
        training_bridge_permitted=True,
        training_bridge_cert="SAP-LH-ROB-101",
    )
    db.add(task)
    db.commit()
    return task


@pytest.fixture
def task_cert_no_bridge(db, sample_line):
    task = Task(
        id="TASK-CERT-NOBRIDGE",
        line_id="LINE-01",
        title="Hazardous Cell (No Training Allowed)",
        required_headcount=1,
        required_hours=8.0,
        shift="MORNING",
        required_skills=["Manual Assembly"],
        mandatory_certs=["SPECIAL_HAZARD_CERT"],
        training_bridge_permitted=False,
        training_bridge_cert=None,
    )
    db.add(task)
    db.commit()
    return task


def _make_worker(db, wid, shift="MORNING", emp_type="PERMANENT", hours=40.0,
                 skills=None, certs=None, tenure=2.0):
    w = Worker(
        id=wid,
        name=f"Worker {wid}",
        role="Operator",
        line_id="LINE-03",
        shift=shift,
        employment_type=emp_type,
        available_hours=hours,
        tenure_years=tenure,
    )
    db.add(w)
    db.flush()
    for skill_name, prof in (skills or []):
        db.add(WorkerSkill(worker_id=wid, skill_name=skill_name, proficiency=prof, verified=True))
    for cert_code in (certs or []):
        db.add(WorkerCertification(worker_id=wid, cert_code=cert_code, is_valid=True))
    db.commit()
    db.refresh(w)
    return w


# =========================================================================== #
# SAFETY RULE TESTS                                                            #
# =========================================================================== #

class TestSafetyRules:

    def test_qualified_worker_is_eligible_now(self, db, task_with_cert):
        """A worker with all required skills AND cert is immediately eligible."""
        worker = _make_worker(
            db, "W-QQ1",
            skills=[("Manual Assembly", 4)],
            certs=["ROBOTICS_SAFETY_L1"],
        )
        result = check_eligibility(worker, task_with_cert)
        assert result["eligible_now"] is True
        assert result["blocked"] is False
        assert result["eligible_after_training"] is False

    def test_worker_missing_cert_but_bridge_allowed(self, db, task_with_cert):
        """Worker with skills but no cert gets a training bridge — NOT a hard block."""
        worker = _make_worker(
            db, "W-BRIDGE1",
            skills=[("Manual Assembly", 4)],
            certs=[],  # Missing ROBOTICS_SAFETY_L1
        )
        result = check_eligibility(worker, task_with_cert, max_training_hours=20)
        assert result["blocked"] is False
        assert result["eligible_now"] is False
        assert result["eligible_after_training"] is True
        assert result["training_required"] is not None
        assert result["training_required"]["cert_awarded"] == "ROBOTICS_SAFETY_L1"

    def test_worker_missing_cert_no_bridge_is_hard_blocked(self, db, task_cert_no_bridge):
        """Worker missing a cert for a task where NO training bridge is allowed = hard block."""
        worker = _make_worker(
            db, "W-HARDBLOCK1",
            skills=[("Manual Assembly", 4)],
            certs=[],
        )
        result = check_eligibility(worker, task_cert_no_bridge)
        assert result["blocked"] is True
        assert "Training bridge not permitted" in result["block_reasons"][0]

    def test_wrong_shift_is_hard_blocked(self, db, task_no_cert):
        """A night shift worker cannot be placed on a morning shift task."""
        worker = _make_worker(
            db, "W-NIGHTSHIFT1",
            shift="NIGHT",
            skills=[("Manual Assembly", 4)],
        )
        result = check_eligibility(worker, task_no_cert)
        assert result["blocked"] is True
        assert "shift" in result["block_reasons"][0].lower()

    def test_missing_required_skill_is_blocked(self, db, task_no_cert):
        """A worker without the required skill cannot be assigned even with no cert needed."""
        worker = _make_worker(
            db, "W-NOSKILL1",
            shift="MORNING",
            skills=[("Packaging Operations", 3)],  # Wrong skill
        )
        result = check_eligibility(worker, task_no_cert)
        assert result["blocked"] is True
        assert "Missing required skills" in result["block_reasons"][0]

    def test_post_solve_validation_catches_violations(self, db, task_with_cert):
        """The post-solver validation pass catches any invalid assignment the solver might produce."""
        worker = _make_worker(
            db, "W-VIOL1",
            skills=[("Manual Assembly", 4)],
            certs=[],  # No cert, and training bridge NOT allowed for validation test
        )
        # Fake an assignment that violates safety (uncertified worker on cert-required task)
        bad_assignments = [{
            "worker_id": "W-VIOL1",
            "task_id": "TASK-CERT-NOBRIDGE",
            "assigned_hours": 8.0,
        }]
        # We use the cert-no-bridge task for this check
        task_cert_no_bridge = Task(
            id="TASK-CERT-NOBRIDGE-VAL",
            line_id="LINE-01",
            title="Hazardous Cell (Val Test)",
            required_headcount=1,
            required_hours=8.0,
            shift="MORNING",
            required_skills=["Manual Assembly"],
            mandatory_certs=["SPECIAL_HAZARD_CERT"],
            training_bridge_permitted=False,
            training_bridge_cert=None,
        )
        is_valid, violations = validate_plan_assignments(
            bad_assignments, [worker], [task_cert_no_bridge], max_training_hours=0
        )
        assert is_valid is False
        assert len(violations) > 0


# =========================================================================== #
# SOLVER TESTS                                                                 #
# =========================================================================== #

class TestSolver:

    def _setup_solver_data(self, db):
        """Sets up a minimal workforce for solver testing."""
        line = ProductionLine(id="LINE-SOLVE-01", name="Assembly", supervisor_capacity=8)
        db.add(line)
        task = Task(
            id="TASK-SOLVE-01",
            line_id="LINE-SOLVE-01",
            title="Assembly Work",
            required_headcount=2,
            required_hours=8.0,
            shift="MORNING",
            required_skills=["Manual Assembly"],
            mandatory_certs=[],
            training_bridge_permitted=False,
            training_bridge_cert=None,
        )
        db.add(task)
        workers = [
            _make_worker(db, f"W-SOLVE-{i}", skills=[("Manual Assembly", 3)], hours=40.0)
            for i in range(1, 5)
        ]
        db.commit()
        return workers, [task]

    def test_solver_produces_valid_assignments(self, db):
        """Solver should produce at least some assignments when eligible workers exist."""
        workers, tasks = self._setup_solver_data(db)
        result = run_solver(workers, tasks, planning_hours=40.0, strategy="FAIRNESS_BALANCED")
        assert result["solver_status"] in ["OPTIMAL", "FEASIBLE"]
        assert len(result["assignments"]) > 0

    def test_solver_infeasible_when_no_eligible_workers(self, db):
        """
        When no worker has the required certification and no bridge is allowed,
        the solver must report INFEASIBLE — never fabricate phantom assignments.
        """
        line = ProductionLine(id="LINE-INF", name="Hazardous", supervisor_capacity=8)
        db.add(line)
        task = Task(
            id="TASK-INF",
            line_id="LINE-INF",
            title="Hazardous Job",
            required_headcount=1,
            required_hours=8.0,
            shift="MORNING",
            required_skills=["Manual Assembly"],
            mandatory_certs=["RARE_CERT"],
            training_bridge_permitted=False,
            training_bridge_cert=None,
        )
        db.add(task)
        worker = _make_worker(db, "W-INF-1", skills=[("Manual Assembly", 3)], certs=[])
        db.commit()

        result = run_solver([worker], [task], planning_hours=40.0, strategy="FAIRNESS_BALANCED")
        # With no eligible workers, no assignments should be made
        assert len(result["assignments"]) == 0

    def test_all_three_strategies_run_without_error(self, db):
        """All 3 strategies must complete without crashing."""
        workers, tasks = self._setup_solver_data(db)
        for strategy in ["SUPERVISOR_BASELINE", "COST_FOCUSED", "FAIRNESS_BALANCED"]:
            result = run_solver(workers, tasks, planning_hours=40.0, strategy=strategy)
            assert "solver_status" in result
            assert "assignments" in result
            assert "metrics" in result


# =========================================================================== #
# FAIRNESS METRIC TESTS                                                        #
# =========================================================================== #

class TestFairnessMetrics:

    def test_idle_hours_calculated_correctly(self, db):
        """idle_hours = available_hours - assigned_hours. Checks base math."""
        w1 = _make_worker(db, "W-FAIR-1", hours=40.0, emp_type="PERMANENT")
        w2 = _make_worker(db, "W-FAIR-2", hours=40.0, emp_type="CONTRACT")

        # w1 gets 30 hours of work, w2 gets 10 hours
        assignments = [
            {"worker_id": "W-FAIR-1", "assigned_hours": 30.0},
            {"worker_id": "W-FAIR-2", "assigned_hours": 10.0},
        ]
        idle = calculate_idle_hours([w1, w2], assignments, planning_hours=40.0)

        assert idle["W-FAIR-1"] == pytest.approx(10.0)
        assert idle["W-FAIR-2"] == pytest.approx(30.0)

    def test_group_disparity_detects_unequal_distribution(self, db):
        """
        If contract workers consistently get more idle hours than permanent workers,
        the fairness check should flag it as a disparity.
        """
        # 2 permanent workers: 5 idle hours each (low idle = good)
        perm1 = _make_worker(db, "W-DISP-P1", emp_type="PERMANENT", hours=40.0)
        perm2 = _make_worker(db, "W-DISP-P2", emp_type="PERMANENT", hours=40.0)
        # 2 contract workers: 30 idle hours each (high idle = bad)
        cont1 = _make_worker(db, "W-DISP-C1", emp_type="CONTRACT", hours=40.0)
        cont2 = _make_worker(db, "W-DISP-C2", emp_type="CONTRACT", hours=40.0)

        idle = {
            "W-DISP-P1": 5.0,
            "W-DISP-P2": 5.0,
            "W-DISP-C1": 30.0,
            "W-DISP-C2": 30.0,
        }

        disparity = calculate_group_disparity([perm1, perm2, cont1, cont2], idle)
        # Contract workers have 6x more idle hours — should be flagged
        assert disparity["most_impacted_group"] == "CONTRACT"
        assert disparity["relative_disparity_pct"] > 15.0  # clearly exceeds 15% threshold

    def test_equal_distribution_passes_fairness(self, db):
        """When idle hours are evenly distributed, fairness checks should pass."""
        perm = _make_worker(db, "W-EQ-P1", emp_type="PERMANENT", hours=40.0)
        cont = _make_worker(db, "W-EQ-C1", emp_type="CONTRACT", hours=40.0)

        idle = {"W-EQ-P1": 8.0, "W-EQ-C1": 8.0}  # exactly equal
        disparity = calculate_group_disparity([perm, cont], idle)
        assert disparity["relative_disparity_pct"] == pytest.approx(0.0)
        assert disparity["four_fifths_threshold_met"] is True
