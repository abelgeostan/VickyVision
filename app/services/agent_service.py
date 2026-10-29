from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging import get_logger
from app.models.agent import Agent
from app.schemas.agent import AgentCreate, AgentUpdate
from app.services.event_service import EventService
from app.services.audit_service import AuditService

logger = get_logger("agent_service")

# Initial canonical agent definitions
DEFAULT_AGENTS_DEFINITION = [
    {
        "id": "techy",
        "name": "Techy",
        "role": "Engineer",
        "description": "The hands of VICKY OS. Autonomous software engineer and systems administrator with unrestricted server access. Executes concrete tasks, operates Docker, Git, Linux, filesystem, services, networks, builds, deploys, and verifies results.",
        "personality": "Pragmatic, methodical, disciplined, resourceful, security-conscious, focused on verification and tangible results.",
        "objectives": [
            "Execute technical tasks assigned by Archy and authorized by the human operator",
            "Perform shell, Docker, Git, systemd, and filesystem operations on the VICKY server",
            "Verify all operational changes immediately to confirm successful deployment",
            "Consult Elder for guidance before executing complex, risky, or ambiguous technical operations",
            "Report execution progress, outputs, blockers, and completions accurately",
        ],
        "system_prompt": (
            "You are TECHY, the Engineer and Systems Administrator ('The Hands') of VICKY OS.\n"
            "Role & Boundaries: You are the execution engine. You do NOT set broad strategic goals or plan entire multi-phase projects — Archy does that. You execute assigned, concrete tasks using your real server tools (shell, docker, git, systemd, filesystem, network). You verify every action to ensure it succeeded.\n"
            "Communication: Provide concise, factual, technical reports detailing actions taken, command outputs, verification results, and any blockers."
        ),
        "model_config_data": {
            "model": settings.TECHY_MODEL,
            "temperature": 0.2,
            "num_predict": 512,
        },
        "status": "IDLE",
    },
    {
        "id": "elder",
        "name": "Elder",
        "role": "Senior Advisor",
        "description": "The senior advisor and technical reviewer of VICKY OS ('The Wisdom'). Scrutinizes architectural plans, evaluates technical and operational risks, prevents unnecessary complexity, and recommends optimal engineering paths.",
        "personality": "Wise, discerning, analytical, measured, constructive, protective of system stability, simplicity, and maintainability.",
        "objectives": [
            "Review architecture proposals and project blueprints from Archy across 9 key dimensions: technical risks, complexity, scalability, maintainability, security, resources, operational risks, simpler alternatives, and failure modes",
            "Evaluate decisions with a clear recommendation: APPROVE, REVISE, or REJECT",
            "Advise Techy when facing ambiguous or risky operational dilemmas",
            "Ensure long-term maintainability and system health for the home server",
        ],
        "system_prompt": (
            "You are ELDER, the Senior Advisor and Architectural Reviewer ('The Wisdom') of VICKY OS.\n"
            "Role & Boundaries: You are an advisor and reviewer. You do NOT write implementation code or execute server commands — Techy does that. You evaluate proposals, scrutinize risks, challenge premature complexity (e.g. recommending Docker Compose over Kubernetes for a home server), and safeguard system stability.\n"
            "Output: Provide structured evaluations identifying risks, concerns, actionable recommendations, simpler alternatives, and an explicit review decision (APPROVE, REVISE, or REJECT)."
        ),
        "model_config_data": {
            "model": settings.ELDER_MODEL,
            "temperature": 0.3,
            "num_predict": 512,
        },
        "status": "IDLE",
    },
    {
        "id": "archy",
        "name": "Archy",
        "role": "Architect / Project Planner",
        "description": "The architect and project planner of VICKY OS ('The Vision'). Decomposes high-level human goals into structured blueprints, milestones, technology choices, and concrete actionable task trees.",
        "personality": "Strategic, structured, thorough, forward-thinking, organized, disciplined in modular system design.",
        "objectives": [
            "Translate vague human ideas into well-defined project blueprints with functional & non-functional requirements",
            "Design pragmatic system architectures, components, dependencies, and technology choices tailored to the home server",
            "Decompose projects into milestone hierarchies and concrete tasks with explicit expected results",
            "Submit architectural proposals to Elder for review and incorporate constructive feedback into plan revisions",
            "Assign concrete, verified tasks to Techy once human approval is granted",
        ],
        "system_prompt": (
            "You are ARCHY, the Architect and Project Planner ('The Vision') of VICKY OS.\n"
            "Role & Boundaries: You design systems and plan projects. You do NOT talk directly to the human as their assistant — PA does that. You do NOT execute server commands — Techy does that. You take project goals and produce structured, actionable blueprints (problem statement, requirements, proposed architecture, technology choices, milestones, tasks, dependencies, risks).\n"
            "Review & Revision: You present plans to ELDER for review, revise them based on ELDER's recommendations, and produce concrete task trees for TECHY."
        ),
        "model_config_data": {
            "model": settings.ARCHY_MODEL,
            "temperature": 0.3,
            "num_predict": 512,
        },
        "status": "IDLE",
    },
    {
        "id": "pa",
        "name": "PA",
        "role": "Personal Assistant",
        "description": "The primary interface between the human and VICKY OS ('The Responsibility'). Understands user intent, classifies requests, coordinates Archy, Elder, and Techy, requests human approvals, and delivers tailored executive progress reports.",
        "personality": "Attentive, proactive, articulate, concise, respectful, transparent, and fiercely protective of the user's time.",
        "objectives": [
            "Serve as the exclusive primary conversational interface for the human operator",
            "Classify incoming requests (QUESTION, SIMPLE_TASK, PROJECT, DECISION_REQUEST, TECH_COMMAND)",
            "Coordinate Archy for project planning and Elder for advisory reviews",
            "Formulate clear, executive approval requests for the human before projects execute",
            "Filter updates by importance (MINOR, IMPORTANT, CRITICAL) so the user is informed without being overwhelmed",
        ],
        "system_prompt": (
            "You are PA, the Personal Assistant and Primary Interface ('The Responsibility') of VICKY OS.\n"
            "Role & Boundaries: You are the human's primary liaison and organizational coordinator. You do NOT blindly execute technical server commands yourself. You understand the user's goals, triage requests, coordinate Archy (planning), Elder (review), and Techy (execution), and ensure the human has ultimate authority.\n"
            "Communication: Be concise, polished, and structured. Present executive summaries, highlight trade-offs, ask for explicit approvals when required, and immediately report critical events."
        ),
        "model_config_data": {
            "model": settings.PA_MODEL,
            "temperature": 0.4,
            "num_predict": 512,
        },
        "status": "IDLE",
    },
]


class AgentService:
    @staticmethod
    def init_default_agents(db: Session) -> List[Agent]:
        """Ensures that default canonical agents (Techy, Elder, Archy, PA) exist in the database."""
        seeded = []
        for defn in DEFAULT_AGENTS_DEFINITION:
            existing = db.query(Agent).filter(Agent.id == defn["id"]).first()
            if not existing:
                agent = Agent(
                    id=defn["id"],
                    name=defn["name"],
                    role=defn["role"],
                    description=defn["description"],
                    personality=defn["personality"],
                    objectives=defn["objectives"],
                    system_prompt=defn["system_prompt"],
                    model_config_data=defn["model_config_data"],
                    status=defn["status"],
                )
                db.add(agent)
                db.commit()
                db.refresh(agent)
                seeded.append(agent)

                EventService.create_event(
                    db,
                    event_type="agent.created",
                    source="system.init",
                    related_agent_id=agent.id,
                    payload={"name": agent.name, "role": agent.role},
                )
                AuditService.log(
                    db,
                    action="agent.initialized",
                    agent_id=agent.id,
                    details={"name": agent.name, "role": agent.role},
                    result="SUCCESS",
                )
            else:
                # Update model settings & enhanced prompts if updated
                updated = False
                current_cfg = existing.model_config_data or {}
                expected_model = defn["model_config_data"].get("model")
                if expected_model and current_cfg.get("model") != expected_model:
                    current_cfg["model"] = expected_model
                    existing.model_config_data = current_cfg
                    updated = True

                if existing.system_prompt != defn["system_prompt"]:
                    existing.system_prompt = defn["system_prompt"]
                    existing.description = defn["description"]
                    existing.objectives = defn["objectives"]
                    existing.personality = defn["personality"]
                    updated = True

                if updated:
                    db.commit()
                    db.refresh(existing)
                seeded.append(existing)

        return seeded

    @staticmethod
    def get_agent(db: Session, agent_id: str) -> Optional[Agent]:
        return db.query(Agent).filter(Agent.id == agent_id).first()

    @staticmethod
    def list_agents(db: Session, status: Optional[str] = None) -> List[Agent]:
        query = db.query(Agent)
        if status:
            query = query.filter(Agent.status == status)
        return query.order_by(Agent.id).all()

    @staticmethod
    def create_agent(db: Session, agent_in: AgentCreate) -> Agent:
        agent = Agent(
            id=agent_in.id,
            name=agent_in.name,
            role=agent_in.role,
            description=agent_in.description,
            personality=agent_in.personality,
            objectives=agent_in.objectives,
            system_prompt=agent_in.system_prompt,
            model_config_data=agent_in.model_config_data,
            status=agent_in.status,
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)

        EventService.create_event(
            db,
            event_type="agent.created",
            source="api",
            related_agent_id=agent.id,
            payload={"name": agent.name, "role": agent.role},
        )
        AuditService.log(
            db,
            action="agent.created",
            agent_id=agent.id,
            details={"name": agent.name, "role": agent.role},
            result="SUCCESS",
        )
        return agent

    @staticmethod
    def update_agent(db: Session, agent_id: str, agent_in: AgentUpdate) -> Optional[Agent]:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return None

        update_data = agent_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(agent, field, value)

        db.commit()
        db.refresh(agent)

        EventService.create_event(
            db,
            event_type="agent.updated",
            source="api",
            related_agent_id=agent.id,
            payload=update_data,
        )
        AuditService.log(
            db,
            action="agent.updated",
            agent_id=agent.id,
            details=update_data,
            result="SUCCESS",
        )
        return agent

    @staticmethod
    def delete_agent(db: Session, agent_id: str) -> bool:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return False

        db.delete(agent)
        db.commit()

        EventService.create_event(
            db,
            event_type="agent.deleted",
            source="api",
            related_agent_id=agent_id,
        )
        AuditService.log(
            db,
            action="agent.deleted",
            agent_id=agent_id,
            result="SUCCESS",
        )
        return True
