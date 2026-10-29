def test_project_lifecycle(client):
    payload = {
        "name": "Home Network Monitor",
        "description": "Continuous monitoring of LAN devices and open ports",
        "status": "PLANNING",
        "created_by": "archy",
        "objectives": ["Discover LAN hosts", "Check service health", "Alert on packet drop"],
        "metadata_json": {"target_subnet": "192.168.1.0/24"},
    }
    # Create
    res = client.post("/api/projects", json=payload)
    assert res.status_code == 201
    data = res.json()
    proj_id = data["id"]
    assert data["name"] == "Home Network Monitor"
    assert data["created_by"] == "archy"

    # Get
    get_res = client.get(f"/api/projects/{proj_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == proj_id

    # Update
    update_res = client.put(f"/api/projects/{proj_id}", json={"status": "ACTIVE"})
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "ACTIVE"

    # List
    list_res = client.get("/api/projects?status=ACTIVE")
    assert list_res.status_code == 200
    assert any(p["id"] == proj_id for p in list_res.json())

    # Delete
    del_res = client.delete(f"/api/projects/{proj_id}")
    assert del_res.status_code == 204
