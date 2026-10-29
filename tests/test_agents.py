def test_canonical_agents_exist(client):
    res = client.get("/api/agents")
    assert res.status_code == 200
    agents = res.json()
    agent_ids = [a["id"] for a in agents]

    # Verify all 4 canonical agents exist
    assert "techy" in agent_ids
    assert "elder" in agent_ids
    assert "archy" in agent_ids
    assert "pa" in agent_ids

    # Verify techy's profile
    techy = next(a for a in agents if a["id"] == "techy")
    assert techy["role"] == "Engineer"
    assert "model_config_data" in techy
    assert len(techy["objectives"]) > 0


def test_agent_crud(client):
    # Create dynamic agent
    new_agent = {
        "id": "scout",
        "name": "Scout",
        "role": "Reconnaissance / Security",
        "description": "Monitors network anomalies and logs.",
        "personality": "Vigilant, quiet, observant.",
        "objectives": ["Monitor network ports", "Detect anomalies"],
        "system_prompt": "You are Scout...",
        "model_config_data": {"model": "gemma3:4b", "temperature": 0.1},
        "status": "IDLE",
    }
    create_res = client.post("/api/agents", json=new_agent)
    assert create_res.status_code == 201
    assert create_res.json()["id"] == "scout"

    # Get agent
    get_res = client.get("/api/agents/scout")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Scout"

    # Update agent
    update_res = client.put("/api/agents/scout", json={"status": "ACTIVE"})
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "ACTIVE"

    # Delete agent
    del_res = client.delete("/api/agents/scout")
    assert del_res.status_code == 204
