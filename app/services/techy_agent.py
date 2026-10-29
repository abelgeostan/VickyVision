import json
import re
import time
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging import get_logger
from app.models.agent import Agent
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate
from app.schemas.techy import TechyStepRecord, TechyExecuteResponse
from app.services.agent_service import AgentService
from app.services.task_service import TaskService
from app.services.event_service import EventService
from app.services.audit_service import AuditService
from app.services.memory_service import MemoryService
from app.services.server_discovery import ServerDiscoveryService
from app.schemas.memory import MemoryCreate
from app.execution.base import BaseExecutionProvider
from app.execution.factory import get_execution_provider
from app.tools.registry import ToolRegistry, get_tool_registry
from app.llm.base import BaseLLMProvider
from app.llm.ollama import get_llm_provider

logger = get_logger("techy_agent")


class TechyAgentLoop:
    """
    Autonomous execution engine for Techy.
    Runs multi-step inspection, diagnosis, execution, and verification loops on the VICKY server.
    """

    def __init__(
        self,
        execution_provider: Optional[BaseExecutionProvider] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
        tool_registry: Optional[ToolRegistry] = None,
    ):
        self.exec_provider = execution_provider or get_execution_provider()
        self.llm_provider = llm_provider or get_llm_provider()
        self.tool_registry = tool_registry or get_tool_registry()

    def _extract_json_action(self, response_text: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Robustly parses structured JSON tool action or finish response from LLM output."""
        if not response_text:
            return None, "Empty response from LLM"

        text = response_text.strip()
        # Clean think tags if model outputs them
        if "<think>" in text and "</think>" in text:
            parts = re.split(r"</think>", text, maxsplit=1)
            text = parts[1].strip() or parts[0].replace("<think>", "").strip()

        # Check for markdown code blocks
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1)), None
            except json.JSONDecodeError:
                pass

        # Try raw JSON block between first { and last }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1]
            try:
                return json.loads(candidate), None
            except json.JSONDecodeError as err:
                return None, f"JSON syntax error: {str(err)}"

        return None, "Could not find a valid JSON action block in model response"

    def _build_system_prompt(self, agent: Agent, discovery_summary: str, memory_context: str) -> str:
        tools_doc = self.tool_registry.format_tools_for_prompt()

        return (
            f"{agent.system_prompt}\n\n"
            "==================================================\n"
            "SERVER & INFRASTRUCTURE CONTEXT\n"
            "==================================================\n"
            f"{discovery_summary}\n\n"
            "==================================================\n"
            "ORGANIZATIONAL & TECHNICAL MEMORY\n"
            "==================================================\n"
            f"{memory_context}\n\n"
            "==================================================\n"
            "AVAILABLE REAL-WORLD TOOLS\n"
            "==================================================\n"
            f"{tools_doc}\n\n"
            "==================================================\n"
            "OPERATING INSTRUCTIONS & PROTOCOL\n"
            "==================================================\n"
            "You are TECHY, autonomous engineer for VICKY OS with FULL, UNRESTRICTED ACCESS to this server.\n"
            "You operate the server in sequential steps: inspect, execute, verify, and report.\n"
            "CRITICAL RULES:\n"
            "1. You must respond ONLY with a single JSON object at each step.\n"
            "2. When you want to call a tool, respond with:\n"
            '   {\n'
            '     "thought": "<reasoning for what you are doing and why>",\n'
            '     "action": "<tool_name>",\n'
            '     "args": { ... }\n'
            '   }\n'
            "3. When you have satisfied the objective or verified your findings, finish with:\n"
            '   {\n'
            '     "thought": "<summary of what was verified>",\n'
            '     "action": "finish",\n'
            '     "final_answer": "<comprehensive, clear answer or report for the user>",\n'
            '     "learned_fact": "<optional single reusable infrastructure fact to store in memory, or null>"\n'
            '   }\n'
            "4. NEVER assume a command succeeded without checking stdout/stderr.\n"
            "5. After modifying files, restarting services, or deploying, verify health.\n"
            "6. Keep thoughts concise and actionable.\n"
        )

    def execute_task(
        self,
        db: Session,
        instruction: str,
        task_id: Optional[str] = None,
        project_id: Optional[str] = None,
        max_steps: Optional[int] = None,
        timeout_seconds: Optional[float] = None,
    ) -> TechyExecuteResponse:
        """Executes an autonomous multi-step technical task on the server."""
        max_steps = max_steps or settings.TECHY_MAX_STEPS
        timeout_seconds = timeout_seconds or settings.TECHY_LOOP_TIMEOUT_SECONDS
        start_loop_time = time.perf_counter()

        # 1. Resolve or create Task record
        if task_id:
            task = TaskService.get_task(db, task_id)
            if not task:
                raise ValueError(f"Task with ID '{task_id}' not found.")
            task.assigned_to = "techy"
            task.status = "RUNNING"
            db.commit()
            db.refresh(task)
        else:
            task = TaskService.create_task(
                db,
                TaskCreate(
                    title=f"Techy: {instruction[:60]}...",
                    description=instruction,
                    created_by="user",
                    assigned_to="techy",
                    project_id=project_id,
                    status="RUNNING",
                    priority="HIGH",
                ),
            )

        EventService.create_event(
            db,
            event_type="techy.task_started",
            source="techy_agent",
            related_agent_id="techy",
            related_task_id=task.id,
            related_project_id=project_id,
            payload={"instruction": instruction},
        )
        AuditService.log(
            db,
            action="techy.task_started",
            agent_id="techy",
            task_id=task.id,
            project_id=project_id,
            details={"instruction": instruction},
            result="RUNNING",
        )

        # 2. Techy Agent Profile & Model Config
        techy_agent = AgentService.get_agent(db, "techy")
        model = (techy_agent.model_config_data or {}).get("model", settings.TECHY_MODEL)
        techy_options = {
            "temperature": (techy_agent.model_config_data or {}).get("temperature", 0.2),
            "num_predict": 512,
        }

        # 3. Context Assembly
        discovery = ServerDiscoveryService.get_discovery(self.exec_provider, db=db)
        discovery_summary = (
            f"Host: {discovery.get('hostname')} ({discovery.get('os')}, kernel {discovery.get('kernel')})\n"
            f"CPUs: {discovery.get('cpu_cores')} cores | RAM: {discovery.get('ram_total_mb')}MB total ({discovery.get('ram_available_mb')}MB free)\n"
            f"Disk Root: {discovery.get('disk_root_avail')}\n"
            f"IPs: {', '.join(discovery.get('ip_addresses', []))}\n"
            f"Docker: {discovery.get('docker_version')}\n"
            f"Containers: {len(discovery.get('running_containers', []))} running: {', '.join(discovery.get('running_containers', [])[:8])}"
        )

        memories = MemoryService.list_memories(db, agent_id="techy", limit=4)
        memory_context = (
            "\n".join([f"- [{m.type}] {m.content}" for m in memories])
            if memories
            else "No prior infrastructure memories."
        )

        system_prompt = self._build_system_prompt(techy_agent, discovery_summary, memory_context)

        # Chat message history for the LLM
        conversation: List[Dict[str, str]] = [
            {
                "role": "user",
                "content": f"TASK OBJECTIVE:\n{instruction}\n\nInspect the server, execute necessary tools, verify results, and complete the objective.",
            }
        ]

        steps: List[TechyStepRecord] = []
        action_history: List[str] = []
        final_answer = ""
        learned_fact: Optional[str] = None
        task_status = "COMPLETED"
        task_error = None

        logger.info(f"Starting Techy loop for task {task.id} (model={model})", extra={"component": "techy_loop"})

        # 4. Multi-step Autonomous Execution Loop
        for step_num in range(1, max_steps + 1):
            elapsed = time.perf_counter() - start_loop_time
            if elapsed > timeout_seconds:
                task_status = "FAILED"
                task_error = f"Execution timeout exceeded ({timeout_seconds}s)."
                final_answer = f"Techy timed out after {step_num - 1} steps."
                break

            logger.info(f"Techy step {step_num}/{max_steps}...", extra={"component": "techy_loop", "task": task.id})

            # Call LLM
            try:
                llm_res = self.llm_provider.chat(
                    messages=conversation,
                    model=model,
                    system_prompt=system_prompt,
                    options=techy_options,
                )
                raw_response = llm_res.content
            except Exception as e:
                task_status = "FAILED"
                task_error = f"LLM invocation failed: {str(e)}"
                final_answer = f"Failed to communicate with LLM model {model}."
                break

            action_data, parse_err = self._extract_json_action(raw_response)

            if parse_err or not action_data:
                # Give model feedback to return valid JSON
                conversation.append({"role": "assistant", "content": raw_response})
                conversation.append({
                    "role": "user",
                    "content": f"Error: Your response could not be parsed as valid JSON ({parse_err}). Respond with valid JSON: {{\"thought\": \"...\", \"action\": \"...\", \"args\": {{...}}}}",
                })
                continue

            thought = action_data.get("thought", "")
            action = action_data.get("action", "")
            args = action_data.get("args", {})

            # Check if finished
            if action == "finish":
                final_answer = action_data.get("final_answer", thought or "Objective completed.")
                learned_fact = action_data.get("learned_fact")
                steps.append(
                    TechyStepRecord(
                        step_number=step_num,
                        thought=thought,
                        action="finish",
                        args={},
                        tool_success=True,
                        tool_output="Finish requested by agent",
                    )
                )
                logger.info(f"Techy finished task {task.id} at step {step_num}", extra={"component": "techy_loop"})
                break

            # Handle loop repetition detection (3 identical calls)
            call_sig = f"{action}:{json.dumps(args, sort_keys=True)}"
            action_history.append(call_sig)
            if action_history.count(call_sig) >= 3:
                conversation.append({"role": "assistant", "content": raw_response})
                conversation.append({
                    "role": "user",
                    "content": (
                        f"Warning: You have executed tool '{action}' with identical arguments 3 times. "
                        "Do not repeat the same action. Try a different approach or finish if the objective cannot be met."
                    ),
                })
                continue

            # Execute tool
            step_start = time.perf_counter()
            tool_res = self.tool_registry.execute(name=action, args=args, provider=self.exec_provider)
            step_duration = round((time.perf_counter() - step_start) * 1000, 2)

            step_record = TechyStepRecord(
                step_number=step_num,
                thought=thought,
                action=action,
                args=args,
                tool_success=tool_res.success,
                tool_output=tool_res.raw_output[:2000] if tool_res.raw_output else "",
                tool_error=tool_res.error,
                duration_ms=step_duration,
            )
            steps.append(step_record)

            # Record Event and Audit
            EventService.create_event(
                db,
                event_type="techy.tool_executed",
                source="techy_agent",
                related_agent_id="techy",
                related_task_id=task.id,
                payload={
                    "step": step_num,
                    "tool": action,
                    "success": tool_res.success,
                    "duration_ms": step_duration,
                },
            )
            AuditService.log(
                db,
                action=f"techy.tool.{action}",
                agent_id="techy",
                task_id=task.id,
                details={"args": args, "success": tool_res.success},
                result="SUCCESS" if tool_res.success else "FAILED",
            )

            # Update conversation history with tool output
            conversation.append({"role": "assistant", "content": json.dumps(action_data)})
            result_str = (
                f"Tool '{action}' Execution Result (success={tool_res.success}):\n"
                f"{tool_res.raw_output or tool_res.error or 'Done.'}"
            )
            conversation.append({
                "role": "user",
                "content": f"{result_str}\n\nAnalyze this result and decide your next action or finish.",
            })

        else:
            # Loop ended by reaching max_steps without "finish"
            task_status = "BLOCKED"
            final_answer = f"Techy reached maximum step limit ({max_steps}) before explicit completion."

        total_duration_ms = round((time.perf_counter() - start_loop_time) * 1000, 2)

        # 5. Persist learned fact into permanent memory if provided
        if learned_fact and isinstance(learned_fact, str) and len(learned_fact.strip()) > 5:
            try:
                MemoryService.create_memory(
                    db,
                    MemoryCreate(
                        agent_id="techy",
                        type="PROJECT" if project_id else "LONG_TERM",
                        content=learned_fact.strip(),
                        importance=8,
                        metadata_json={"source_task": task.id},
                    ),
                )
            except Exception as e:
                logger.warning(f"Could not save learned fact to memory: {e}")

        # 6. Update Task Record in DB
        task.status = task_status
        task.progress = 100 if task_status == "COMPLETED" else 80
        task.result = {
            "final_answer": final_answer,
            "steps_count": len(steps),
            "execution_time_ms": total_duration_ms,
            "steps": [s.model_dump() for s in steps],
        }
        task.error = task_error
        db.commit()
        db.refresh(task)

        # Emits completion event & audit log
        event_name = "task.completed" if task_status == "COMPLETED" else "task.failed"
        EventService.create_event(
            db,
            event_type=event_name,
            source="techy_agent",
            related_agent_id="techy",
            related_task_id=task.id,
            related_project_id=project_id,
            payload={"status": task_status, "steps": len(steps)},
        )
        AuditService.log(
            db,
            action=event_name,
            agent_id="techy",
            task_id=task.id,
            project_id=project_id,
            details={"status": task_status, "steps": len(steps)},
            result=task_status,
        )

        return TechyExecuteResponse(
            success=(task_status == "COMPLETED"),
            task_id=task.id,
            status=task_status,
            steps_count=len(steps),
            execution_time_ms=total_duration_ms,
            final_answer=final_answer,
            steps=steps,
            error=task_error,
        )
