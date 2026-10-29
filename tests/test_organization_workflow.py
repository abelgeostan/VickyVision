import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.project import Project
from app.models.task import Task
from app.models.approval import ApprovalRequest
from app.models.decision import DecisionRecord
from app.schemas.organization import (
    UserRequestClassification,
    ArchyProjectPlan,
    ElderReview,
    PAResponse,
    HumanApprovalSubmission,
)
from app.schemas.decision import DecisionRecordCreate
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.schemas.task import TaskCreate, TaskUpdate
from app.schemas.approval import ApprovalCreate, ApprovalDecision
from app.services.agent_service import AgentService
from app.services.project_service import ProjectService
from app.services.task_service import TaskService
from app.services.approval_service import ApprovalService
from app.services.decision_service import DecisionService
from app.services.memory_service import MemoryService
from app.services.workflow_engine import OrganizationalWorkflowEngine, extract_json_from_llm
from app.llm.base import BaseLLMProvider, LLMResponse


class MockLLM(BaseLLMProvider):
    """Predictable mock LLM for testing organizational workflows."""

    def __init__(self, responses: dict = None):
        self.responses = responses or {}

    def generate(self, prompt, model, system_prompt=None, options=None):
        for key, val in self.responses.items():
            if key in prompt or (system_prompt and key in system_prompt):
                return LLMResponse(content=val, model=model)
        # Default JSON response
        return LLMResponse(
            content='{"intent_type": "PROJECT", "summary": "Build network monitoring", "target_agent": "archy", "requires_planning": true, "requires_elder_review": true, "confidence": 0.95}',
            model=model,
        )

    def chat(self, messages, model, system_prompt=None, options=None):
        return LLMResponse(content="Acknowledged.", model=model)

    def check_health(self):
        return True

    def list_models(self):
        return ["mock-model"]


@pytest.fixture
def mock_engine(db_session: Session):
    AgentService.init_default_agents(db_session)
    mock_llm = MockLLM()
    return OrganizationalWorkflowEngine(llm_provider=mock_llm)


def test_extract_json_from_llm():
    """Verifies that markdown codeblocks and outer text are correctly stripped."""
    raw_md = '```json\n{"project_name": "Test Project", "status": "OK"}\n```'
    parsed = extract_json_from_llm(raw_md)
    assert parsed == {"project_name": "Test Project", "status": "OK"}

    raw_text = 'Sure, here is the JSON:\n{"key": "value"}\nHope this helps!'
    parsed2 = extract_json_from_llm(raw_text)
    assert parsed2 == {"key": "value"}


def test_user_request_classification(mock_engine, db_session: Session):
    """Tests PA's intent classification for questions vs project requests."""
    # Question
    res_q = mock_engine.classify_user_request(db_session, "What is the status of Vicky?")
    assert res_q.intent_type in ("QUESTION", "PROJECT")

    # Project
    res_p = mock_engine.classify_user_request(db_session, "I want to build a home network monitoring system.")
    assert res_p.intent_type == "PROJECT"
    assert res_p.requires_planning is True


def test_archy_plan_project_and_task_tree(mock_engine, db_session: Session):
    """Tests that Archy generates structured blueprint and persists milestone task tree."""
    proj = ProjectService.create_project(
        db_session,
        ProjectCreate(
            name="Network Monitor",
            description="Build network monitoring for home devices",
            status="IDEA",
            created_by="pa",
        ),
    )

    plan = mock_engine.archy_plan_project(db_session, project_id=proj.id, user_goal="Build network monitoring")
    assert isinstance(plan, ArchyProjectPlan)
    assert plan.project_name != ""
    assert len(plan.milestones) > 0

    # Verify Project state in DB
    db_session.refresh(proj)
    assert proj.status == "PLANNING"
    assert "proposed_architecture" in proj.metadata_json

    # Verify task tree in DB
    tasks = TaskService.list_tasks(db_session, project_id=proj.id)
    parent_tasks = [t for t in tasks if t.parent_task_id is None]
    child_tasks = [t for t in tasks if t.parent_task_id is not None]

    assert len(parent_tasks) > 0, "Milestones should exist as parent tasks"
    assert len(child_tasks) > 0, "Concrete tasks should exist under milestones"
    assert child_tasks[0].parent_task_id == parent_tasks[0].id


def test_elder_review_and_decision_record(mock_engine, db_session: Session):
    """Tests that Elder reviews the plan and records a persistent decision."""
    proj = ProjectService.create_project(
        db_session,
        ProjectCreate(
            name="Health Dashboard",
            description="Simple server dashboard",
            status="PLANNING",
            metadata_json={"proposed_architecture": "FastAPI + Docker Compose", "technology_choices": [{"choice": "Docker Compose"}]},
        ),
    )

    review = mock_engine.elder_review_plan(db_session, project_id=proj.id)
    assert isinstance(review, ElderReview)
    assert review.decision in ("APPROVE", "REVISE", "REJECT")

    # Verify Project state
    db_session.refresh(proj)
    assert proj.status == "REVIEW"

    # Verify Decision Record created
    decisions = DecisionService.list_decisions(db_session, project_id=proj.id)
    assert len(decisions) >= 1
    d = decisions[0]
    assert d.category == "ARCHITECTURE"
    assert d.proposed_by == "archy"
    assert d.reviewed_by == "elder"
    assert d.status in ("REVIEWED", "PROPOSED")


def test_pa_present_for_approval(mock_engine, db_session: Session):
    """Tests that PA transitions project to AWAITING_APPROVAL and creates ApprovalRequest."""
    proj = ProjectService.create_project(
        db_session,
        ProjectCreate(
            name="Backup Service",
            description="Automated nightly backups",
            status="REVIEW",
            metadata_json={"proposed_architecture": "BorgBackup + Docker", "elder_review": {"review_summary": "Low risk, highly recommended"}},
        ),
    )

    approval_req, pa_response = mock_engine.pa_present_for_approval(db_session, project_id=proj.id)
    assert approval_req.project_id == proj.id
    assert approval_req.status == "PENDING"
    assert pa_response.requires_human_approval is True
    assert pa_response.approval_id == approval_req.id

    db_session.refresh(proj)
    assert proj.status == "AWAITING_APPROVAL"


def test_human_approval_and_execution_lifecycle(db_session: Session, monkeypatch):
    """Tests the full human approval hand-off to execution, completion, and memory persistence."""
    mock_llm = MockLLM()
    engine = OrganizationalWorkflowEngine(llm_provider=mock_llm)

    proj = ProjectService.create_project(
        db_session,
        ProjectCreate(
            name="Vicky Metrics",
            description="Collect CPU and RAM metrics",
            status="AWAITING_APPROVAL",
            metadata_json={"proposed_architecture": "Python telemetry daemon"},
        ),
    )

    # Create approval request
    approval_req = ApprovalService.create_request(
        db_session,
        ApprovalCreate(
            requesting_agent_id="pa",
            project_id=proj.id,
            action=f"Approve project {proj.name}",
            reason="Elder approved architecture",
        ),
    )

    # Create task
    task = TaskService.create_task(
        db_session,
        TaskCreate(
            title="Inspect host metrics",
            description="Gather CPU and memory metrics",
            project_id=proj.id,
            assigned_to="techy",
            status="PENDING",
        ),
    )

    # Mock TechyAgentLoop so execution finishes cleanly without live server during unit test
    def mock_execute(*args, **kwargs):
        res = MagicMock()
        res.success = True
        res.status = "COMPLETED"
        res.steps_count = 2
        res.final_answer = "Metrics checked: 8 cores active, memory 4.2GB free."
        return res

    monkeypatch.setattr("app.services.techy_agent.TechyAgentLoop.execute_task", mock_execute)

    # Human approves
    pa_res = engine.handle_human_decision(
        db_session,
        approval_id=approval_req.id,
        decision_type="APPROVE",
        approved_by="user",
    )

    assert "PROJECT COMPLETED" in pa_res.message
    db_session.refresh(proj)
    assert proj.status == "COMPLETED"

    # Verify decision record updated
    decisions = DecisionService.list_decisions(db_session, project_id=proj.id)
    for d in decisions:
        assert d.status == "APPROVED"
        assert d.approved_by == "user"

    # Verify organizational memory created
    memories = MemoryService.get_organizational_memories(db_session, category="PROJECT_FACT")
    assert any("Vicky Metrics" in m.content for m in memories)


def test_human_rejection_and_change_request(mock_engine, db_session: Session):
    """Tests REJECT and REQUEST_CHANGES transitions."""
    proj = ProjectService.create_project(
        db_session,
        ProjectCreate(name="Risky Project", status="AWAITING_APPROVAL"),
    )
    req = ApprovalService.create_request(
        db_session,
        ApprovalCreate(requesting_agent_id="pa", project_id=proj.id, action="Execute", reason="Test"),
    )

    # Reject
    res_reject = mock_engine.handle_human_decision(db_session, approval_id=req.id, decision_type="REJECT", notes="Too risky")
    assert "rejected" in res_reject.message
    db_session.refresh(proj)
    assert proj.status == "REJECTED"

    # Request changes
    proj2 = ProjectService.create_project(
        db_session,
        ProjectCreate(name="Revision Project", status="AWAITING_APPROVAL"),
    )
    req2 = ApprovalService.create_request(
        db_session,
        ApprovalCreate(requesting_agent_id="pa", project_id=proj2.id, action="Execute", reason="Test"),
    )
    res_changes = mock_engine.handle_human_decision(
        db_session, approval_id=req2.id, decision_type="REQUEST_CHANGES", notes="Use SQLite instead of PostgreSQL"
    )
    assert "revised" in res_changes.message
    db_session.refresh(proj2)
    assert proj2.status == "PLANNING"


def test_decision_records_crud(db_session: Session):
    """Tests persistent decision records CRUD operations and filtering."""
    d = DecisionService.create_decision(
        db_session,
        DecisionRecordCreate(
            title="Database engine selection",
            category="ARCHITECTURE",
            decision="PostgreSQL 16",
            reason="ACID compliance and relational integrity",
            alternatives_considered=["SQLite", "MySQL"],
            risks_identified=["Higher RAM consumption"],
        ),
    )
    assert d.id is not None
    assert d.category == "ARCHITECTURE"

    fetched = DecisionService.get_decision(db_session, d.id)
    assert fetched.title == "Database engine selection"

    decisions = DecisionService.list_decisions(db_session, category="ARCHITECTURE")
    assert len(decisions) >= 1


def test_organizational_memory_categories(db_session: Session):
    """Tests the 5 canonical organizational memory categories."""
    categories = [
        "USER_PREFERENCE",
        "PROJECT_FACT",
        "ARCHITECTURAL_DECISION",
        "SERVER_FACT",
        "LESSON_LEARNED",
    ]
    for cat in categories:
        m = MemoryService.record_organizational_fact(
            db_session,
            category=cat,
            content=f"Important knowledge for {cat}",
            importance=8,
        )
        assert m.type == cat

    server_facts = MemoryService.get_organizational_memories(db_session, category="SERVER_FACT")
    assert len(server_facts) >= 1
    assert "SERVER_FACT" in server_facts[0].type


def test_api_org_endpoints(client: TestClient, db_session: Session, monkeypatch):
    """Tests the Phase 3 REST API endpoints (/api/org/*)."""
    # 1. Organization Status
    res_status = client.get("/api/org/status")
    assert res_status.status_code == 200
    data_status = res_status.json()
    assert "active_projects_count" in data_status
    assert "agents_status" in data_status

    # 2. Decision Records API
    res_dec = client.post(
        "/api/org/decisions",
        json={
            "title": "Use Nginx reverse proxy",
            "decision": "Nginx on port 80/443",
            "reason": "Standard TLS termination",
            "category": "INFRASTRUCTURE",
            "status": "APPROVED",
        },
    )
    assert res_dec.status_code == 200
    dec_id = res_dec.json()["id"]

    res_list = client.get("/api/org/decisions?category=INFRASTRUCTURE")
    assert res_list.status_code == 200
    assert any(item["id"] == dec_id for item in res_list.json())

    # 3. Chat with PA (End-to-End Initiation)
    # Mock LLM generation during API call
    def mock_process(*args, **kwargs):
        return PAResponse(
            message="Project proposal for Health Dashboard ready for review.",
            intent="PROJECT",
            action_taken="Archy designed blueprint, Elder approved architecture.",
            project_id="test-proj-123",
            approval_id="test-appr-456",
            requires_human_approval=True,
        )

    monkeypatch.setattr(
        "app.services.workflow_engine.OrganizationalWorkflowEngine.process_user_input",
        mock_process,
    )

    res_chat = client.post(
        "/api/org/chat",
        json={"message": "I want a health dashboard for Vicky"},
    )
    assert res_chat.status_code == 200
    chat_data = res_chat.json()
    assert chat_data["requires_human_approval"] is True
    assert chat_data["project_id"] == "test-proj-123"
