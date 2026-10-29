from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=List[TaskResponse])
def list_tasks(
    project_id: Optional[str] = None,
    assigned_to: Optional[str] = None,
    created_by: Optional[str] = None,
    parent_task_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List tasks with optional filtering by project, assignee, creator, parent task, or status."""
    return TaskService.list_tasks(
        db,
        project_id=project_id,
        assigned_to=assigned_to,
        created_by=created_by,
        parent_task_id=parent_task_id,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task_in: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task or hierarchical subtask."""
    return TaskService.create_task(db, task_in)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    """Retrieve task details, including nested subtasks."""
    task = TaskService.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' not found.")
    return task


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, task_in: TaskUpdate, db: Session = Depends(get_db)):
    """Update task status, progress, priority, result, or error."""
    updated = TaskService.update_task(db, task_id, task_in)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' not found.")
    return updated


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str, db: Session = Depends(get_db)):
    """Delete a task and its subtasks."""
    success = TaskService.delete_task(db, task_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' not found.")
    return None
