from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.event_service import EventService
from app.services.audit_service import AuditService
from app.core.logging import get_logger

logger = get_logger("task_service")


class TaskService:
    @staticmethod
    def create_task(db: Session, task_in: TaskCreate) -> Task:
        task = Task(
            title=task_in.title,
            description=task_in.description,
            created_by=task_in.created_by,
            assigned_to=task_in.assigned_to,
            parent_task_id=task_in.parent_task_id,
            project_id=task_in.project_id,
            status=task_in.status,
            priority=task_in.priority,
            progress=task_in.progress,
            result=task_in.result,
            error=task_in.error,
        )
        if task.status == "RUNNING":
            task.started_at = datetime.now(timezone.utc)

        db.add(task)
        db.commit()
        db.refresh(task)

        EventService.create_event(
            db,
            event_type="task.created",
            source="task_service",
            related_agent_id=task.created_by or task.assigned_to,
            related_task_id=task.id,
            related_project_id=task.project_id,
            payload={"title": task.title, "status": task.status, "assigned_to": task.assigned_to},
        )
        AuditService.log(
            db,
            action="task.created",
            agent_id=task.created_by,
            task_id=task.id,
            project_id=task.project_id,
            details={"title": task.title, "assigned_to": task.assigned_to, "status": task.status},
            result="SUCCESS",
        )
        return task

    @staticmethod
    def get_task(db: Session, task_id: str) -> Optional[Task]:
        return db.query(Task).filter(Task.id == task_id).first()

    @staticmethod
    def list_tasks(
        db: Session,
        project_id: Optional[str] = None,
        assigned_to: Optional[str] = None,
        created_by: Optional[str] = None,
        parent_task_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Task]:
        query = db.query(Task)
        if project_id:
            query = query.filter(Task.project_id == project_id)
        if assigned_to:
            query = query.filter(Task.assigned_to == assigned_to)
        if created_by:
            query = query.filter(Task.created_by == created_by)
        if parent_task_id:
            query = query.filter(Task.parent_task_id == parent_task_id)
        if status:
            query = query.filter(Task.status == status)

        return query.order_by(desc(Task.created_at)).offset(offset).limit(limit).all()

    @staticmethod
    def update_task(db: Session, task_id: str, task_in: TaskUpdate) -> Optional[Task]:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None

        update_data = task_in.model_dump(exclude_unset=True)
        old_status = task.status

        for field, value in update_data.items():
            setattr(task, field, value)

        new_status = task.status
        now = datetime.now(timezone.utc)

        # Handle lifecycle timestamps based on status
        if new_status == "RUNNING" and not task.started_at:
            task.started_at = now
        elif new_status in ("COMPLETED", "FAILED", "CANCELLED") and not task.completed_at:
            task.completed_at = now
            if new_status == "COMPLETED" and task.progress < 100:
                task.progress = 100

        db.commit()
        db.refresh(task)

        # Determine event type
        if old_status != new_status:
            if new_status == "RUNNING":
                event_type = "task.started"
            elif new_status == "COMPLETED":
                event_type = "task.completed"
            elif new_status == "FAILED":
                event_type = "task.failed"
            else:
                event_type = "task.status_changed"
        else:
            event_type = "task.updated"

        EventService.create_event(
            db,
            event_type=event_type,
            source="task_service",
            related_agent_id=task.assigned_to or task.created_by,
            related_task_id=task.id,
            related_project_id=task.project_id,
            payload={
                "title": task.title,
                "old_status": old_status,
                "new_status": new_status,
                "progress": task.progress,
            },
        )
        AuditService.log(
            db,
            action=event_type,
            agent_id=task.assigned_to or task.created_by,
            task_id=task.id,
            project_id=task.project_id,
            details=update_data,
            result=new_status,
        )
        return task

    @staticmethod
    def delete_task(db: Session, task_id: str) -> bool:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return False

        db.delete(task)
        db.commit()

        EventService.create_event(
            db,
            event_type="task.deleted",
            source="task_service",
            related_task_id=task_id,
        )
        AuditService.log(
            db,
            action="task.deleted",
            task_id=task_id,
            result="SUCCESS",
        )
        return True
