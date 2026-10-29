from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.execution.factory import get_execution_provider
from app.tools.registry import get_tool_registry
from app.services.techy_agent import TechyAgentLoop
from app.services.server_discovery import ServerDiscoveryService
from app.services.task_service import TaskService
from app.services.event_service import EventService
from app.services.audit_service import AuditService
from app.schemas.techy import (
    TechyExecuteRequest,
    TechyExecuteResponse,
    ToolExecuteRequest,
    ToolExecuteResponse,
    ServerDiscoveryResponse,
)

router = APIRouter(prefix="/techy", tags=["Techy Autonomous Engineer"])


@router.post("/execute", response_model=TechyExecuteResponse)
def execute_techy_task(
    req: TechyExecuteRequest,
    db: Session = Depends(get_db),
):
    """
    Triggers an autonomous multi-step execution loop for TECHY on the VICKY server.
    Techy inspects state, executes necessary tools, verifies results, and completes the task.
    """
    loop = TechyAgentLoop()
    try:
        return loop.execute_task(
            db=db,
            instruction=req.instruction,
            task_id=req.task_id,
            project_id=req.project_id,
            max_steps=req.max_steps,
            timeout_seconds=req.timeout_seconds,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Techy autonomous execution failed: {str(e)}",
        )


@router.post("/tool", response_model=ToolExecuteResponse)
def execute_single_tool(
    req: ToolExecuteRequest,
    db: Session = Depends(get_db),
):
    """Directly executes a single real tool on the VICKY server runtime."""
    registry = get_tool_registry()
    provider = get_execution_provider()

    tool = registry.get(req.tool_name)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{req.tool_name}' not found. Available: {', '.join(registry.list_tools())}",
        )

    res = registry.execute(req.tool_name, req.args, provider)

    EventService.create_event(
        db,
        event_type="techy.direct_tool_executed",
        source="api",
        related_agent_id="techy",
        payload={"tool": req.tool_name, "success": res.success},
    )
    AuditService.log(
        db,
        action=f"techy.direct_tool.{req.tool_name}",
        agent_id="techy",
        details={"args": req.args, "success": res.success},
        result="SUCCESS" if res.success else "FAILED",
    )

    return ToolExecuteResponse(
        tool_name=req.tool_name,
        success=res.success,
        data=res.data,
        raw_output=res.raw_output,
        error=res.error,
        duration_ms=res.duration_ms,
    )


@router.get("/tools")
def list_available_tools():
    """Returns catalog of all registered tools and their input schemas."""
    registry = get_tool_registry()
    return {
        "count": len(registry.list_tools()),
        "tools": registry.get_schemas(),
    }


@router.get("/discovery", response_model=ServerDiscoveryResponse)
def get_server_discovery(
    force_refresh: bool = Query(default=False, description="Force a live re-inspection of the host"),
    db: Session = Depends(get_db),
):
    """Retrieve discovered host specs, resources, network IPs, and Docker status."""
    provider = get_execution_provider()
    discovery = ServerDiscoveryService.get_discovery(provider=provider, db=db, force_refresh=force_refresh)
    return ServerDiscoveryResponse(discovery=discovery, cached=not force_refresh)


@router.get("/runs/{task_id}")
def get_techy_run_details(task_id: str, db: Session = Depends(get_db)):
    """Retrieve execution history, actions, and outputs for a Techy task."""
    task = TaskService.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' not found.")

    return {
        "task_id": task.id,
        "title": task.title,
        "status": task.status,
        "progress": task.progress,
        "assigned_to": task.assigned_to,
        "created_at": task.created_at,
        "started_at": task.started_at,
        "completed_at": task.completed_at,
        "result": task.result,
        "error": task.error,
    }
