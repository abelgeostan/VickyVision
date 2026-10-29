from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.approval import ApprovalCreate, ApprovalDecision, ApprovalResponse
from app.services.approval_service import ApprovalService

router = APIRouter(prefix="/approvals", tags=["Approvals"])


@router.get("", response_model=List[ApprovalResponse])
def list_approvals(
    status: Optional[str] = None,
    requesting_agent_id: Optional[str] = None,
    task_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List approval requests (e.g. for PA to present to user)."""
    return ApprovalService.list_requests(
        db,
        status=status,
        requesting_agent_id=requesting_agent_id,
        task_id=task_id,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=ApprovalResponse, status_code=status.HTTP_201_CREATED)
def create_approval_request(req_in: ApprovalCreate, db: Session = Depends(get_db)):
    """Agent creates an approval request before high-risk or external actions."""
    return ApprovalService.create_request(db, req_in)


@router.get("/{approval_id}", response_model=ApprovalResponse)
def get_approval_request(approval_id: str, db: Session = Depends(get_db)):
    """Retrieve an approval request by ID."""
    req = ApprovalService.get_request(db, approval_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Approval request '{approval_id}' not found.")
    return req


@router.post("/{approval_id}/decision", response_model=ApprovalResponse)
def decide_approval(approval_id: str, decision: ApprovalDecision, db: Session = Depends(get_db)):
    """Approve or reject a pending request."""
    try:
        updated = ApprovalService.decide_request(db, approval_id, decision)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Approval request '{approval_id}' not found.")
    return updated
