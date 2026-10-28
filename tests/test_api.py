from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_create_list_review_metrics():
    created = client.post("/requests", json={"subject": "Export", "body": "How do I export a report to Excel?"})
    assert created.status_code == 200
    rid = created.json()["id"]
    assert any(x["id"] == rid for x in client.get("/requests?status=pending").json())
    reviewed = client.post(f"/requests/{rid}/review",
                           json={"action": "approve", "reviewer": "Praveen", "seconds_spent": 30})
    assert reviewed.json()["status"] == "approved"
    assert client.post("/baseline", json={"ticket_ref": "T02", "seconds": 240}).status_code == 200
    m = client.get("/metrics").json()
    assert m["reviewed"] >= 1 and m["manual_baseline_seconds"] is not None


def test_errors():
    assert client.get("/requests/99999").status_code == 404
    assert client.post("/requests", json={"subject": "", "body": "x"}).status_code == 422
    rid = client.post("/requests", json={"subject": "Q", "body": "Export to CSV?"}).json()["id"]
    assert client.post(f"/requests/{rid}/review", json={"action": "reject", "reviewer": "P"}).status_code == 400


def test_samples():
    assert len(client.get("/samples").json()) == 52


def test_review_time_and_audit_limit_are_validated():
    rid = client.post("/requests", json={"subject": "Q", "body": "Export to CSV?"}).json()["id"]
    bad = {"action": "approve", "reviewer": "P", "seconds_spent": -5}
    assert client.post(f"/requests/{rid}/review", json=bad).status_code == 422
    assert client.get("/audit?limit=-1").status_code == 422
    assert client.get("/audit?limit=5").status_code == 200
