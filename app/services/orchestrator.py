from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging import get_logger
from app.models.agent import Agent
from app.models.task import Task
from app.models.message import Message
from app.schemas.orchestrator import OrchestratorResponse, RouteMessageRequest
from app.schemas.message import MessageResponse
from app.services.agent_service import AgentService
from app.services.task_service import TaskService
from app.services.message_service import MessageService
from app.services.event_service import EventService
from app.services.audit_service import AuditService
from app.services.memory_service import MemoryService
from app.llm.base import BaseLLMProvider
from app.llm.ollama import get_llm_provider

logger = get_logger("agent_orchestrator")


class AgentOrchestrator:
    """
    Central orchestration layer of VICKY OS.
    All inter-agent communication, user-to-agent interactions, and task routing
    pass strictly through this orchestrator.
    """

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm_provider = llm_provider or get_llm_provider()

    def _build_agent_prompt(
        self,
        db: Session,
        agent: Agent,
        incoming_content: str,
        sender_id: str,
        message_type: str,
        task: Optional[Task] = None,
        project_id: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Assembles rich context: system prompt, memories, task metadata, and message history."""
        messages: List[Dict[str, str]] = []

        # 1. Fetch relevant memories (agent's private + shared organizational memories)
        memories = MemoryService.list_memories(db, agent_id=agent.id, limit=5)
        memory_text = ""
        if memories:
            memory_items = [f"- [{m.type}] {m.content}" for m in memories]
            memory_text = "\nRelevant Memories:\n" + "\n".join(memory_items)

        # 2. Task context if associated
        task_text = ""
        if task:
            task_text = (
                f"\nAssociated Task Context:\n"
                f"- Task ID: {task.id}\n"
                f"- Title: {task.title}\n"
                f"- Status: {task.status}\n"
                f"- Priority: {task.priority}\n"
                f"- Description: {task.description or 'None'}\n"
            )

        # 3. Enhanced system prompt
        enhanced_system_prompt = (
            f"{agent.system_prompt}\n\n"
            f"Agent ID: {agent.id}\n"
            f"Name: {agent.name}\n"
            f"Role: {agent.role}\n"
            f"Personality: {agent.personality}\n"
            f"{memory_text}\n"
            f"{task_text}\n"
            "Instructions: Respond in character according to your role and responsibilities. "
            "Keep responses concise, clear, and actionable."
        )

        # 4. Fetch recent conversation context between sender and receiver
        recent_history = MessageService.list_messages(
            db,
            conversation_between=(sender_id, agent.id),
            task_id=task.id if task else None,
            limit=4,
        )
        # Oldest first
        recent_history.reverse()

        for msg in recent_history:
            role = "assistant" if msg.sender_id == agent.id else "user"
            messages.append({"role": role, "content": msg.content})

        # Add the current incoming message if not already in recent_history
        if not recent_history or recent_history[-1].content != incoming_content:
            messages.append({
                "role": "user",
                "content": f"[{message_type} from {sender_id.upper()}]: {incoming_content}",
            })

        return enhanced_system_prompt, messages

    def route_message(
        self,
        db: Session,
        sender_id: str,
        receiver_id: str,
        content: str,
        message_type: str = "REQUEST",
        task_id: Optional[str] = None,
        project_id: Optional[str] = None,
        invoke_agent: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> OrchestratorResponse:
        """
        Routes a message between agents or user-to-agent.
        Tracks context, stores message history, emits events, and executes LLM generation.
        """
        logger.info(
            f"Routing message from '{sender_id}' to '{receiver_id}' (type={message_type})",
            extra={"component": "orchestrator", "agent": sender_id, "task": task_id, "event": "route_message"},
        )

        task = TaskService.get_task(db, task_id) if task_id else None
        if task and not project_id and task.project_id:
            project_id = task.project_id

        # 1. Store incoming source message
        source_message = MessageService.create_message(
            db,
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            message_type=message_type,
            task_id=task_id,
            project_id=project_id,
            metadata_json=metadata or {},
            status="DELIVERED",
        )

        AuditService.log(
            db,
            action="orchestrator.route_message",
            agent_id=sender_id if sender_id != "user" else None,
            user_id="user" if sender_id == "user" else None,
            task_id=task_id,
            project_id=project_id,
            details={
                "source_message_id": source_message.id,
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "message_type": message_type,
            },
            result="DELIVERED",
        )

        # 2. Check if destination is a registered agent
        receiver_agent = AgentService.get_agent(db, receiver_id)
        agent_response_model: Optional[Message] = None

        if invoke_agent and receiver_agent:
            # Mark agent status as ACTIVE / BUSY
            prev_status = receiver_agent.status
            receiver_agent.status = "BUSY"
            db.commit()

            try:
                system_prompt, messages = self._build_agent_prompt(
                    db=db,
                    agent=receiver_agent,
                    incoming_content=content,
                    sender_id=sender_id,
                    message_type=message_type,
                    task=task,
                    project_id=project_id,
                )

                # Determine model and options from agent's config
                cfg = receiver_agent.model_config_data or {}
                model = cfg.get("model", settings.DEFAULT_MODEL)
                options = {
                    "temperature": cfg.get("temperature", 0.3),
                    "num_predict": cfg.get("num_predict", 512),
                }

                logger.info(
                    f"Invoking LLM for agent '{receiver_agent.id}' with model '{model}'",
                    extra={"component": "orchestrator", "agent": receiver_agent.id, "task": task_id},
                )

                llm_res = self.llm_provider.chat(
                    messages=messages,
                    model=model,
                    system_prompt=system_prompt,
                    options=options,
                )

                response_type = "RESPONSE"
                if message_type == "ADVICE":
                    response_type = "ADVICE"
                elif message_type == "TASK_ASSIGNMENT":
                    response_type = "TASK_UPDATE"

                # Save generated response message
                agent_response_model = MessageService.create_message(
                    db,
                    sender_id=receiver_agent.id,
                    receiver_id=sender_id,
                    content=llm_res.content,
                    message_type=response_type,
                    task_id=task_id,
                    project_id=project_id,
                    metadata_json={
                        "model": model,
                        "duration_ms": llm_res.total_duration_ms,
                        "reply_to": source_message.id,
                    },
                    status="SENT",
                )

                EventService.create_event(
                    db,
                    event_type="agent.responded",
                    source="orchestrator",
                    related_agent_id=receiver_agent.id,
                    related_task_id=task_id,
                    related_project_id=project_id,
                    payload={
                        "response_message_id": agent_response_model.id,
                        "model": model,
                    },
                )

            except Exception as e:
                logger.error(
                    f"Error invoking agent '{receiver_agent.id}': {e}",
                    extra={"component": "orchestrator", "agent": receiver_agent.id, "task": task_id},
                )
                EventService.create_event(
                    db,
                    event_type="agent.error",
                    source="orchestrator",
                    related_agent_id=receiver_agent.id,
                    related_task_id=task_id,
                    payload={"error": str(e)},
                )
                raise
            finally:
                receiver_agent.status = prev_status if prev_status != "BUSY" else "IDLE"
                db.commit()

        return OrchestratorResponse(
            success=True,
            source_message=MessageResponse.model_validate(source_message),
            agent_response=MessageResponse.model_validate(agent_response_model) if agent_response_model else None,
            task_id=task_id,
            project_id=project_id,
            notes=f"Message processed successfully from {sender_id} to {receiver_id}.",
        )

    def execute_flow_step(
        self,
        db: Session,
        flow: str,
        content: str,
        task_id: Optional[str] = None,
        project_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> OrchestratorResponse:
        """
        Executes one of the canonical organizational message flows:
        - user_to_pa
        - pa_to_archy
        - archy_to_elder
        - elder_to_archy
        - archy_to_techy
        - techy_to_elder
        - techy_to_pa
        """
        flow_mapping = {
            "user_to_pa": ("user", "pa", "REQUEST"),
            "pa_to_archy": ("pa", "archy", "REQUEST"),
            "archy_to_elder": ("archy", "elder", "ADVICE"),
            "elder_to_archy": ("elder", "archy", "RESPONSE"),
            "archy_to_techy": ("archy", "techy", "TASK_ASSIGNMENT"),
            "techy_to_elder": ("techy", "elder", "ADVICE"),
            "techy_to_pa": ("techy", "pa", "REPORT"),
        }

        if flow not in flow_mapping:
            valid_flows = ", ".join(flow_mapping.keys())
            raise ValueError(f"Unknown flow '{flow}'. Supported flows: {valid_flows}")

        sender_id, receiver_id, message_type = flow_mapping[flow]

        return self.route_message(
            db=db,
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            message_type=message_type,
            task_id=task_id,
            project_id=project_id,
            invoke_agent=True,
            metadata=metadata,
        )

    def dispatch_task(
        self,
        db: Session,
        task_id: str,
        assigned_to: Optional[str] = None,
        instruction: Optional[str] = None,
    ) -> OrchestratorResponse:
        """Assigns and dispatches a task to an agent, triggering an assignment notification flow."""
        task = TaskService.get_task(db, task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found.")

        target_agent = assigned_to or task.assigned_to
        if not target_agent:
            raise ValueError("Task has no assigned agent.")

        # Update assignment and status
        task.assigned_to = target_agent
        if task.status == "PENDING":
            task.status = "RUNNING"
        db.commit()
        db.refresh(task)

        content = instruction or f"Task Assigned: '{task.title}'. Description: {task.description or 'No extra details'}"
        return self.route_message(
            db=db,
            sender_id=task.created_by or "archy",
            receiver_id=target_agent,
            content=content,
            message_type="TASK_ASSIGNMENT",
            task_id=task.id,
            project_id=task.project_id,
            invoke_agent=True,
        )
