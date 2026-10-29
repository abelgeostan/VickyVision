from typing import Optional, Dict, Any, List, Callable
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.event import Event
from app.schemas.event import EventCreate
from app.core.logging import get_logger

logger = get_logger("event_service")

# In-memory subscribers for decoupled real-time hooks
EventSubscriber = Callable[[Event], None]
_subscribers: List[EventSubscriber] = []


def register_event_subscriber(subscriber: EventSubscriber) -> None:
    """Registers an event callback (e.g. for PA real-time notifications or monitoring)."""
    if subscriber not in _subscribers:
        _subscribers.append(subscriber)


class EventService:
    @staticmethod
    def create_event(
        db: Session,
        event_type: str,
        source: str,
        related_agent_id: Optional[str] = None,
        related_task_id: Optional[str] = None,
        related_project_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Event:
        """Persists an event to the database and dispatches to registered subscribers."""
        event = Event(
            event_type=event_type,
            source=source,
            related_agent_id=related_agent_id,
            related_task_id=related_task_id,
            related_project_id=related_project_id,
            payload=payload or {},
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        logger.info(
            f"Event emitted: {event_type} from {source}",
            extra={
                "component": "event_system",
                "agent": related_agent_id,
                "task": related_task_id,
                "event": event_type,
            },
        )

        # Notify in-memory subscribers safely
        for sub in _subscribers:
            try:
                sub(event)
            except Exception as e:
                logger.error(f"Error in event subscriber {sub}: {e}", extra={"component": "event_system"})

        return event

    @staticmethod
    def list_events(
        db: Session,
        event_type: Optional[str] = None,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Event]:
        query = db.query(Event)
        if event_type:
            query = query.filter(Event.event_type == event_type)
        if agent_id:
            query = query.filter(Event.related_agent_id == agent_id)
        if task_id:
            query = query.filter(Event.related_task_id == task_id)
        if project_id:
            query = query.filter(Event.related_project_id == project_id)

        return query.order_by(desc(Event.created_at)).offset(offset).limit(limit).all()

    @staticmethod
    def get_event(db: Session, event_id: str) -> Optional[Event]:
        return db.query(Event).filter(Event.id == event_id).first()
