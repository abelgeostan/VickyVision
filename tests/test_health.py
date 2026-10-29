def test_health_endpoints(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["service"] == "VICKY OS"
    assert "components" in data
    assert "database" in data["components"]

    res_api = client.get("/api/health")
    assert res_api.status_code == 200
    assert res_api.json()["status"] in ("healthy", "degraded", "unhealthy")


def test_root_endpoint(client):
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "OPERATIONAL"
    assert "techy" in data["agents"]
    assert "elder" in data["agents"]
    assert "archy" in data["agents"]
    assert "pa" in data["agents"]
