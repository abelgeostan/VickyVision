def test_task_hierarchical_creation(client):
    # 1. Create a parent task by Archy
    parent_payload = {
        "title": "Build Home Network Monitor",
        "description": "Full end-to-end telemetry system",
        "created_by": "archy",
        "assigned_to": "archy",
        "status": "PLANNING",
        "priority": "HIGH",
    }
    p_res = client.post("/api/tasks", json=parent_payload)
    assert p_res.status_code == 201
    parent_id = p_res.json()["id"]

    # 2. Create subtasks assigned to Techy
    subtask_1 = {
        "title": "Build backend ping scanner",
        "description": "ICMP ping scanner daemon",
        "created_by": "archy",
        "assigned_to": "techy",
        "parent_task_id": parent_id,
        "status": "PENDING",
        "priority": "HIGH",
    }
    s1_res = client.post("/api/tasks", json=subtask_1)
    assert s1_res.status_code == 201
    s1_id = s1_res.json()["id"]
    assert s1_res.json()["parent_task_id"] == parent_id

    # 3. Create second subtask
    subtask_2 = {
        "title": "Build frontend dashboard",
        "description": "Web GUI for telemetry",
        "created_by": "archy",
        "assigned_to": "techy",
        "parent_task_id": parent_id,
        "status": "PENDING",
        "priority": "MEDIUM",
    }
    s2_res = client.post("/api/tasks", json=subtask_2)
    assert s2_res.status_code == 201

    # 4. Update subtask status to RUNNING, then COMPLETED
    up_res = client.put(f"/api/tasks/{s1_id}", json={"status": "RUNNING", "progress": 50})
    assert up_res.status_code == 200
    assert up_res.json()["status"] == "RUNNING"
    assert up_res.json()["started_at"] is not None

    done_res = client.put(f"/api/tasks/{s1_id}", json={"status": "COMPLETED", "progress": 100})
    assert done_res.status_code == 200
    assert done_res.json()["status"] == "COMPLETED"
    assert done_res.json()["completed_at"] is not None

    # 5. List subtasks by parent_task_id
    sub_list = client.get(f"/api/tasks?parent_task_id={parent_id}")
    assert sub_list.status_code == 200
    assert len(sub_list.json()) == 2
