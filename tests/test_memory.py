def test_memory_creation_and_search(client):
    # 1. Private memory for Techy
    mem_techy = {
        "agent_id": "techy",
        "type": "SHORT_TERM",
        "content": "Port 8000 is occupied by Portainer on the server.",
        "importance": 8,
        "metadata_json": {"host": "vicky"},
    }
    t_res = client.post("/api/memory", json=mem_techy)
    assert t_res.status_code == 201
    t_id = t_res.json()["id"]

    # 2. Shared organizational memory
    mem_shared = {
        "agent_id": None,
        "type": "SHARED",
        "content": "Server architecture: Ubuntu 24.04 with Docker host network at 192.168.1.123",
        "importance": 10,
        "metadata_json": {"org": "vicky_os"},
    }
    s_res = client.post("/api/memory", json=mem_shared)
    assert s_res.status_code == 201
    s_id = s_res.json()["id"]

    # 3. Query memory for Techy with shared included
    list_res = client.get("/api/memory?agent_id=techy&include_shared=true")
    assert list_res.status_code == 200
    ids = [m["id"] for m in list_res.json()]
    assert t_id in ids
    assert s_id in ids

    # 4. Search query
    search_res = client.get("/api/memory?query=Portainer")
    assert search_res.status_code == 200
    assert any(m["id"] == t_id for m in search_res.json())
