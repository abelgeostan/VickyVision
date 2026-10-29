from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.audit import AuditLogResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("", response_model=List[AuditLogResponse])
def list_audit_logs(
    action: Optional[str] = None,
    agent_id: Optional[str] = None,
    task_id: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Retrieve persistent audit trail for the organization."""
    return AuditService.list_logs(
        db,
        action=action,
        agent_id=agent_id,
        task_id=task_id,
        project_id=project_id,
        limit=limit,
        offset=offset,
    )


@router.get("/{log_id}", response_model=AuditLogResponse)
def get_audit_log(log_id: str, db: Session = Depends(get_db)):
    """Retrieve specific audit log entry by ID."""
    log_entry = AuditService.get_log(db, log_id)
    if not log_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Audit log entry '{log_id}' not found.")
    return log_entry
