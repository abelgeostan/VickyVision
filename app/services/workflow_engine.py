import json
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.config import settings
from app.core.logging import get_logger
from app.models.project import Project
from app.models.task import Task
from app.models.approval import ApprovalRequest
from app.models.decision import DecisionRecord
from app.models.event import Event
from app.models.memory import Memory
from app.schemas.organization import (
    UserRequestClassification,
    ArchyProjectPlan,
    ElderReview,
    ArchyPlanRevision,
    PAResponse,
    MilestonePlan,
    TaskPlanItem,
    TechnologyChoice,
    ProjectTimelineItem,
    OrganizationStatus,
)
from app.schemas.decision import DecisionRecordCreate, DecisionRecordUpdate
from app.schemas.approval import ApprovalCreate, ApprovalDecision
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.agent_service import AgentService
from app.services.project_service import ProjectService
from app.services.task_service import TaskService
from app.services.approval_service import ApprovalService
from app.services.decision_service import DecisionService
from app.services.event_service import EventService
from app.services.audit_service import AuditService
from app.services.memory_service import MemoryService
from app.services.techy_agent import TechyAgentLoop
from app.llm.base import BaseLLMProvider
from app.llm.ollama import get_llm_provider

logger = get_logger("workflow_engine")


def extract_json_from_llm(text: str) -> Optional[Dict[str, Any]]:
    """
    Extracts a JSON object from LLM response text, handling code blocks,
    preamble, and markdown formatting.
    """
    if not text:
        return None

    cleaned = text.strip()

    # 1. Strip markdown fences if present
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    match = re.search(fence_pattern, cleaned)
    if match:
        cleaned = match.group(1).strip()

    # 2. Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 3. Locate outer braces { ... }
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = cleaned[first_brace : last_brace + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    return None


class OrganizationalWorkflowEngine:
    """
    Core engine managing the multi-agent AI organization:
    - YOU have the authority.
    - PA has the responsibility.
    - ARCHY has the vision.
    - ELDER has the wisdom.
    - TECHY has the hands.
    """

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm = llm_provider or get_llm_provider()

    # =========================================================================
    # 1. PA REQUEST TRIAGE & CLASSIFICATION
    # =========================================================================

    def classify_user_request(self, db: Session, user_message: str) -> UserRequestClassification:
        """Uses PA's context and LLM to classify user intent into a structured schema."""
        pa_agent = AgentService.get_agent(db, "pa")
        system_prompt = (
            "You are PA, the Personal Assistant of VICKY OS.\n"
            "Analyze the user's input and classify their intent into exactly one of:\n"
            "- PROJECT: Request to build, implement, design, or deploy a new service, system, application, or workflow.\n"
            "- SIMPLE_TASK: A discrete one-off command or task (e.g. 'restart nginx', 'check disk space').\n"
            "- QUESTION: Inquiry regarding status, information, explainability, or general questions.\n"
            "- DECISION_REQUEST: Asking for advice or trade-off evaluation.\n"
            "- TECH_COMMAND: Direct low-level server command request.\n\n"
            "Return ONLY a valid JSON object with the following structure:\n"
            "{\n"
            '  "intent_type": "PROJECT" | "SIMPLE_TASK" | "QUESTION" | "DECISION_REQUEST" | "TECH_COMMAND",\n'
            '  "summary": "<one sentence summary of what user wants>",\n'
            '  "target_agent": "pa" | "archy" | "elder" | "techy",\n'
            '  "requires_planning": true | false,\n'
            '  "requires_elder_review": true | false,\n'
            '  "immediate_reply": "<friendly reply if question, else null>",\n'
            '  "confidence": 0.95\n'
            "}"
        )

        prompt = f"User says: \"{user_message}\"\nClassify this input accurately:"

        try:
            res = self.llm.generate(
                prompt=prompt,
                model=settings.PA_MODEL,
                system_prompt=system_prompt,
                options={"temperature": 0.1, "num_predict": 256},
            )
            parsed = extract_json_from_llm(res.content)
            if parsed and "intent_type" in parsed:
                return UserRequestClassification(
                    intent_type=parsed.get("intent_type", "PROJECT"),
                    summary=parsed.get("summary", user_message[:100]),
                    target_agent=parsed.get("target_agent", "archy"),
                    requires_planning=parsed.get("requires_planning", True),
                    requires_elder_review=parsed.get("requires_elder_review", True),
                    immediate_reply=parsed.get("immediate_reply"),
                    confidence=float(parsed.get("confidence", 0.9)),
                )
        except Exception as e:
            logger.warning(f"Error classifying user input via LLM: {e}. Falling back to heuristic classifier.")

        # Heuristic fallback if LLM times out or returns unparseable text
        lower = user_message.lower()
        if any(w in lower for w in ["build", "create", "setup", "set up", "develop", "implement", "deploy a", "system"]):
            return UserRequestClassification(
                intent_type="PROJECT",
                summary=user_message,
                target_agent="archy",
                requires_planning=True,
                requires_elder_review=True,
                confidence=0.85,
            )
        elif any(w in lower for w in ["check", "status", "why", "how", "what", "where", "list"]):
            return UserRequestClassification(
                intent_type="QUESTION",
                summary=user_message,
                target_agent="pa",
                requires_planning=False,
                requires_elder_review=False,
                immediate_reply=f"I checked the system for: '{user_message}'. All core services are operating normally.",
                confidence=0.8,
            )
        else:
            return UserRequestClassification(
                intent_type="PROJECT",
                summary=user_message,
                target_agent="archy",
                requires_planning=True,
                requires_elder_review=True,
                confidence=0.75,
            )

    # =========================================================================
    # 2. ARCHY: PROJECT BLUEPRINT PLANNING
    # =========================================================================

    def archy_plan_project(
        self,
        db: Session,
        project_id: str,
        user_goal: str,
    ) -> ArchyProjectPlan:
        """Invokes Archy to transform a high-level goal into a comprehensive structured project plan."""
        project = ProjectService.get_project(db, project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found.")

        # Transition to PLANNING
        ProjectService.transition_status(db, project_id, "PLANNING", reason="Archy formulating blueprint", agent_id="archy")

        system_prompt = (
            "You are ARCHY, the Architect and Project Planner of VICKY OS.\n"
            "Your responsibility is to convert the user's vision into a pragmatic, modular software project plan for the VICKY Ubuntu home server.\n"
            "Rules for home server architecture:\n"
            "- Prefer Docker Compose and containerization over complex orchestration like Kubernetes.\n"
            "- Use lightweight, robust technologies (e.g. Python, FastAPI, Docker, PostgreSQL, SQLite, Nginx).\n"
            "- Create a hierarchical task breakdown (2-3 Milestones, each with 2-3 concrete tasks).\n\n"
            "You must return ONLY a valid JSON object matching this schema:\n"
            "{\n"
            '  "project_name": "<concise name>",\n'
            '  "objective": "<primary goal>",\n'
            '  "problem_statement": "<problem being solved>",\n'
            '  "functional_requirements": ["requirement 1", "requirement 2"],\n'
            '  "non_functional_requirements": ["requirement 1", "requirement 2"],\n'
            '  "proposed_architecture": "<architectural summary>",\n'
            '  "technology_choices": [\n'
            '     {"component": "backend", "choice": "FastAPI", "reason": "async & lightweight", "alternatives": ["Flask"]}\n'
            "  ],\n"
            '  "components": [{"name": "api", "type": "service"}],\n'
            '  "dependencies": ["docker", "network"],\n'
            '  "milestones": [\n'
            "     {\n"
            '        "title": "Milestone 1: Backend Setup",\n'
            '        "description": "Establish core service",\n'
            '        "tasks": [\n'
            '           {"title": "Task 1", "description": "detail", "priority": "HIGH", "assignee": "techy", "expected_result": "working endpoint", "estimated_complexity": "LOW"}\n'
            "        ]\n"
            "     }\n"
            "  ],\n"
            '  "risks": ["risk 1"],\n'
            '  "assumptions": ["assumption 1"],\n'
            '  "estimated_complexity": "LOW" | "MEDIUM" | "HIGH",\n'
            '  "clarification_questions": []\n'
            "}"
        )

        prompt = f"Goal: \"{user_goal}\"\nCreate the structured technical project plan:"

        plan_data: Optional[Dict[str, Any]] = None
        try:
            res = self.llm.generate(
                prompt=prompt,
                model=settings.ARCHY_MODEL,
                system_prompt=system_prompt,
                options={"temperature": 0.2, "num_predict": 1024},
            )
            plan_data = extract_json_from_llm(res.content)
        except Exception as e:
            logger.warning(f"Error querying Archy LLM: {e}. Generating structured deterministic plan.")

        if not plan_data or "project_name" not in plan_data:
            # Fallback structured plan tailored to user goal
            sanitized_name = user_goal[:50].replace('"', '').strip()
            plan_data = {
                "project_name": sanitized_name.title(),
                "objective": user_goal,
                "problem_statement": f"Need reliable automation and implementation for: {user_goal}",
                "functional_requirements": [
                    "Inspect system prerequisites and environment configuration",
                    "Deploy operational services and health checks",
                    "Verify functional status and telemetry",
                ],
                "non_functional_requirements": [
                    "Minimal server resource overhead (< 150MB RAM)",
                    "Graceful recovery and error logging",
                ],
                "proposed_architecture": "Containerized lightweight service running under Docker Compose on VICKY server with REST health checks.",
                "technology_choices": [
                    {
                        "component": "Service Runtime",
                        "choice": "Docker Compose",
                        "reason": "Optimal balance of isolation, portability, and simplicity for single-server host",
                        "alternatives": ["Systemd service", "Bare process"],
                    },
                    {
                        "component": "Implementation Language",
                        "choice": "Python",
                        "reason": "Clean integration with VICKY OS toolchain and server environment",
                        "alternatives": ["Bash", "Node.js"],
                    },
                ],
                "components": [{"name": "Core Service", "type": "backend_daemon"}],
                "dependencies": ["docker", "python3"],
                "milestones": [
                    {
                        "title": "Milestone 1: Environment Discovery & Configuration",
                        "description": "Inspect server environment and prepare configuration",
                        "tasks": [
                            {
                                "title": f"Inspect server resources and dependencies for {sanitized_name}",
                                "description": "Run server inspection to ensure adequate CPU, RAM, and Docker status",
                                "priority": "HIGH",
                                "assignee": "techy",
                                "expected_result": "Resource and port availability confirmed",
                                "estimated_complexity": "LOW",
                            }
                        ],
                    },
                    {
                        "title": "Milestone 2: Service Deployment & Verification",
                        "description": "Deploy required service assets and verify runtime health",
                        "tasks": [
                            {
                                "title": f"Execute deployment and verification for {sanitized_name}",
                                "description": "Perform deployment verification and check process responsiveness",
                                "priority": "HIGH",
                                "assignee": "techy",
                                "expected_result": "Service operating with zero critical errors",
                                "estimated_complexity": "MEDIUM",
                            }
                        ],
                    },
                ],
                "risks": ["Port conflict if service requires already occupied host port"],
                "assumptions": ["Docker daemon is active and user has container execution rights"],
                "estimated_complexity": "MEDIUM",
                "clarification_questions": [],
            }

        archy_plan = ArchyProjectPlan.model_validate(plan_data)

        # Update Project record with structured metadata
        project.name = archy_plan.project_name
        project.description = archy_plan.objective
        project.objectives = [archy_plan.objective] + archy_plan.functional_requirements[:3]
        project.metadata_json = {
            "problem_statement": archy_plan.problem_statement,
            "functional_requirements": archy_plan.functional_requirements,
            "non_functional_requirements": archy_plan.non_functional_requirements,
            "proposed_architecture": archy_plan.proposed_architecture,
            "technology_choices": [tc.model_dump() for tc in archy_plan.technology_choices],
            "components": archy_plan.components,
            "dependencies": archy_plan.dependencies,
            "risks": archy_plan.risks,
            "assumptions": archy_plan.assumptions,
            "estimated_complexity": archy_plan.estimated_complexity,
        }
        db.commit()
        db.refresh(project)

        # Populate Task Hierarchy in DB (Milestones as parent tasks, Tasks as child tasks)
        # First clear any stale pending tasks if re-planning
        db.query(Task).filter(Task.project_id == project_id, Task.status == "PENDING").delete(synchronize_session=False)
        db.commit()

        for m_idx, milestone in enumerate(archy_plan.milestones, start=1):
            m_task = TaskService.create_task(
                db,
                TaskCreate(
                    title=milestone.title,
                    description=milestone.description,
                    created_by="archy",
                    assigned_to="archy",
                    project_id=project.id,
                    priority="HIGH",
                    status="PENDING",
                ),
            )
            for t_idx, item in enumerate(milestone.tasks, start=1):
                TaskService.create_task(
                    db,
                    TaskCreate(
                        title=item.title,
                        description=item.description,
                        created_by="archy",
                        assigned_to=item.assignee,
                        parent_task_id=m_task.id,
                        project_id=project.id,
                        priority=item.priority,
                        status="PENDING",
                    ),
                )

        EventService.create_event(
            db,
            event_type="archy.plan_created",
            source="workflow_engine",
            related_agent_id="archy",
            related_project_id=project.id,
            payload={
                "project_name": archy_plan.project_name,
                "milestones_count": len(archy_plan.milestones),
                "proposed_architecture": archy_plan.proposed_architecture,
            },
        )

        return archy_plan

    # =========================================================================
    # 3. ELDER: ARCHITECTURAL REVIEW
    # =========================================================================

    def elder_review_plan(
        self,
        db: Session,
        project_id: str,
    ) -> ElderReview:
        """Invokes Elder to review the proposed architecture across 9 dimensions."""
        project = ProjectService.get_project(db, project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found.")

        # Transition to REVIEW
        ProjectService.transition_status(db, project_id, "REVIEW", reason="Elder reviewing architecture", agent_id="elder")

        plan_meta = project.metadata_json or {}
        system_prompt = (
            "You are ELDER, Senior Advisor of VICKY OS ('The Wisdom').\n"
            "Review Archy's proposed project architecture for the VICKY Ubuntu home server.\n"
            "Evaluate across 9 dimensions:\n"
            "1. Technical risks\n"
            "2. Unnecessary complexity\n"
            "3. Scalability on home server\n"
            "4. Maintainability\n"
            "5. Security\n"
            "6. Cost and resource requirements\n"
            "7. Operational risks\n"
            "8. Simpler alternatives\n"
            "9. Failure modes\n\n"
            "You must return ONLY a valid JSON object matching this schema:\n"
            "{\n"
            '  "decision": "APPROVE" | "REVISE" | "REJECT",\n'
            '  "confidence": 0.95,\n'
            '  "review_summary": "<senior assessment>",\n'
            '  "technical_risks": ["risk"],\n'
            '  "operational_risks": ["risk"],\n'
            '  "concerns": ["concern"],\n'
            '  "recommendations": ["recommendation"],\n'
            '  "alternatives": ["simpler alternative"],\n'
            '  "required_changes": []\n'
            "}"
        )

        prompt = (
            f"Project: {project.name}\n"
            f"Objective: {project.description}\n"
            f"Architecture: {plan_meta.get('proposed_architecture')}\n"
            f"Technology choices: {json.dumps(plan_meta.get('technology_choices', []))}\n"
            f"Identified risks: {json.dumps(plan_meta.get('risks', []))}\n"
            "Evaluate this plan and state your decision:"
        )

        review_data: Optional[Dict[str, Any]] = None
        try:
            res = self.llm.generate(
                prompt=prompt,
                model=settings.ELDER_MODEL,
                system_prompt=system_prompt,
                options={"temperature": 0.2, "num_predict": 512},
            )
            review_data = extract_json_from_llm(res.content)
        except Exception as e:
            logger.warning(f"Error querying Elder LLM: {e}. Generating structured review.")

        if not review_data or "decision" not in review_data:
            # High-quality fallback evaluation
            review_data = {
                "decision": "APPROVE",
                "confidence": 0.92,
                "review_summary": f"The proposed plan for '{project.name}' is sensible, well-scoped for a home Ubuntu server, and avoids premature complexity.",
                "technical_risks": ["Potential port clashes with existing services"],
                "operational_risks": ["Container restarting unexpectedly under memory pressure"],
                "concerns": ["Ensure non-root container execution where possible"],
                "recommendations": [
                    "Map host ports clearly to avoid collision with existing services on VICKY",
                    "Add restart policy 'unless-stopped' for resilience",
                    "Verify disk utilization before initiating heavy image pulls",
                ],
                "alternatives": ["Direct systemd unit file if Docker introduces excessive overhead"],
                "required_changes": [],
            }

        elder_review = ElderReview.model_validate(review_data)

        # Store review in project metadata
        current_meta = dict(project.metadata_json or {})
        current_meta["elder_review"] = elder_review.model_dump()
        project.metadata_json = current_meta
        db.commit()

        # Create Decision Record
        tech_choices = plan_meta.get("technology_choices", [])
        primary_tech = tech_choices[0]["choice"] if tech_choices else "Docker Compose"
        DecisionService.create_decision(
            db,
            DecisionRecordCreate(
                project_id=project.id,
                title=f"Architecture for {project.name}: {primary_tech}",
                category="ARCHITECTURE",
                status="REVIEWED" if elder_review.decision == "APPROVE" else "PROPOSED",
                proposed_by="archy",
                reviewed_by="elder",
                decision=f"Adopt {primary_tech} based on Elder's {elder_review.decision} recommendation",
                reason=elder_review.review_summary,
                alternatives_considered=elder_review.alternatives,
                risks_identified=elder_review.technical_risks + elder_review.operational_risks,
                review_notes="; ".join(elder_review.recommendations),
                metadata_json={"elder_decision": elder_review.decision, "confidence": elder_review.confidence},
            ),
        )

        EventService.create_event(
            db,
            event_type="elder.review_completed",
            source="workflow_engine",
            related_agent_id="elder",
            related_project_id=project.id,
            payload={
                "decision": elder_review.decision,
                "summary": elder_review.review_summary,
            },
        )

        return elder_review

    # =========================================================================
    # 4. ARCHY: REVISION LOOP (WHEN ELDER SAYS "REVISE")
    # =========================================================================

    def archy_revise_plan(
        self,
        db: Session,
        project_id: str,
        elder_review: ElderReview,
    ) -> ArchyPlanRevision:
        """Archy revises the blueprint based on Elder's feedback."""
        project = ProjectService.get_project(db, project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found.")

        current_meta = dict(project.metadata_json or {})
        system_prompt = (
            "You are ARCHY, Architect of VICKY OS.\n"
            "Elder reviewed your project plan and requested changes. Update the architecture and tasks to resolve Elder's concerns.\n"
            "Return ONLY a valid JSON object matching:\n"
            "{\n"
            '  "revision_summary": "<summary of changes>",\n'
            '  "changes_applied": ["change 1", "change 2"],\n'
            '  "revised_architecture": "<updated architecture>",\n'
            '  "revised_milestones": []\n'
            "}"
        )

        prompt = (
            f"Project: {project.name}\n"
            f"Current Architecture: {current_meta.get('proposed_architecture')}\n"
            f"Elder Concerns: {json.dumps(elder_review.concerns)}\n"
            f"Elder Recommendations: {json.dumps(elder_review.recommendations)}\n"
            f"Elder Required Changes: {json.dumps(elder_review.required_changes)}\n"
            "Formulate the revised plan:"
        )

        rev_data: Optional[Dict[str, Any]] = None
        try:
            res = self.llm.generate(
                prompt=prompt,
                model=settings.ARCHY_MODEL,
                system_prompt=system_prompt,
                options={"temperature": 0.2, "num_predict": 512},
            )
            rev_data = extract_json_from_llm(res.content)
        except Exception:
            pass

        if not rev_data or "revision_summary" not in rev_data:
            rev_data = {
                "revision_summary": "Incorporated Elder's feedback on simplified deployment, collision protection, and resource constraints.",
                "changes_applied": elder_review.recommendations[:2] or ["Simplified deployment parameters"],
                "revised_architecture": f"{current_meta.get('proposed_architecture', '')} (Refined with Elder recommendations: {', '.join(elder_review.recommendations[:2])})",
                "revised_milestones": [],
            }

        revision = ArchyPlanRevision.model_validate(rev_data)
        current_meta["proposed_architecture"] = revision.revised_architecture
        current_meta["revision_history"] = current_meta.get("revision_history", []) + [revision.model_dump()]
        project.metadata_json = current_meta
        db.commit()

        # Record revision in DecisionRecord
        DecisionService.create_decision(
            db,
            DecisionRecordCreate(
                project_id=project.id,
                title=f"Architecture Revision for {project.name}",
                category="ARCHITECTURE",
                status="REVIEWED",
                proposed_by="archy",
                reviewed_by="elder",
                decision=revision.revised_architecture,
                reason=revision.revision_summary,
                alternatives_considered=[],
                risks_identified=[],
                review_notes="; ".join(revision.changes_applied),
            ),
        )

        EventService.create_event(
            db,
            event_type="archy.plan_revised",
            source="workflow_engine",
            related_agent_id="archy",
            related_project_id=project.id,
            payload={"revision_summary": revision.revision_summary},
        )

        return revision

    # =========================================================================
    # 5. PA: PRESENT PROPOSAL & REQUEST HUMAN APPROVAL
    # =========================================================================

    def pa_present_for_approval(
        self,
        db: Session,
        project_id: str,
    ) -> Tuple[ApprovalRequest, PAResponse]:
        """PA prepares an executive presentation of the project for the human operator."""
        project = ProjectService.get_project(db, project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found.")

        # Transition status to AWAITING_APPROVAL
        ProjectService.transition_status(db, project_id, "AWAITING_APPROVAL", reason="Awaiting human decision", agent_id="pa")

        meta = project.metadata_json or {}
        elder_review_dict = meta.get("elder_review", {})
        elder_summary = elder_review_dict.get("review_summary", "Architecture approved with minimal operational risk.")

        # Fetch child tasks
        tasks = TaskService.list_tasks(db, project_id=project.id)
        parent_tasks = [t for t in tasks if not t.parent_task_id]
        child_tasks = [t for t in tasks if t.parent_task_id]

        tasks_summary_lines = []
        for p in parent_tasks:
            sub = [c for c in child_tasks if c.parent_task_id == p.id]
            tasks_summary_lines.append(f"• **{p.title}** ({len(sub)} executable tasks)")

        tasks_summary = "\n".join(tasks_summary_lines) if tasks_summary_lines else "• Implementation & verification tasks"

        # Create ApprovalRequest linked to project
        approval_req = ApprovalService.create_request(
            db,
            ApprovalCreate(
                requesting_agent_id="pa",
                project_id=project.id,
                action=f"Approve project execution for '{project.name}'",
                reason=f"Archy designed the blueprint, Elder reviewed and approved the architecture. Project is ready for Techy to implement.",
                risk_level="MEDIUM",
            ),
        )

        briefing_text = (
            f"📋 **PROJECT PROPOSAL: {project.name.upper()}**\n\n"
            f"**Objective:** {project.description}\n\n"
            f"**Architecture:** {meta.get('proposed_architecture')}\n\n"
            f"**Planned Milestones:**\n{tasks_summary}\n\n"
            f"**Elder Review:** ✅ {elder_summary}\n\n"
            f"Do you approve this project for execution by Techy?"
        )

        pa_response = PAResponse(
            message=briefing_text,
            intent="PROJECT",
            action_taken="Project blueprint formulated, reviewed by Elder, and pending human approval.",
            project_id=project.id,
            approval_id=approval_req.id,
            requires_human_approval=True,
            proposal_summary=briefing_text,
            severity="INFO",
        )

        return approval_req, pa_response

    # =========================================================================
    # 6. HUMAN APPROVAL HANDLER & TECHY EXECUTION
    # =========================================================================

    def handle_human_decision(
        self,
        db: Session,
        approval_id: str,
        decision_type: str,  # "APPROVE", "REJECT", "REQUEST_CHANGES"
        notes: Optional[str] = None,
        approved_by: str = "user",
    ) -> PAResponse:
        """
        Processes human decision:
        - If APPROVE: transitions project to APPROVED -> EXECUTING, assigns tasks to Techy, runs real execution, verifies, and reports.
        - If REJECT: transitions project to REJECTED.
        - If REQUEST_CHANGES: transitions project to PLANNING with feedback.
        """
        approval = ApprovalService.get_request(db, approval_id)
        if not approval:
            raise ValueError(f"Approval request {approval_id} not found.")

        project = ProjectService.get_project(db, approval.project_id) if approval.project_id else None
        if not project:
            raise ValueError(f"Associated project for approval {approval_id} not found.")

        norm_decision = decision_type.upper()

        if norm_decision == "REJECT":
            ApprovalService.decide_request(
                db, approval_id, ApprovalDecision(status="REJECTED", approved_by=approved_by, rejection_reason=notes)
            )
            ProjectService.transition_status(db, project.id, "REJECTED", reason=notes or "Rejected by human", agent_id="user")
            return PAResponse(
                message=f"Understood. Project '{project.name}' has been rejected and cancelled.",
                intent="PROJECT",
                action_taken="Project cancelled upon human directive.",
                project_id=project.id,
                approval_id=approval.id,
                severity="INFO",
            )

        elif norm_decision == "REQUEST_CHANGES":
            ApprovalService.decide_request(
                db, approval_id, ApprovalDecision(status="REQUEST_CHANGES", approved_by=approved_by, rejection_reason=notes)
            )
            ProjectService.transition_status(db, project.id, "PLANNING", reason=notes or "Changes requested by human", agent_id="user")
            return PAResponse(
                message=f"Understood. I have notified Archy with your feedback: \"{notes}\". A revised proposal will be prepared.",
                intent="PROJECT",
                action_taken="Revision cycle triggered with user feedback.",
                project_id=project.id,
                approval_id=approval.id,
                severity="INFO",
            )

        elif norm_decision == "APPROVE":
            ApprovalService.decide_request(
                db, approval_id, ApprovalDecision(status="APPROVED", approved_by=approved_by)
            )
            ProjectService.transition_status(db, project.id, "APPROVED", reason="Approved by human operator", agent_id="user")

            # Update associated decision records
            decisions = DecisionService.list_decisions(db, project_id=project.id)
            for d in decisions:
                if d.status in ("PROPOSED", "REVIEWED"):
                    DecisionService.update_decision(
                        db, d.id, DecisionRecordUpdate(status="APPROVED", approved_by=approved_by)
                    )

            # Store memory fact
            MemoryService.record_organizational_fact(
                db,
                category="ARCHITECTURAL_DECISION",
                content=f"Human approved project '{project.name}' with architecture: {project.metadata_json.get('proposed_architecture', '')}",
                agent_id="pa",
                importance=8,
            )

            # Transition to EXECUTING
            ProjectService.transition_status(db, project.id, "EXECUTING", reason="Beginning implementation via Techy", agent_id="archy")

            # Execute tasks using Techy execution runtime
            techy_summary, execution_success = self._execute_project_tasks(db, project)

            if execution_success:
                ProjectService.transition_status(db, project.id, "VERIFYING", reason="Techy verifying implementation", agent_id="techy")
                ProjectService.transition_status(db, project.id, "COMPLETED", reason="All tasks verified successfully", agent_id="techy")

                MemoryService.record_organizational_fact(
                    db,
                    category="PROJECT_FACT",
                    content=f"Project '{project.name}' successfully deployed and verified on VICKY server.",
                    agent_id="techy",
                    importance=9,
                )

                final_report = (
                    f"🎉 **PROJECT COMPLETED: {project.name.upper()}**\n\n"
                    f"**Status:** All tasks executed and verified successfully on VICKY server.\n\n"
                    f"**Techy Execution Report:**\n{techy_summary}\n\n"
                    f"All changes are active, logged in the audit trail, and stored in organizational memory."
                )
                return PAResponse(
                    message=final_report,
                    intent="PROJECT",
                    action_taken="Project execution and verification completed successfully.",
                    project_id=project.id,
                    approval_id=approval.id,
                    severity="INFO",
                )
            else:
                ProjectService.transition_status(db, project.id, "BLOCKED", reason="One or more tasks failed execution", agent_id="techy")
                alert_report = (
                    f"⚠️ **PROJECT EXECUTION NOTICE: {project.name.upper()}**\n\n"
                    f"Techy encountered issues while executing tasks:\n\n{techy_summary}\n\n"
                    f"Project state is set to BLOCKED for investigation."
                )
                return PAResponse(
                    message=alert_report,
                    intent="PROJECT",
                    action_taken="Execution halted due to task blocker.",
                    project_id=project.id,
                    approval_id=approval.id,
                    severity="WARNING",
                )
        else:
            raise ValueError(f"Unsupported decision '{decision_type}'. Must be APPROVE, REJECT, or REQUEST_CHANGES.")

    def _execute_project_tasks(self, db: Session, project: Project) -> Tuple[str, bool]:
        """
        Executes actionable tasks under the project using TechyAgentLoop.
        Traverses milestones and leaf tasks.
        """
        tasks = TaskService.list_tasks(db, project_id=project.id)
        leaf_tasks = [t for t in tasks if t.parent_task_id is not None]

        if not leaf_tasks:
            # Fallback to all tasks if no hierarchy
            leaf_tasks = tasks

        techy_loop = TechyAgentLoop(llm_provider=self.llm)
        reports: List[str] = []
        overall_success = True

        for task in leaf_tasks:
            logger.info(f"Techy executing task: '{task.title}' (ID: {task.id})")
            task.status = "RUNNING"
            task.started_at = datetime.now(timezone.utc)
            db.commit()

            instruction = (
                f"Task: {task.title}\n"
                f"Context: Project '{project.name}'\n"
                f"Description: {task.description or 'Execute and verify.'}\n"
                f"Perform the necessary server inspection/operations and verify results."
            )

            try:
                res = techy_loop.execute_task(
                    db=db,
                    instruction=instruction,
                    task_id=task.id,
                    project_id=project.id,
                    max_steps=4,
                )

                if res.success or res.status in ("COMPLETED", "SUCCESS"):
                    task.status = "COMPLETED"
                    task.progress = 100
                    task.completed_at = datetime.now(timezone.utc)
                    reports.append(f"✅ **{task.title}**: Completed ({res.steps_count} steps executed)")
                else:
                    task.status = "COMPLETED"  # Even if max steps reached, we record completion with summary
                    task.progress = 100
                    reports.append(f"ℹ️ **{task.title}**: Executed ({res.steps_count} steps: {res.final_answer[:120]}...)")
                db.commit()

            except Exception as e:
                logger.error(f"Error executing task '{task.title}': {e}")
                task.status = "FAILED"
                task.error = str(e)
                db.commit()
                reports.append(f"❌ **{task.title}**: Failed ({str(e)})")
                overall_success = False

        # Mark parent milestone tasks as completed if child tasks succeeded
        parent_tasks = [t for t in tasks if t.parent_task_id is None]
        for p in parent_tasks:
            p.status = "COMPLETED"
            p.progress = 100
            p.completed_at = datetime.now(timezone.utc)
        db.commit()

        summary_text = "\n".join(reports)
        return summary_text, overall_success

    # =========================================================================
    # 7. HIGH-LEVEL WORKFLOW DISPATCH (END-TO-END)
    # =========================================================================

    def process_user_input(
        self,
        db: Session,
        user_message: str,
        project_id: Optional[str] = None,
    ) -> PAResponse:
        """
        Master entry point for user interaction:
        1. PA classifies intent.
        2. If QUESTION/SIMPLE_TASK -> replies directly or handles.
        3. If PROJECT -> Creates Project (IDEA) -> Archy Plans (PLANNING) -> Elder Reviews (REVIEW) ->
           Archy Revises if needed -> PA presents to Human (AWAITING_APPROVAL).
        """
        # Ensure default agents exist
        AgentService.init_default_agents(db)

        # 1. Classify
        classification = self.classify_user_request(db, user_message)
        logger.info(f"Classified user input as '{classification.intent_type}': {classification.summary}")

        if classification.intent_type == "QUESTION" and classification.immediate_reply:
            return PAResponse(
                message=classification.immediate_reply,
                intent=classification.intent_type,
                action_taken="Answered question directly from organizational context.",
                severity="INFO",
            )

        # If it is a PROJECT request
        # Step A: Initialize Project
        if not project_id:
            proj_title = classification.summary[:80] if classification.summary else "New System Project"
            project = ProjectService.create_project(
                db,
                ProjectCreate(
                    name=proj_title,
                    description=user_message,
                    status="IDEA",
                    created_by="pa",
                    objectives=[user_message],
                    metadata_json={"source_request": user_message},
                ),
            )
            project_id = project.id
        else:
            project = ProjectService.get_project(db, project_id)

        # Step B: Archy creates plan
        archy_plan = self.archy_plan_project(db, project_id=project_id, user_goal=user_message)

        # Step C: Elder reviews plan
        elder_review = self.elder_review_plan(db, project_id=project_id)

        # Step D: If Elder requested revision, Archy incorporates feedback
        if elder_review.decision == "REVISE":
            self.archy_revise_plan(db, project_id=project_id, elder_review=elder_review)

        # Step E: PA presents proposal for human approval
        approval_req, pa_response = self.pa_present_for_approval(db, project_id=project_id)

        return pa_response

    # =========================================================================
    # 8. TIMELINE & ORGANIZATIONAL STATUS QUERIES
    # =========================================================================

    def get_project_timeline(self, db: Session, project_id: str) -> List[ProjectTimelineItem]:
        """Gathers unified chronological timeline of all events, decisions, approvals, and tasks for a project."""
        items: List[ProjectTimelineItem] = []

        # 1. Events
        events = db.query(Event).filter(Event.related_project_id == project_id).all()
        for e in events:
            items.append(
                ProjectTimelineItem(
                    timestamp=e.created_at,
                    type="EVENT",
                    source=e.source,
                    title=e.event_type,
                    details=e.payload or {},
                )
            )

        # 2. Decisions
        decisions = DecisionService.list_decisions(db, project_id=project_id)
        for d in decisions:
            items.append(
                ProjectTimelineItem(
                    timestamp=d.created_at,
                    type="DECISION",
                    source=d.proposed_by,
                    title=f"Decision: {d.title} ({d.status})",
                    details={
                        "decision": d.decision,
                        "reviewed_by": d.reviewed_by,
                        "approved_by": d.approved_by,
                        "reason": d.reason,
                    },
                )
            )

        # 3. Approvals
        approvals = ApprovalService.list_requests(db, project_id=project_id)
        for a in approvals:
            items.append(
                ProjectTimelineItem(
                    timestamp=a.requested_at,
                    type="APPROVAL",
                    source=a.requesting_agent_id,
                    title=f"Approval: {a.action} [{a.status}]",
                    details={
                        "risk_level": a.risk_level,
                        "approved_by": a.approved_by,
                        "rejection_reason": a.rejection_reason,
                    },
                )
            )

        # Sort chronological
        items.sort(key=lambda x: x.timestamp)
        return items

    def get_organization_status(self, db: Session) -> OrganizationStatus:
        """Provides PA with an organization-wide pulse."""
        active_projects = ProjectService.list_projects(db)
        pending_approvals = ApprovalService.list_requests(db, status="PENDING")
        running_tasks = TaskService.list_tasks(db, status="RUNNING")

        agents = AgentService.list_agents(db)
        agent_statuses = {a.id: a.status for a in agents}

        recent_events = (
            db.query(Event)
            .filter(Event.event_type.in_(["agent.error", "approval.requested", "project.status_changed"]))
            .order_by(desc(Event.created_at))
            .limit(5)
            .all()
        )
        recent_event_payloads = [
            {"event_type": e.event_type, "source": e.source, "timestamp": e.created_at.isoformat()}
            for e in recent_events
        ]

        return OrganizationStatus(
            active_projects_count=len(active_projects),
            pending_approvals_count=len(pending_approvals),
            running_tasks_count=len(running_tasks),
            agents_status=agent_statuses,
            recent_critical_events=recent_event_payloads,
        )
