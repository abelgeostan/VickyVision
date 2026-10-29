from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.core.logging import get_logger
from app.models.decision import DecisionRecord
from app.schemas.decision import DecisionRecordCreate, DecisionRecordUpdate
from app.services.event_service import EventService
from app.services.audit_service import AuditService

logger = get_logger("decision_service")


class DecisionService:
    @staticmethod
    def create_decision(db: Session, data: DecisionRecordCreate) -> DecisionRecord:
        """Creates and stores a persistent architectural or organizational decision."""
        decision = DecisionRecord(
            project_id=data.project_id,
            task_id=data.task_id,
            title=data.title,
            category=data.category,
            status=data.status,
            proposed_by=data.proposed_by,
            reviewed_by=data.reviewed_by,
            approved_by=data.approved_by,
            decision=data.decision,
            reason=data.reason,
            alternatives_considered=data.alternatives_considered,
            risks_identified=data.risks_identified,
            review_notes=data.review_notes,
            metadata_json=data.metadata_json,
        )
        db.add(decision)
        db.commit()
        db.refresh(decision)

        EventService.create_event(
            db,
            event_type="decision.created",
            source="decision_service",
            related_agent_id=data.proposed_by,
            related_project_id=data.project_id,
            related_task_id=data.task_id,
            payload={
                "decision_id": decision.id,
                "title": decision.title,
                "status": decision.status,
                "decision": decision.decision,
            },
        )

        AuditService.log(
            db,
            action="decision.create",
            agent_id=data.proposed_by if data.proposed_by != "user" else None,
            user_id="user" if data.proposed_by == "user" else None,
            project_id=data.project_id,
            task_id=data.task_id,
            details={"decision_id": decision.id, "title": decision.title, "status": decision.status},
            result="SUCCESS",
        )

        return decision

    @staticmethod
    def get_decision(db: Session, decision_id: str) -> Optional[DecisionRecord]:
        return db.query(DecisionRecord).filter(DecisionRecord.id == decision_id).first()

    @staticmethod
    def list_decisions(
        db: Session,
        project_id: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[DecisionRecord]:
        query = db.query(DecisionRecord)
        if project_id:
            query = query.filter(DecisionRecord.project_id == project_id)
        if category:
            query = query.filter(DecisionRecord.category == category)
        if status:
            query = query.filter(DecisionRecord.status == status)
        return query.order_by(DecisionRecord.created_at.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def update_decision(db: Session, decision_id: str, data: DecisionRecordUpdate) -> Optional[DecisionRecord]:
        decision = DecisionService.get_decision(db, decision_id)
        if not decision:
            return None

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(decision, key, value)

        db.commit()
        db.refresh(decision)

        EventService.create_event(
            db,
            event_type="decision.updated",
            source="decision_service",
            related_project_id=decision.project_id,
            related_task_id=decision.task_id,
            payload={"decision_id": decision.id, "status": decision.status},
        )
        return decision
