def test_techy_api_list_tools(client):
    res = client.get("/api/techy/tools")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] >= 30
    assert any(t["name"] == "server.execute_command" for t in data["tools"])
    assert any(t["name"] == "docker.list_containers" for t in data["tools"])
    assert any(t["name"] == "git.status" for t in data["tools"])


def test_techy_api_discovery(client):
    res = client.get("/api/techy/discovery")
    assert res.status_code == 200
    data = res.json()
    assert "discovery" in data
    disc = data["discovery"]
    assert "hostname" in disc
    assert "docker_version" in disc


def test_techy_api_direct_tool_execution(client):
    req = {
        "tool_name": "server.execute_command",
        "args": {"command": "echo 'api_tool_test_ok'"},
    }
    res = client.post("/api/techy/tool", json=req)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "api_tool_test_ok" in data["raw_output"]


def test_techy_api_run_details(client):
    # First create a task via Task API
    task_res = client.post("/api/tasks", json={
        "title": "Check system logs",
        "assigned_to": "techy",
        "status": "COMPLETED",
        "progress": 100,
        "result": {"final_answer": "Logs are clean", "steps_count": 2},
    })
    task_id = task_res.json()["id"]

    # Query run details
    run_res = client.get(f"/api/techy/runs/{task_id}")
    assert run_res.status_code == 200
    run_data = run_res.json()
    assert run_data["task_id"] == task_id
    assert run_data["status"] == "COMPLETED"
    assert run_data["result"]["final_answer"] == "Logs are clean"
