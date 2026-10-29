from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.orchestrator import (
    RouteMessageRequest,
    OrchestratorResponse,
    DispatchTaskRequest,
    FlowStepRequest,
)
from app.services.orchestrator import AgentOrchestrator

router = APIRouter(prefix="/orchestrator", tags=["Orchestrator"])
orchestrator = AgentOrchestrator()


@router.post("/route", response_model=OrchestratorResponse)
def route_message(req: RouteMessageRequest, db: Session = Depends(get_db)):
    """Routes an interaction between agents or user and agent through the central orchestrator."""
    try:
        return orchestrator.route_message(
            db=db,
            sender_id=req.sender_id,
            receiver_id=req.receiver_id,
            content=req.content,
            message_type=req.message_type,
            task_id=req.task_id,
            project_id=req.project_id,
            invoke_agent=req.invoke_agent,
            metadata=req.metadata,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestration routing failed: {str(e)}",
        )


@router.post("/flow", response_model=OrchestratorResponse)
def execute_flow(req: FlowStepRequest, db: Session = Depends(get_db)):
    """
    Executes a standard organizational flow:
    - user_to_pa
    - pa_to_archy
    - archy_to_elder
    - elder_to_archy
    - archy_to_techy
    - techy_to_elder
    - techy_to_pa
    """
    try:
        return orchestrator.execute_flow_step(
            db=db,
            flow=req.flow,
            content=req.content,
            task_id=req.task_id,
            project_id=req.project_id,
            metadata=req.metadata,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Flow execution failed: {str(e)}",
        )


@router.post("/dispatch", response_model=OrchestratorResponse)
def dispatch_task(req: DispatchTaskRequest, db: Session = Depends(get_db)):
    """Dispatches a task to an assigned agent and notifies them through the orchestrator."""
    try:
        return orchestrator.dispatch_task(
            db=db,
            task_id=req.task_id,
            assigned_to=req.assigned_to,
            instruction=req.instruction,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task dispatch failed: {str(e)}",
        )
