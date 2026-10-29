def test_message_creation_and_retrieval(client):
    msg_payload = {
        "sender_id": "archy",
        "receiver_id": "elder",
        "content": "Elder, could you review the proposed architecture for the telemetry scanner?",
        "message_type": "ADVICE",
        "status": "SENT",
        "metadata_json": {"priority": "normal"},
    }
    create_res = client.post("/api/messages", json=msg_payload)
    assert create_res.status_code == 201
    msg_data = create_res.json()
    msg_id = msg_data["id"]
    assert msg_data["sender_id"] == "archy"
    assert msg_data["receiver_id"] == "elder"
    assert msg_data["message_type"] == "ADVICE"

    # Get by ID
    get_res = client.get(f"/api/messages/{msg_id}")
    assert get_res.status_code == 200
    assert get_res.json()["content"] == msg_payload["content"]

    # Filter messages
    list_res = client.get("/api/messages?receiver_id=elder")
    assert list_res.status_code == 200
    assert any(m["id"] == msg_id for m in list_res.json())
