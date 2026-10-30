# VICKY OS — Autonomous Multi-Agent AI Organization (Phases 1, 2, 3 & 4)

**VICKY OS** is a self-hosted, continuously running multi-agent AI organization platform running on local infrastructure, powered by local LLMs via Ollama and PostgreSQL.

- **Phase 1 (Core Platform)**: Agent abstractions, relational persistence, central orchestrator, message flows, hierarchical tasks, events, long-term memory, approval gates, and audit trails.
- **Phase 2 (Autonomous Techy Runtime)**: Full-access server execution runtime (Local + Paramiko SSH), 31 operational system tools, autonomous multi-step execution loop with safety guardrails, automated server discovery, and action verification.
- **Phase 3 (Organizational Intelligence & Multi-Agent Workflow)**: The operational organization structure where:
  - **YOU** have the **authority** (human approval required for impactful changes).
  - **PA** has the **responsibility** (primary user liaison, triage, tracking, progress reporting).
  - **ARCHY** has the **vision** (transforms ideas into structured blueprints, milestones, tasks).
  - **ELDER** has the **wisdom** (evaluates architecture across 9 dimensions, recommends APPROVE/REVISE/REJECT).
  - **TECHY** has the **hands** (executes approved tasks on the live Ubuntu server using Phase 2 tools).
- **Phase 4 (Command Center UI & Real-Time Event Streaming)**: Minimalistic, professional control center built with React 19, TypeScript, and Vite. Features PA chat, agent status monitor, inter-agent conversation explorer, project & task pipelines, executive human approvals gate, Techy live execution logs, server situational awareness, 5-category organizational memory, and Server-Sent Events (SSE) live activity stream.

---

## 🤖 Organizational Agent Roles & Boundaries

| Agent | Identifier | Role & Authority | Core Responsibilities & Boundaries |
| :--- | :--- | :--- | :--- |
| **YOU** | `human` | **Ultimate Authority** | Approves or rejects project proposals, architectural plans, and destructive operations. |
| **PA** | `pa` | **Personal Assistant** | **Responsibility**: First point of contact for the user. Classifies requests (`PROJECT`, `SIMPLE_TASK`, `QUESTION`, `DECISION_REQUEST`, `TECH_COMMAND`). Routes projects to Archy, presents briefs for approval, and reports progress. *Does not execute technical tools directly.* |
| **Archy** | `archy` | **Architect / Planner** | **Vision**: Turns user ideas into concrete project plans, architectural components, milestone plans, and hierarchical task trees. Revises plans based on Elder's feedback. *Does not execute tasks on the server.* |
| **Elder** | `elder` | **Senior Advisor** | **Wisdom**: Evaluates proposed architectures across 9 dimensions (Simplicity, Robustness, Security, Maintainability, Resource Efficiency, Observability, Failure Recovery, Reversibility, Local LLM Feasibility). *Does not plan or execute directly.* |
| **Techy** | `techy` | **Autonomous Engineer** | **Hands**: Autonomous software engineer with unrestricted access to the VICKY Ubuntu server. Executes approved task lists, verifies outcomes, and reports to PA. *Only executes tasks that have been approved.* |

---

## 🏗️ Organizational Architecture & Workflow

```
                             YOU (Human Operator)
                                      │
                                      ▼
                        PA (Personal Assistant)
                                      │
               ┌──────────────────────┴──────────────────────┐
               ▼                                             ▼
        [Request Triage]                              [Final Briefing]
               │                                             ▲
               ▼                                             │
      ARCHY (Architect) ────────► ELDER (Senior Advisor)     │
      • Structured Plan           • 9-Dimension Review       │
      • Milestones & Tasks        • Trade-offs & Risks       │
      • Tech Choices              • APPROVE / REVISE         │
               │                                             │
               └─────────◄ [If Revision Needed] ─────────────┘
               │
               ▼
       [HUMAN APPROVAL GATE] ◄─── (PA presents briefing)
               │ (Approved)
               ▼
       TECHY (Autonomous Engineer)
       • Execution Runtime (Local / SSH to VICKY Server)
       • 31 System Tools (server, docker, git, service, network, fs)
       • Step-by-step verification & failure recovery
               │
               ▼
    [POST-EXECUTION & REPORTING]
       • Archival to Decision Records (decision_records table)
       • Organizational Memory Extraction (5 Categories)
       • PA Executive Summary Delivered to User
```

---

## 🔄 Project Lifecycle State Machine

Projects progress through a strictly audited state machine:

```
[IDEA] ───► [PLANNING] ───► [REVIEW] ───► [AWAITING_APPROVAL]
                                                │
               ┌────────────────────────────────┴────────────────┐
               ▼                                                 ▼
          [REJECTED]                                         [APPROVED]
                                                                 │
                                                                 ▼
                                                            [EXECUTING]
                                                                 │
                                                                 ▼
                                                            [VERIFYING]
                                                                 │
                                                                 ▼
                                                            [COMPLETED]
```

1. **`IDEA`**: The user presents a high-level intent or request to PA.
2. **`PLANNING`**: Archy designs a blueprint containing objectives, milestones, tasks, and tech stack choices.
3. **`REVIEW`**: Elder assesses the plan across 9 architectural dimensions and either approves or requests revisions.
4. **`AWAITING_APPROVAL`**: PA presents an executive briefing, risks, and estimated effort to the human.
5. **`APPROVED`**: The user reviews and approves execution.
6. **`EXECUTING`**: Techy picks up tasks and runs real operations via the execution runtime.
7. **`VERIFYING`**: Techy and the system verify that all steps succeeded and system state is healthy.
8. **`COMPLETED`**: Final status report delivered to PA; decision records and organizational memory persisted.

---

## 🧠 Organizational Memory & Decision Provenance

### 1. Decision Records (`decision_records` table)
Every major architectural evaluation by Elder and every approval/rejection by the user is permanently recorded with full provenance:
- **`title`**, **`category`** (`ARCHITECTURAL`, `OPERATIONAL`, `SECURITY`, `INFRASTRUCTURE`)
- **`proposed_by`** (`archy`), **`reviewed_by`** (`elder`), **`approved_by`** (`human`)
- **`decision`** (`APPROVED`, `REJECTED`, `REVISED`)
- **`reason`**, **`alternatives_considered`**, **`risks_identified`**, **`review_notes`**

### 2. Organizational Memory Categories
Facts discovered during execution and planning are categorized and stored:
- **`USER_PREFERENCE`**: Explicit user desires, habits, and approval thresholds.
- **`PROJECT_FACT`**: Project architecture, dependencies, and configuration decisions.
- **`ARCHITECTURAL_DECISION`**: Key design choices and rationale agreed upon by Archy and Elder.
- **`SERVER_FACT`**: Hardware, network topology, port allocations, and service states on VICKY.
- **`LESSON_LEARNED`**: Operational insights and failure recovery patterns for future tasks.

---

## 🛠️ Techy Tool System (31 Tools)

Techy has unrestricted access to the host server through 31 real operational tools across 6 categories:

| Category | Tools | Description |
| :--- | :--- | :--- |
| **`server.*`** | `execute_command`, `get_system_info`, `get_resources`, `list_processes`, `read_file`, `write_file`, `edit_file`, `search_files` | Execute raw shell commands, inspect CPU/RAM/OS, list processes, and manipulate files with diff inspection. |
| **`docker.*`** | `list_containers`, `container_status`, `logs`, `start`, `stop`, `restart`, `build`, `compose`, `inspect` | Manage containers, inspect logs, run compose operations, and build images. |
| **`git.*`** | `status`, `log`, `diff`, `branch`, `pull`, `checkout` | Inspect and manipulate repositories on the server. |
| **`service.*`** | `status`, `start`, `stop`, `restart`, `logs` | Inspect systemd unit files, manage background daemons, and view journal logs. |
| **`network.*`** | `status`, `connections` | Inspect network interfaces, listening sockets, routing, and open ports. |
| **`filesystem.*`** | `disk_usage` | Inspect partition sizes, available storage, and mount points. |

---

## 🛡️ Autonomous Loop & Guardrails

The `TechyAgentLoop` executes sequential steps autonomously until completion:
1. **Context Assembly**: Injects system prompt, server hardware/container discovery, task context, and relevant memory.
2. **Structured Tool Calling**: Extracts and validates tool calls with argument parsing and fallback alias resolution.
3. **Execution & Feedback**: Runs tools against the server via the configured execution provider (SSH or Local).
4. **Safety & Loop Limits**:
   - `TECHY_MAX_STEPS`: Configurable maximum loop steps (default: 15).
   - `TECHY_LOOP_TIMEOUT_SECONDS`: Total execution timeout (default: 180s).
   - **Repetition Detection**: Detects 3 identical sequential tool actions with identical arguments, issues a corrective hint, and terminates gracefully if persistent.
   - **Secret Redaction**: Automatically scrubs SSH passwords, sudo passwords, and credentials from command logs, outputs, and audit events.
5. **Event & Audit Integration**: Emits lifecycle events (`TECHY_TASK_STARTED`, `TECHY_STEP_EXECUTED`, `TECHY_TASK_COMPLETED`, `TECHY_TASK_FAILED`) and logs every tool invocation to the audit table.
6. **Post-Action Verification**: Verifies outcomes after modifying files, services, or containers.

---

## ⚙️ Configuration (`.env`)

Configuration is managed through environment variables:

```ini
# Server host and port
HOST=0.0.0.0
PORT=8090
ENVIRONMENT=development
LOG_LEVEL=INFO

# Database connection
# Inside Docker:
DATABASE_URL=postgresql://vicky:vickypass@postgres:5432/vicky_os
# Or from external host:
# DATABASE_URL=postgresql+psycopg2://vicky:vickypass@192.168.1.123:5433/vicky_os

# Ollama / Local LLM provider
OLLAMA_BASE_URL=http://192.168.1.123:11434
OLLAMA_TIMEOUT_SECONDS=60.0

# Per-agent model allocations
DEFAULT_MODEL=gemma3:4b
TECHY_MODEL=gemma3:4b
ELDER_MODEL=gemma3:4b
ARCHY_MODEL=gemma3:4b
PA_MODEL=gemma3:4b

# Phase 2: Techy Server Execution
TECHY_EXEC_PROVIDER=ssh           # "ssh" (remote) or "local" (same host)
TECHY_SSH_HOST=192.168.1.123
TECHY_SSH_PORT=22
TECHY_SSH_USER=vickyops
TECHY_SSH_PASSWORD=vickythegoat
TECHY_SSH_KEY_PATH=
TECHY_SUDO_PASSWORD=vickythegoat
TECHY_EXEC_TIMEOUT_SECONDS=30.0
TECHY_MAX_STEPS=15
TECHY_LOOP_TIMEOUT_SECONDS=180.0
```

---

## 🚀 Running VICKY OS

### Option 1: Docker Compose (Production / Server Mode)

Run directly on the home server (`vicky` at `192.168.1.123`):

```bash
# 1. Clone/navigate to project directory
cd /home/vickyops/vicky-os

# 2. Start services (PostgreSQL 16 and VICKY OS Backend)
docker compose up -d --build

# 3. Inspect logs
docker compose logs -f vicky-backend
```

### Option 2: Local Python Development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run database migrations
python -m alembic upgrade head

# 3. Start the application
uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload
```

### Option 3: Running the Frontend Command Center (Phase 4)

The Command Center is located in the `frontend/` directory (React 19, TypeScript, Vite, Tailwind CSS v4, Lucide React).

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies (if not already installed)
npm install

# 3. Start development server (proxies /api to backend at http://127.0.0.1:8090)
npm run dev

# 4. Open in browser: http://localhost:5173
```

To build for production:
```bash
npm run build
# Outputs optimized static bundle to frontend/dist/
```

To run frontend unit tests:
```bash
npm test
```

---

## 🧪 Running Automated Tests

### Backend Tests (44 Tests):
Run the full pytest suite (covering Phase 1 core, Phase 2 Techy execution, Phase 3 organizational workflows, and Phase 4 SSE streaming):

```bash
# Run unit and fast integration tests (44 passed in ~25s)
pytest -m "not slow" --ignore=tests/test_techy_vicky_integration.py -v

# Run live VICKY server + Ollama end-to-end integration tests
pytest tests/test_techy_vicky_integration.py -v -s
```

### Frontend Tests (5 Tests):
```bash
cd frontend
npm test
```

---

## 💻 Frontend Command Center Features (Phase 4)

The web UI provides situational awareness, transparent accountability, and direct human control over the AI organization:

1. **Command Center (`/`)**: High-level organizational status, infrastructure health (Backend, Postgres, Ollama, Techy runtime, SSE stream), agent status cards, active projects, prominent pending approvals alert with 1-click decisions, live activity stream, and authority hierarchy graph.
2. **PA Chat (`/chat`)**: First-class conversational liaison to VICKY OS. Classifies requests, delegates to Archy and Elder, presents inline project proposals with 1-click `[Approve]`, `[Request Changes]`, and `[Reject]` actions, displays background delegation stages, and stores persistent chat history in PostgreSQL.
3. **Agents (`/agents`)**: Real-time status, model configurations, system prompts, core objectives, and responsibilities for PA, Archy, Elder, and Techy.
4. **Conversation Explorer (`/conversations`)**: Unified chronological event and message stream across the entire organization. Filter by agent (`ALL`, `USER`, `PA`, `ARCHY`, `ELDER`, `TECHY`) and type (`MESSAGE`, `TASK`, `TOOL`, `DECISION`, `APPROVAL`, `EVENT`), with detail modal inspection.
5. **Projects (`/projects`)**: Project index with status state machine tracking, architectural blueprints, milestones, tasks, decision records, and unified chronological timeline (`GET /api/org/projects/{id}/timeline`).
6. **Tasks (`/tasks`)**: Operational work items, assigned agents, priorities, progress, execution steps, and verification outputs.
7. **Human Approvals (`/approvals`)**: Executive gate for project blueprints and high-risk actions. Provides one-click decision submission (`APPROVE`, `REQUEST_CHANGES`, `REJECT`) with optional human feedback.
8. **Techy Live Execution (`/execution`)**: Autonomous server engineer runtime monitor. Displays real tool invocations (`server.execute_command`, `docker.list_containers`, `service.logs`), arguments, execution durations, command outputs, and verification results. Also supports direct manual task dispatch.
9. **Server Situational Awareness (`/server`)**: Hardware resource usage (CPU %, Memory %, Disk %), uptime, OS kernel, Docker container states, and discovered listening network ports from `/api/techy/discovery`.
10. **Organizational Memory (`/memory`)**: 5 knowledge categories (`USER_PREFERENCE`, `PROJECT_FACT`, `ARCHITECTURAL_DECISION`, `SERVER_FACT`, `LESSON_LEARNED`) with search and category filtering.
11. **Decision Records (`/decisions`)**: Governance audit trail with visual provenance flow (*User request → PA triage → Archy blueprint → Elder 9-dimension review → Human approval → Decision*).
12. **Real-time Event Stream (SSE)**: Built on `GET /api/events/stream`, automatically refreshing active projects, tasks, approvals, and live activity without manual page reload.

---

## 📡 REST API Reference

- **Interactive Swagger Docs**: `http://<SERVER_IP>:8090/docs`
- **Health Check**: `GET /health` or `GET /api/health`

### Phase 3: Organizational Workflow Endpoints (`/api/org/*`)
- **`POST /api/org/chat`**: Primary entry point for user requests. Triage by PA; if a project, Archy plans it, Elder reviews it, and PA presents it for approval.
- **`POST /api/org/projects/plan`**: Directly invoke Archy to create an architectural blueprint for a goal.
- **`POST /api/org/projects/{id}/review`**: Directly invoke Elder to review an existing project across 9 dimensions.
- **`POST /api/org/approvals/{id}/decide`**: Submit human decision (`APPROVE`, `REJECT`, `REQUEST_CHANGES`). If approved, automatically dispatches Techy to execute and verify tasks.
- **`GET /api/org/decisions`**: Retrieve full decision audit trail with provenance.
- **`GET /api/org/projects/{id}/timeline`**: Retrieve unified chronological timeline of all messages, tasks, reviews, and decisions for a project.
- **`GET /api/org/status`**: Overview of organization health, active projects, pending approvals, and agent statuses.

### Phase 2: Techy Autonomous Execution Endpoints (`/api/techy/*`)
- **`POST /api/techy/execute`**: Submit an objective for Techy to autonomously investigate, execute tools, and report.
- **`POST /api/techy/tool`**: Execute a specific tool directly with arguments.
- **`GET /api/techy/tools`**: List all 31 registered tools and their schemas.
- **`GET /api/techy/discovery`**: View cached server discovery (CPU, RAM, Docker containers, network).
- **`GET /api/techy/runs/{task_id}`**: Retrieve step-by-step execution log, thoughts, tool inputs, and outputs.

### Phase 1: Core System Endpoints
- **Agents**: `GET /api/agents`, `POST /api/agents`, `GET /api/agents/{id}`, `PUT /api/agents/{id}`
- **Projects**: `GET /api/projects`, `POST /api/projects`, `GET /api/projects/{id}`, `PUT /api/projects/{id}`
- **Tasks**: `GET /api/tasks`, `POST /api/tasks`, `GET /api/tasks/{id}`, `PUT /api/tasks/{id}`
- **Messages**: `GET /api/messages`, `POST /api/messages`, `GET /api/messages/{id}`
- **Events**: `GET /api/events`, `POST /api/events`, `GET /api/events/{id}`
- **Memory**: `GET /api/memory`, `POST /api/memory`, `GET /api/memory/{id}`
- **Approvals**: `GET /api/approvals`, `POST /api/approvals`, `POST /api/approvals/{id}/decision`
- **Audit Logs**: `GET /api/audit`, `GET /api/audit/{id}`

---

## 🔄 Example Organizational Workflow Walkthrough

### 1. Submit a Goal to PA

User submits a request to PA:

```bash
curl -X POST http://192.168.1.123:8090/api/org/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want a simple server health dashboard for VICKY."
  }'
```

**Response**: PA classifies request as `PROJECT`, calls Archy to design the blueprint, calls Elder to review across 9 dimensions, transitions project to `AWAITING_APPROVAL`, creates an `ApprovalRequest`, and returns an executive briefing to the human.

### 2. Human Approves the Project

Human submits their approval decision:

```bash
curl -X POST http://192.168.1.123:8090/api/org/approvals/<APPROVAL_ID>/decide \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "APPROVE",
    "notes": "Approved for execution on VICKY server."
  }'
```

**Outcome**:
1. Project transitions to `APPROVED` -> `EXECUTING`.
2. Techy is dispatched with full server access to execute the planned tasks sequentially.
3. System verifies task outcomes and transitions project to `VERIFYING` -> `COMPLETED`.
4. Organizational memories and decision records are persisted.
5. PA delivers a completion summary.

### 3. Inspect Project Timeline

Retrieve the complete multi-agent history of the project:

```bash
curl -X GET http://192.168.1.123:8090/api/org/projects/<PROJECT_ID>/timeline
```

### 4. Inspect Decision Records

Retrieve all architectural and human decisions:

```bash
curl -X GET http://192.168.1.123:8090/api/org/decisions
```
