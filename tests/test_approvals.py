def test_approval_workflow(client):
    req_payload = {
        "requesting_agent_id": "techy",
        "action": "reboot_host_server",
        "reason": "Apply kernel security patch update",
        "risk_level": "CRITICAL",
    }
    # Create approval request
    req_res = client.post("/api/approvals", json=req_payload)
    assert req_res.status_code == 201
    approval_id = req_res.json()["id"]
    assert req_res.json()["status"] == "PENDING"

    # Make decision (APPROVE)
    decision = {
        "status": "APPROVED",
        "approved_by": "user",
        "rejection_reason": None,
    }
    dec_res = client.post(f"/api/approvals/{approval_id}/decision", json=decision)
    assert dec_res.status_code == 200
    assert dec_res.json()["status"] == "APPROVED"
    assert dec_res.json()["approved_by"] == "user"
    assert dec_res.json()["approved_at"] is not None

    # Verify audit log recorded the approval
    audit_res = client.get(f"/api/audit?action=approval.approved")
    assert audit_res.status_code == 200
    assert len(audit_res.json()) >= 1
