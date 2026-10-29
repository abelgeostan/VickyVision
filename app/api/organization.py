from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.organization import (
    PARequestInput,
    PAResponse,
    ArchyProjectPlan,
    ElderReview,
    HumanApprovalSubmission,
    ProjectTimelineItem,
    OrganizationStatus,
)
from app.schemas.decision import (
    DecisionRecordCreate,
    DecisionRecordResponse,
    DecisionRecordUpdate,
)
from app.services.workflow_engine import OrganizationalWorkflowEngine
from app.services.decision_service import DecisionService
from app.services.project_service import ProjectService
from app.services.approval_service import ApprovalService
from app.core.logging import get_logger

logger = get_logger("org_api")
router = APIRouter(prefix="/org", tags=["organizational-workflow"])
workflow_engine = OrganizationalWorkflowEngine()


@router.post("/chat", response_model=PAResponse, summary="Send message/goal to PA (Primary Human Interface)")
def chat_with_pa(
    payload: PARequestInput,
    db: Session = Depends(get_db),
):
    """
    Primary interface between human operator and VICKY OS:
    1. PA classifies intent.
    2. If question or simple task, answers directly.
    3. If project, Archy designs structured blueprint, Elder reviews architecture,
       and PA presents the final proposal for human approval.
    """
    try:
        response = workflow_engine.process_user_input(
            db=db,
            user_message=payload.message,
            project_id=payload.project_id,
        )
        return response
    except Exception as e:
        logger.error(f"Error in chat_with_pa: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Organizational workflow error: {str(e)}",
        )


@router.post("/projects/plan", response_model=ArchyProjectPlan, summary="Archy Blueprint Planning")
def archy_plan_project(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """Directly invokes Archy to create a structured project plan with milestones and task tree."""
    user_goal = payload.get("user_goal")
    project_id = payload.get("project_id")
    if not user_goal:
        raise HTTPException(status_code=400, detail="Field 'user_goal' is required.")

    if not project_id:
        proj = ProjectService.create_project(
            db,
            ProjectCreate(
                name=user_goal[:50],
                description=user_goal,
                status="IDEA",
                created_by="archy",
                objectives=[user_goal],
            ),
        )
        project_id = proj.id

    try:
        plan = workflow_engine.archy_plan_project(db, project_id=project_id, user_goal=user_goal)
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/review", response_model=ElderReview, summary="Elder Architecture Review")
def elder_review_project(
    project_id: str,
    db: Session = Depends(get_db),
):
    """Directly invokes Elder to review an existing project blueprint across 9 dimensions."""
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

    try:
        review = workflow_engine.elder_review_plan(db, project_id=project_id)
        return review
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approvals/{approval_id}/decide", response_model=PAResponse, summary="Submit Human Approval Decision")
def submit_human_decision(
    approval_id: str,
    payload: HumanApprovalSubmission,
    db: Session = Depends(get_db),
):
    """
    Submits human authority decision (APPROVE, REJECT, or REQUEST_CHANGES):
    - When APPROVED, Archy hands tasks to Techy, Techy executes on VICKY server, verifies results, and PA reports outcome.
    - When REJECTED, project is cancelled.
    - When REQUEST_CHANGES, project returns to Archy for revision.
    """
    try:
        response = workflow_engine.handle_human_decision(
            db=db,
            approval_id=approval_id,
            decision_type=payload.decision,
            notes=payload.notes,
            approved_by=payload.approved_by,
        )
        return response
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")


@router.get("/decisions", response_model=List[DecisionRecordResponse], summary="List Decision Records")
def list_decisions(
    project_id: Optional[str] = None,
    category: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Retrieves persistent architectural and organizational decision records."""
    return DecisionService.list_decisions(
        db=db,
        project_id=project_id,
        category=category,
        status=status_filter,
        limit=limit,
        offset=offset,
    )


@router.post("/decisions", response_model=DecisionRecordResponse, summary="Create Decision Record")
def create_decision(
    payload: DecisionRecordCreate,
    db: Session = Depends(get_db),
):
    """Creates a new persistent decision record."""
    return DecisionService.create_decision(db, payload)


@router.get("/decisions/{decision_id}", response_model=DecisionRecordResponse, summary="Get Decision Record")
def get_decision(
    decision_id: str,
    db: Session = Depends(get_db),
):
    record = DecisionService.get_decision(db, decision_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Decision {decision_id} not found.")
    return record


@router.get("/projects/{project_id}/timeline", response_model=List[ProjectTimelineItem], summary="Get Project Timeline")
def get_project_timeline(
    project_id: str,
    db: Session = Depends(get_db),
):
    """Returns unified chronological timeline of events, decisions, approvals, and task updates for a project."""
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")
    return workflow_engine.get_project_timeline(db, project_id=project_id)


@router.get("/status", response_model=OrganizationStatus, summary="Get Organization Pulse (PA Overview)")
def get_organization_status(
    db: Session = Depends(get_db),
):
    """Returns high-level status of the entire AI organization: active projects, pending approvals, running tasks, agent health."""
    return workflow_engine.get_organization_status(db)
