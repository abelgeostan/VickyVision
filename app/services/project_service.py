from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.event_service import EventService
from app.services.audit_service import AuditService
from app.core.logging import get_logger

logger = get_logger("project_service")


class ProjectService:
    @staticmethod
    def create_project(db: Session, project_in: ProjectCreate) -> Project:
        project = Project(
            name=project_in.name,
            description=project_in.description,
            status=project_in.status,
            created_by=project_in.created_by,
            objectives=project_in.objectives,
            metadata_json=project_in.metadata_json,
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        EventService.create_event(
            db,
            event_type="project.created",
            source="project_service",
            related_agent_id=project.created_by,
            related_project_id=project.id,
            payload={"name": project.name, "status": project.status},
        )
        AuditService.log(
            db,
            action="project.created",
            agent_id=project.created_by,
            project_id=project.id,
            details={"name": project.name, "status": project.status},
            result="SUCCESS",
        )
        return project

    @staticmethod
    def get_project(db: Session, project_id: str) -> Optional[Project]:
        return db.query(Project).filter(Project.id == project_id).first()

    @staticmethod
    def list_projects(
        db: Session,
        status: Optional[str] = None,
        created_by: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Project]:
        query = db.query(Project)
        if status:
            query = query.filter(Project.status == status)
        if created_by:
            query = query.filter(Project.created_by == created_by)
        return query.order_by(desc(Project.created_at)).offset(offset).limit(limit).all()

    @staticmethod
    def update_project(db: Session, project_id: str, project_in: ProjectUpdate) -> Optional[Project]:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None

        update_data = project_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)

        db.commit()
        db.refresh(project)

        EventService.create_event(
            db,
            event_type="project.updated",
            source="project_service",
            related_project_id=project.id,
            payload=update_data,
        )
        AuditService.log(
            db,
            action="project.updated",
            project_id=project.id,
            details=update_data,
            result="SUCCESS",
        )
        return project

    @staticmethod
    def delete_project(db: Session, project_id: str) -> bool:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False

        db.delete(project)
        db.commit()

        EventService.create_event(
            db,
            event_type="project.deleted",
            source="project_service",
            related_project_id=project_id,
        )
        AuditService.log(
            db,
            action="project.deleted",
            project_id=project_id,
            result="SUCCESS",
        )
        return True

    @staticmethod
    def transition_status(
        db: Session,
        project_id: str,
        new_status: str,
        reason: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> Optional[Project]:
        """Transitions a project to a new lifecycle state with formal event and audit trail."""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None

        old_status = project.status
        project.status = new_status
        db.commit()
        db.refresh(project)

        EventService.create_event(
            db,
            event_type="project.status_changed",
            source="project_service",
            related_agent_id=agent_id,
            related_project_id=project.id,
            payload={
                "project_id": project.id,
                "old_status": old_status,
                "new_status": new_status,
                "reason": reason,
            },
        )
        AuditService.log(
            db,
            action="project.status_changed",
            agent_id=agent_id if agent_id != "user" else None,
            user_id="user" if agent_id == "user" else None,
            project_id=project.id,
            reason=reason,
            details={"old_status": old_status, "new_status": new_status},
            result=new_status,
        )
        return project
