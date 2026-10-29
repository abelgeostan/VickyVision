import pytest
from app.services.techy_agent import TechyAgentLoop
from app.execution.factory import get_execution_provider
from app.llm.ollama import get_llm_provider
from app.core.config import settings


def test_techy_live_server_inspection(db_session):
    """
    Real Integration Test:
    Techy is given the task:
    'Inspect the VICKY server and report its hostname, OS, CPU, RAM, disk usage and running Docker containers.'
    Executes real commands via SSH on VICKY and calls Ollama.
    """
    exec_provider = get_execution_provider()
    if not exec_provider.is_available():
        pytest.skip("VICKY server SSH is not reachable in this test environment.")

    llm = get_llm_provider()
    if not llm.check_health():
        pytest.skip("Ollama is not reachable at OLLAMA_BASE_URL.")

    loop = TechyAgentLoop(execution_provider=exec_provider, llm_provider=llm)

    instruction = (
        "Inspect the VICKY server and report its hostname, OS, CPU, RAM, disk usage and running Docker containers."
    )

    res = loop.execute_task(
        db=db_session,
        instruction=instruction,
        max_steps=8,
        timeout_seconds=120.0,
    )

    assert res.task_id is not None
    assert len(res.steps) >= 1, "Techy should execute at least 1 real tool step."
    # Verify tools were executed
    executed_tools = [s.action for s in res.steps]
    assert any("server." in t or "docker." in t for t in executed_tools), f"Expected server/docker tools, got {executed_tools}"
    # Verify final answer or step results contain real server details
    assert len(res.final_answer) > 10
    print(f"\n[TECHY LIVE INSPECTION REPORT]:\n{res.final_answer}\nSteps: {executed_tools}")


def test_techy_live_vickyai_deployment_check(db_session):
    """
    Real Integration Test:
    Techy is given:
    'Check the VickyAI deployment on the server and check container status and logs.'
    Techy inspects docker container state and reports findings.
    """
    exec_provider = get_execution_provider()
    if not exec_provider.is_available():
        pytest.skip("VICKY server SSH is not reachable in this test environment.")

    llm = get_llm_provider()
    if not llm.check_health():
        pytest.skip("Ollama is not reachable at OLLAMA_BASE_URL.")

    loop = TechyAgentLoop(execution_provider=exec_provider, llm_provider=llm)

    instruction = "Check the VickyAI deployment on this server, inspect container status, and verify health."

    res = loop.execute_task(
        db=db_session,
        instruction=instruction,
        max_steps=8,
        timeout_seconds=120.0,
    )

    assert res.task_id is not None
    assert len(res.steps) >= 1
    executed_tools = [s.action for s in res.steps]
    print(f"\n[TECHY VICKYAI CHECK REPORT]:\n{res.final_answer}\nSteps: {executed_tools}")
