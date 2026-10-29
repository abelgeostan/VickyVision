from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.approval import ApprovalRequest
from app.schemas.approval import ApprovalCreate, ApprovalDecision
from app.services.event_service import EventService
from app.services.audit_service import AuditService
from app.core.logging import get_logger

logger = get_logger("approval_service")


class ApprovalService:
    @staticmethod
    def create_request(db: Session, approval_in: ApprovalCreate) -> ApprovalRequest:
        req = ApprovalRequest(
            requesting_agent_id=approval_in.requesting_agent_id,
            task_id=approval_in.task_id,
            project_id=approval_in.project_id,
            action=approval_in.action,
            reason=approval_in.reason,
            risk_level=approval_in.risk_level,
            status="PENDING",
            requested_at=datetime.now(timezone.utc),
        )
        db.add(req)
        db.commit()
        db.refresh(req)

        EventService.create_event(
            db,
            event_type="approval.requested",
            source="approval_service",
            related_agent_id=req.requesting_agent_id,
            related_task_id=req.task_id,
            related_project_id=req.project_id,
            payload={
                "approval_id": req.id,
                "project_id": req.project_id,
                "action": req.action,
                "risk_level": req.risk_level,
                "reason": req.reason,
            },
        )
        AuditService.log(
            db,
            action="approval.requested",
            agent_id=req.requesting_agent_id,
            task_id=req.task_id,
            project_id=req.project_id,
            reason=req.reason,
            details={"action": req.action, "risk_level": req.risk_level},
            result="PENDING",
        )
        return req

    @staticmethod
    def decide_request(db: Session, request_id: str, decision: ApprovalDecision) -> Optional[ApprovalRequest]:
        req = db.query(ApprovalRequest).filter(ApprovalRequest.id == request_id).first()
        if not req:
            return None

        status = decision.status.upper()
        if status not in ("APPROVED", "REJECTED", "CANCELLED", "EXPIRED", "REQUEST_CHANGES"):
            raise ValueError(f"Invalid status: {status}")

        req.status = status
        req.approved_by = decision.approved_by
        req.approved_at = datetime.now(timezone.utc)
        req.rejection_reason = decision.rejection_reason

        db.commit()
        db.refresh(req)

        event_type = f"approval.{status.lower()}"
        EventService.create_event(
            db,
            event_type=event_type,
            source="approval_service",
            related_agent_id=req.requesting_agent_id,
            related_task_id=req.task_id,
            related_project_id=req.project_id,
            payload={
                "approval_id": req.id,
                "project_id": req.project_id,
                "status": status,
                "decided_by": decision.approved_by,
                "rejection_reason": decision.rejection_reason,
            },
        )
        AuditService.log(
            db,
            action=event_type,
            agent_id=req.requesting_agent_id,
            task_id=req.task_id,
            project_id=req.project_id,
            approved_by=decision.approved_by,
            details={"action": req.action, "rejection_reason": decision.rejection_reason},
            result=status,
        )
        return req

    @staticmethod
    def get_request(db: Session, request_id: str) -> Optional[ApprovalRequest]:
        return db.query(ApprovalRequest).filter(ApprovalRequest.id == request_id).first()

    @staticmethod
    def list_requests(
        db: Session,
        status: Optional[str] = None,
        requesting_agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ApprovalRequest]:
        query = db.query(ApprovalRequest)
        if status:
            query = query.filter(ApprovalRequest.status == status)
        if requesting_agent_id:
            query = query.filter(ApprovalRequest.requesting_agent_id == requesting_agent_id)
        if task_id:
            query = query.filter(ApprovalRequest.task_id == task_id)
        if project_id:
            query = query.filter(ApprovalRequest.project_id == project_id)

        return query.order_by(desc(ApprovalRequest.requested_at)).offset(offset).limit(limit).all()
