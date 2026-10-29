from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from app.models.memory import Memory
from app.schemas.memory import MemoryCreate, MemoryUpdate
from app.services.event_service import EventService
from app.core.logging import get_logger

logger = get_logger("memory_service")


class MemoryService:
    @staticmethod
    def create_memory(db: Session, memory_in: MemoryCreate) -> Memory:
        memory = Memory(
            agent_id=memory_in.agent_id,
            type=memory_in.type,
            content=memory_in.content,
            importance=memory_in.importance,
            metadata_json=memory_in.metadata_json,
        )
        db.add(memory)
        db.commit()
        db.refresh(memory)

        EventService.create_event(
            db,
            event_type="memory.created",
            source="memory_service",
            related_agent_id=memory.agent_id,
            payload={"memory_id": memory.id, "type": memory.type, "importance": memory.importance},
        )
        return memory

    @staticmethod
    def get_memory(db: Session, memory_id: str) -> Optional[Memory]:
        return db.query(Memory).filter(Memory.id == memory_id).first()

    @staticmethod
    def list_memories(
        db: Session,
        agent_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        include_shared: bool = True,
        search_query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Memory]:
        query = db.query(Memory)

        if agent_id:
            if include_shared:
                query = query.filter(or_(Memory.agent_id == agent_id, Memory.type == "SHARED", Memory.agent_id.is_(None)))
            else:
                query = query.filter(Memory.agent_id == agent_id)
        elif memory_type:
            query = query.filter(Memory.type == memory_type)

        if search_query:
            query = query.filter(Memory.content.ilike(f"%{search_query}%"))

        return query.order_by(desc(Memory.importance), desc(Memory.created_at)).offset(offset).limit(limit).all()

    @staticmethod
    def update_memory(db: Session, memory_id: str, memory_in: MemoryUpdate) -> Optional[Memory]:
        mem = db.query(Memory).filter(Memory.id == memory_id).first()
        if not mem:
            return None

        update_data = memory_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(mem, field, value)

        db.commit()
        db.refresh(mem)
        return mem

    @staticmethod
    def delete_memory(db: Session, memory_id: str) -> bool:
        mem = db.query(Memory).filter(Memory.id == memory_id).first()
        if not mem:
            return False

        db.delete(mem)
        db.commit()
        return True

    @staticmethod
    def record_organizational_fact(
        db: Session,
        category: str,
        content: str,
        agent_id: Optional[str] = None,
        importance: int = 5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Memory:
        """
        Records structured organizational memory in one of the canonical categories:
        USER_PREFERENCE, PROJECT_FACT, ARCHITECTURAL_DECISION, SERVER_FACT, LESSON_LEARNED.
        """
        valid_categories = {
            "USER_PREFERENCE",
            "PROJECT_FACT",
            "ARCHITECTURAL_DECISION",
            "SERVER_FACT",
            "LESSON_LEARNED",
            "SHARED",
            "LONG_TERM",
        }
        mem_type = category.upper() if category.upper() in valid_categories else "PROJECT_FACT"
        return MemoryService.create_memory(
            db,
            MemoryCreate(
                agent_id=agent_id,
                type=mem_type,
                content=content,
                importance=importance,
                metadata_json=metadata or {},
            ),
        )

    @staticmethod
    def get_organizational_memories(
        db: Session,
        category: Optional[str] = None,
        limit: int = 20,
    ) -> List[Memory]:
        """Retrieves structured organizational facts."""
        query = db.query(Memory)
        if category:
            query = query.filter(Memory.type == category.upper())
        return query.order_by(desc(Memory.importance), desc(Memory.created_at)).limit(limit).all()
