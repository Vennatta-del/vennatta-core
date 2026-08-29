from fastapi.testclient import TestClient

from app.main import app


def test_health_reports_candidate_mode():
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "candidate"
    assert data["real_settlement"] is False
    assert data["network"] == "eip155:8453"


def test_canary_returns_generic_response_and_records_event():
    response = TestClient(app).get("/__canary__/status")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_paid_route_requires_payment_protocol():
    response = TestClient(app).post(
        "/v2/paid-resource",
        json={"input": "test"},
    )

    assert response.status_code == 402
