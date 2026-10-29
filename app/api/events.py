from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.event import EventCreate, EventResponse
from app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("", response_model=List[EventResponse])
def list_events(
    event_type: Optional[str] = None,
    agent_id: Optional[str] = None,
    task_id: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Query system and agent events."""
    return EventService.list_events(
        db,
        event_type=event_type,
        agent_id=agent_id,
        task_id=task_id,
        project_id=project_id,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(event_in: EventCreate, db: Session = Depends(get_db)):
    """Publish a new system or agent event."""
    return EventService.create_event(
        db,
        event_type=event_in.event_type,
        source=event_in.source,
        related_agent_id=event_in.related_agent_id,
        related_task_id=event_in.related_task_id,
        related_project_id=event_in.related_project_id,
        payload=event_in.payload,
    )


@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: str, db: Session = Depends(get_db)):
    """Retrieve event by ID."""
    event = EventService.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event '{event_id}' not found.")
    return event
