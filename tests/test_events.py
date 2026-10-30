def test_event_creation_and_listing(client):
    evt_payload = {
        "event_type": "system.warning",
        "source": "host_monitor",
        "related_agent_id": "techy",
        "payload": {"disk_usage_percent": 88, "mount": "/var"},
    }
    create_res = client.post("/api/events", json=evt_payload)
    assert create_res.status_code == 201
    evt_data = create_res.json()
    evt_id = evt_data["id"]
    assert evt_data["event_type"] == "system.warning"

    # Query by event_type
    list_res = client.get("/api/events?event_type=system.warning")
    assert list_res.status_code == 200
    assert any(e["id"] == evt_id for e in list_res.json())

    # Get single event
    get_res = client.get(f"/api/events/{evt_id}")
    assert get_res.status_code == 200
    assert get_res.json()["source"] == "host_monitor"


def test_event_stream_endpoint(client):
    """Verify that /api/events/stream returns text/event-stream content type and initial ping."""
    res = client.get("/api/events/stream?once=true")
    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]
    assert ": connected" in res.text



