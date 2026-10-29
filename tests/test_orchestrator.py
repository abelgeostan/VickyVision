from app.services.orchestrator import AgentOrchestrator
from app.api.orchestrator import orchestrator as global_orchestrator
from tests.conftest import MockLLMProvider


def test_orchestrator_routing_without_llm(client, db_session):
    payload = {
        "sender_id": "user",
        "receiver_id": "pa",
        "content": "Good morning PA, please give me a system status update.",
        "message_type": "REQUEST",
        "invoke_agent": False,
    }
    res = client.post("/api/orchestrator/route", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["source_message"]["content"] == payload["content"]
    assert data["agent_response"] is None


def test_orchestrator_routing_with_mock_llm(client, db_session):
    # Inject MockLLMProvider into global orchestrator
    original_llm = global_orchestrator.llm_provider
    global_orchestrator.llm_provider = MockLLMProvider("Greetings user! All systems in VICKY OS are operational.")

    try:
        payload = {
            "sender_id": "user",
            "receiver_id": "pa",
            "content": "Status report, PA?",
            "message_type": "REQUEST",
            "invoke_agent": True,
        }
        res = client.post("/api/orchestrator/route", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["agent_response"] is not None
        assert "Greetings user!" in data["agent_response"]["content"]
        assert data["agent_response"]["sender_id"] == "pa"
        assert data["agent_response"]["receiver_id"] == "user"
    finally:
        global_orchestrator.llm_provider = original_llm


def test_orchestrator_named_flows(client, db_session):
    original_llm = global_orchestrator.llm_provider
    global_orchestrator.llm_provider = MockLLMProvider("Acknowledged and processed.")

    try:
        # Test user_to_pa
        res1 = client.post("/api/orchestrator/flow", json={
            "flow": "user_to_pa",
            "content": "We need to plan a new monitoring service.",
        })
        assert res1.status_code == 200
        assert res1.json()["source_message"]["sender_id"] == "user"
        assert res1.json()["source_message"]["receiver_id"] == "pa"

        # Test archy_to_elder
        res2 = client.post("/api/orchestrator/flow", json={
            "flow": "archy_to_elder",
            "content": "Elder, please review this network architecture for high packet volume.",
        })
        assert res2.status_code == 200
        assert res2.json()["source_message"]["sender_id"] == "archy"
        assert res2.json()["source_message"]["receiver_id"] == "elder"

        # Test archy_to_techy
        res3 = client.post("/api/orchestrator/flow", json={
            "flow": "archy_to_techy",
            "content": "Techy, please implement the ping service backend.",
        })
        assert res3.status_code == 200
        assert res3.json()["source_message"]["sender_id"] == "archy"
        assert res3.json()["source_message"]["receiver_id"] == "techy"
    finally:
        global_orchestrator.llm_provider = original_llm


def test_orchestrator_dispatch_task(client, db_session):
    original_llm = global_orchestrator.llm_provider
    global_orchestrator.llm_provider = MockLLMProvider("Starting implementation now.")

    try:
        # Create a task
        task_res = client.post("/api/tasks", json={
            "title": "Setup firewall rule",
            "description": "Allow TCP port 8090 on UFW",
            "created_by": "archy",
            "assigned_to": "techy",
            "status": "PENDING",
        })
        task_id = task_res.json()["id"]

        # Dispatch
        dispatch_res = client.post("/api/orchestrator/dispatch", json={
            "task_id": task_id,
            "assigned_to": "techy",
            "instruction": "Please execute this firewall setup immediately.",
        })
        assert dispatch_res.status_code == 200
        data = dispatch_res.json()
        assert data["success"] is True
        assert data["task_id"] == task_id

        # Verify task is now RUNNING
        get_task = client.get(f"/api/tasks/{task_id}")
        assert get_task.json()["status"] == "RUNNING"
    finally:
        global_orchestrator.llm_provider = original_llm
