from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse
from app.services.agent_service import AgentService

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("", response_model=List[AgentResponse])
def list_agents(status: Optional[str] = None, db: Session = Depends(get_db)):
    """List all registered agents in VICKY OS."""
    return AgentService.list_agents(db, status=status)


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
def create_agent(agent_in: AgentCreate, db: Session = Depends(get_db)):
    """Register a new configurable agent."""
    existing = AgentService.get_agent(db, agent_in.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Agent with ID '{agent_in.id}' already exists.",
        )
    return AgentService.create_agent(db, agent_in)


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """Retrieve details of a specific agent."""
    agent = AgentService.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent '{agent_id}' not found.")
    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
def update_agent(agent_id: str, agent_in: AgentUpdate, db: Session = Depends(get_db)):
    """Update agent configuration, status, or prompts."""
    updated = AgentService.update_agent(db, agent_id, agent_in)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent '{agent_id}' not found.")
    return updated


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    """Delete an agent from the system."""
    success = AgentService.delete_agent(db, agent_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent '{agent_id}' not found.")
    return None
