from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.database import SessionLocal, engine, Base
from app.api.health import router as health_router
from app.api.router import api_router
from app.services.agent_service import AgentService

setup_logging(log_level=settings.LOG_LEVEL)
logger = get_logger("vicky_os")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence
    logger.info("Initializing VICKY OS core services...", extra={"component": "system"})

    # Ensure tables exist (Alembic handles migrations, this is a safety guard for dev)
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified.", extra={"component": "database"})
    except Exception as e:
        logger.warning(f"Database schema initialization warning: {e}", extra={"component": "database"})

    # Initialize canonical default agents (Techy, Elder, Archy, PA)
    try:
        db = SessionLocal()
        try:
            seeded = AgentService.init_default_agents(db)
            agent_names = ", ".join([a.name for a in seeded])
            logger.info(f"Canonical agents initialized: [{agent_names}]", extra={"component": "agent_service"})
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to seed default agents on startup: {e}", extra={"component": "agent_service"})

    logger.info("VICKY OS Core online and ready.", extra={"component": "system"})
    yield
    # Shutdown sequence
    logger.info("Shutting down VICKY OS core...", extra={"component": "system"})


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="VICKY OS — Self-hosted Multi-Agent AI Operating System",
    lifespan=lifespan,
)

# Enable CORS for web and future mobile dashboard connectivity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health_router)
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "OPERATIONAL",
        "docs_url": "/docs",
        "health_url": "/health",
        "agents": ["techy", "elder", "archy", "pa"],
    }
