from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.agents import router as agents_router
from app.api.projects import router as projects_router
from app.api.tasks import router as tasks_router
from app.api.messages import router as messages_router
from app.api.events import router as events_router
from app.api.memory import router as memory_router
from app.api.approvals import router as approvals_router
from app.api.audit import router as audit_router
from app.api.orchestrator import router as orchestrator_router
from app.api.techy import router as techy_router
from app.api.organization import router as org_router

api_router = APIRouter()

# Core system routers
api_router.include_router(agents_router)
api_router.include_router(projects_router)
api_router.include_router(tasks_router)
api_router.include_router(messages_router)
api_router.include_router(events_router)
api_router.include_router(memory_router)
api_router.include_router(approvals_router)
api_router.include_router(audit_router)
api_router.include_router(orchestrator_router)
api_router.include_router(techy_router)
api_router.include_router(org_router)
