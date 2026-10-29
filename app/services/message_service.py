from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_
from app.models.message import Message
from app.schemas.message import MessageCreate
from app.services.event_service import EventService
from app.services.audit_service import AuditService
from app.core.logging import get_logger

logger = get_logger("message_service")


class MessageService:
    @staticmethod
    def create_message(
        db: Session,
        sender_id: str,
        receiver_id: str,
        content: str,
        message_type: str = "REQUEST",
        task_id: Optional[str] = None,
        project_id: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
        status: str = "SENT",
    ) -> Message:
        message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            message_type=message_type,
            task_id=task_id,
            project_id=project_id,
            metadata_json=metadata_json or {},
            status=status,
        )
        db.add(message)
        db.commit()
        db.refresh(message)

        EventService.create_event(
            db,
            event_type="agent.message_sent",
            source="message_service",
            related_agent_id=sender_id,
            related_task_id=task_id,
            related_project_id=project_id,
            payload={
                "message_id": message.id,
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "message_type": message_type,
            },
        )
        return message

    @staticmethod
    def get_message(db: Session, message_id: str) -> Optional[Message]:
        return db.query(Message).filter(Message.id == message_id).first()

    @staticmethod
    def list_messages(
        db: Session,
        sender_id: Optional[str] = None,
        receiver_id: Optional[str] = None,
        conversation_between: Optional[Tuple[str, str]] = None,
        task_id: Optional[str] = None,
        project_id: Optional[str] = None,
        message_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Message]:
        query = db.query(Message)

        if conversation_between:
            a, b = conversation_between
            query = query.filter(
                or_(
                    and_(Message.sender_id == a, Message.receiver_id == b),
                    and_(Message.sender_id == b, Message.receiver_id == a),
                )
            )
        else:
            if sender_id:
                query = query.filter(Message.sender_id == sender_id)
            if receiver_id:
                query = query.filter(Message.receiver_id == receiver_id)

        if task_id:
            query = query.filter(Message.task_id == task_id)
        if project_id:
            query = query.filter(Message.project_id == project_id)
        if message_type:
            query = query.filter(Message.message_type == message_type)

        return query.order_by(desc(Message.created_at)).offset(offset).limit(limit).all()

    @staticmethod
    def update_status(db: Session, message_id: str, status: str) -> Optional[Message]:
        msg = db.query(Message).filter(Message.id == message_id).first()
        if msg:
            msg.status = status
            db.commit()
            db.refresh(msg)
        return msg
