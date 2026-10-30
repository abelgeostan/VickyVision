import asyncio
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.event import EventCreate, EventResponse
from app.services.event_service import EventService, register_event_subscriber, unregister_event_subscriber

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("/stream")
async def stream_events(
    request: Request,
    once: bool = False,
):
    """
    Server-Sent Events (SSE) endpoint providing real-time event streaming
    to the VICKY OS Command Center UI.
    """
    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue()

        def on_event(event):
            try:
                data = {
                    "id": str(event.id),
                    "event_type": str(event.event_type),
                    "source": str(event.source),
                    "related_agent_id": str(event.related_agent_id) if event.related_agent_id else None,
                    "related_task_id": str(event.related_task_id) if event.related_task_id else None,
                    "related_project_id": str(event.related_project_id) if event.related_project_id else None,
                    "payload": event.payload or {},
                    "created_at": event.created_at.isoformat() if event.created_at else None,
                }
                queue.put_nowait(data)
            except Exception:
                pass

        register_event_subscriber(on_event)
        try:
            yield ": connected\n\n"
            if once:
                return

            while True:
                if await request.is_disconnected():
                    break
                try:
                    event_data = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(event_data)}\n\n"
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        except (asyncio.CancelledError, GeneratorExit):
            pass
        finally:
            unregister_event_subscriber(on_event)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )




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
