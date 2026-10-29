from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.llm.ollama import get_llm_provider
from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=Dict[str, Any])
@router.get("/api/health", response_model=Dict[str, Any])
def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check for API, PostgreSQL database, and Ollama LLM provider."""
    # Check Database
    db_status = False
    db_error = None
    try:
        db.execute(text("SELECT 1"))
        db_status = True
    except Exception as e:
        db_error = str(e)

    # Check Ollama
    llm_provider = get_llm_provider()
    ollama_status = llm_provider.check_health()
    available_models = []
    if ollama_status:
        try:
            available_models = llm_provider.list_models()
        except Exception:
            pass

    overall_status = "healthy" if (db_status and ollama_status) else "degraded" if db_status else "unhealthy"

    return {
        "status": overall_status,
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "components": {
            "database": {
                "status": "connected" if db_status else "error",
                "error": db_error,
            },
            "ollama": {
                "status": "connected" if ollama_status else "unreachable",
                "base_url": settings.OLLAMA_BASE_URL,
                "models_available": available_models,
            },
        },
    }
