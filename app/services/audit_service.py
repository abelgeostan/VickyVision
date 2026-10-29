from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.audit import AuditLog
from app.core.logging import get_logger

logger = get_logger("audit_service")


class AuditService:
    @staticmethod
    def log(
        db: Session,
        action: str,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        task_id: Optional[str] = None,
        project_id: Optional[str] = None,
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        result: Optional[str] = None,
        approved_by: Optional[str] = None,
        source: str = "system",
    ) -> AuditLog:
        """Records an auditable operation into persistent storage."""
        entry = AuditLog(
            action=action,
            agent_id=agent_id,
            user_id=user_id,
            task_id=task_id,
            project_id=project_id,
            reason=reason,
            details=details or {},
            result=result,
            approved_by=approved_by,
            source=source,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)

        logger.info(
            f"Audit log recorded: action={action} agent={agent_id} result={result}",
            extra={
                "component": "audit",
                "agent": agent_id,
                "task": task_id,
                "event": action,
            },
        )
        return entry

    @staticmethod
    def list_logs(
        db: Session,
        action: Optional[str] = None,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLog]:
        query = db.query(AuditLog)
        if action:
            query = query.filter(AuditLog.action == action)
        if agent_id:
            query = query.filter(AuditLog.agent_id == agent_id)
        if task_id:
            query = query.filter(AuditLog.task_id == task_id)
        if project_id:
            query = query.filter(AuditLog.project_id == project_id)

        return query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()

    @staticmethod
    def get_log(db: Session, log_id: str) -> Optional[AuditLog]:
        return db.query(AuditLog).filter(AuditLog.id == log_id).first()
