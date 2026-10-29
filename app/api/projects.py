from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=List[ProjectResponse])
def list_projects(
    status: Optional[str] = None,
    created_by: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List projects in VICKY OS."""
    return ProjectService.list_projects(db, status=status, created_by=created_by, limit=limit, offset=offset)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(project_in: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project (e.g. proposed by Archy or requested by user)."""
    return ProjectService.create_project(db, project_in)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    """Retrieve project by ID."""
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found.")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, project_in: ProjectUpdate, db: Session = Depends(get_db)):
    """Update project status, objectives, or metadata."""
    updated = ProjectService.update_project(db, project_id, project_in)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found.")
    return updated


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Delete a project."""
    success = ProjectService.delete_project(db, project_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found.")
    return None
