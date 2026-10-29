from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.memory import MemoryCreate, MemoryUpdate, MemoryResponse
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/memory", tags=["Memory"])


@router.get("", response_model=List[MemoryResponse])
def list_memories(
    agent_id: Optional[str] = None,
    type: Optional[str] = None,
    include_shared: bool = True,
    query: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Retrieve agent memories (SHORT_TERM, PROJECT, LONG_TERM, SHARED)."""
    return MemoryService.list_memories(
        db,
        agent_id=agent_id,
        memory_type=type,
        include_shared=include_shared,
        search_query=query,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
def create_memory(mem_in: MemoryCreate, db: Session = Depends(get_db)):
    """Persist structured memory for an agent or organizational shared space."""
    return MemoryService.create_memory(db, mem_in)


@router.get("/{memory_id}", response_model=MemoryResponse)
def get_memory(memory_id: str, db: Session = Depends(get_db)):
    """Retrieve specific memory by ID."""
    mem = MemoryService.get_memory(db, memory_id)
    if not mem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Memory '{memory_id}' not found.")
    return mem


@router.put("/{memory_id}", response_model=MemoryResponse)
def update_memory(memory_id: str, mem_in: MemoryUpdate, db: Session = Depends(get_db)):
    """Update content or importance of a memory."""
    updated = MemoryService.update_memory(db, memory_id, mem_in)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Memory '{memory_id}' not found.")
    return updated


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(memory_id: str, db: Session = Depends(get_db)):
    """Delete a memory item."""
    success = MemoryService.delete_memory(db, memory_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Memory '{memory_id}' not found.")
    return None
