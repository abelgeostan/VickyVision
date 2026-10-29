from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.message import MessageCreate, MessageResponse
from app.services.message_service import MessageService

router = APIRouter(prefix="/messages", tags=["Messages"])


@router.get("", response_model=List[MessageResponse])
def list_messages(
    sender_id: Optional[str] = None,
    receiver_id: Optional[str] = None,
    task_id: Optional[str] = None,
    project_id: Optional[str] = None,
    message_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Retrieve persistent agent messages and conversation logs."""
    return MessageService.list_messages(
        db,
        sender_id=sender_id,
        receiver_id=receiver_id,
        task_id=task_id,
        project_id=project_id,
        message_type=message_type,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(msg_in: MessageCreate, db: Session = Depends(get_db)):
    """Persist an agent message directly without orchestration routing."""
    return MessageService.create_message(
        db,
        sender_id=msg_in.sender_id,
        receiver_id=msg_in.receiver_id,
        content=msg_in.content,
        message_type=msg_in.message_type,
        task_id=msg_in.task_id,
        project_id=msg_in.project_id,
        metadata_json=msg_in.metadata_json,
        status=msg_in.status,
    )


@router.get("/{message_id}", response_model=MessageResponse)
def get_message(message_id: str, db: Session = Depends(get_db)):
    """Retrieve message by ID."""
    msg = MessageService.get_message(db, message_id)
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Message '{message_id}' not found.")
    return msg
