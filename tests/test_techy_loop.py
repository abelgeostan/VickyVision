import json
import pytest
from app.services.techy_agent import TechyAgentLoop
from app.llm.base import BaseLLMProvider, LLMResponse
from app.execution.factory import get_execution_provider
from app.services.task_service import TaskService


class ScriptedMockLLM(BaseLLMProvider):
    """Returns a sequence of pre-scripted JSON tool responses."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.call_count = 0

    def chat(self, messages, model, system_prompt=None, options=None):
        if self.call_count < len(self.responses):
            reply = self.responses[self.call_count]
            self.call_count += 1
            return LLMResponse(content=reply, model=model, total_duration_ms=10.0)
        return LLMResponse(
            content='{"thought": "done", "action": "finish", "final_answer": "Complete"}',
            model=model,
        )

    def generate(self, prompt, model, system_prompt=None, options=None):
        return self.chat([], model)

    def check_health(self):
        return True

    def list_models(self):
        return ["mock-model"]


def test_techy_loop_sequential_execution(db_session):
    scripted_responses = [
        # Step 1: inspect host
        json.dumps({
            "thought": "I will inspect host system information first.",
            "action": "server.get_system_info",
            "args": {},
        }),
        # Step 2: inspect docker
        json.dumps({
            "thought": "Now I will inspect running docker containers.",
            "action": "docker.list_containers",
            "args": {"all": False},
        }),
        # Step 3: finish
        json.dumps({
            "thought": "I have inspected the host and docker containers.",
            "action": "finish",
            "final_answer": "The server is running Ubuntu with healthy Docker containers.",
            "learned_fact": "VICKY server runs Ubuntu 24.04 with Docker 29.",
        }),
    ]

    mock_llm = ScriptedMockLLM(scripted_responses)
    provider = get_execution_provider()
    loop = TechyAgentLoop(execution_provider=provider, llm_provider=mock_llm)

    res = loop.execute_task(
        db=db_session,
        instruction="Inspect system info and running containers",
        max_steps=5,
    )

    assert res.success is True
    assert res.status == "COMPLETED"
    assert res.steps_count == 3
    assert "Ubuntu" in res.final_answer

    # Verify task in DB
    task = TaskService.get_task(db_session, res.task_id)
    assert task.status == "COMPLETED"
    assert task.progress == 100
    assert task.result["steps_count"] == 3


def test_techy_loop_repetition_protection(db_session):
    # Model attempts to repeat identical action 4 times
    scripted_responses = [
        json.dumps({"thought": "repeat", "action": "server.get_system_info", "args": {}}),
        json.dumps({"thought": "repeat", "action": "server.get_system_info", "args": {}}),
        json.dumps({"thought": "repeat", "action": "server.get_system_info", "args": {}}),
        json.dumps({"thought": "breaking out", "action": "finish", "final_answer": "Avoided loop."}),
    ]

    mock_llm = ScriptedMockLLM(scripted_responses)
    loop = TechyAgentLoop(execution_provider=get_execution_provider(), llm_provider=mock_llm)

    res = loop.execute_task(
        db=db_session,
        instruction="Test loop repetition protection",
        max_steps=6,
    )

    assert res.success is True
    assert "Avoided loop" in res.final_answer


def test_techy_loop_max_steps_protection(db_session):
    # Model that calls different commands without finish
    infinite_llm = ScriptedMockLLM([
        json.dumps({"thought": f"step {i}", "action": "server.execute_command", "args": {"command": f"echo {i}"}})
        for i in range(10)
    ])

    loop = TechyAgentLoop(execution_provider=get_execution_provider(), llm_provider=infinite_llm)
    res = loop.execute_task(
        db=db_session,
        instruction="Run forever until max steps",
        max_steps=3,
    )

    assert res.success is False
    assert res.status == "BLOCKED"
    assert res.steps_count == 3
    assert "maximum step limit" in res.final_answer.lower()
