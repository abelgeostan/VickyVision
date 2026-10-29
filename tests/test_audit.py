def test_audit_logs_recorded(client):
    # Perform an operation that logs an audit entry
    agent_payload = {
        "id": "sentinel",
        "name": "Sentinel",
        "role": "Security Auditor",
        "description": "Monitors security compliance",
        "personality": "Strict",
        "objectives": ["Scan configs"],
        "system_prompt": "You are Sentinel...",
        "model_config_data": {},
        "status": "IDLE",
    }
    client.post("/api/agents", json=agent_payload)

    # Query audit logs for agent creation
    res = client.get("/api/audit?action=agent.created")
    assert res.status_code == 200
    logs = res.json()
    assert len(logs) >= 1
    assert any(log["agent_id"] == "sentinel" for log in logs)
