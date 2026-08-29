from fastapi.testclient import TestClient

from app.main import app
from x402.http import decode_payment_required_header


def test_payment_required_advertises_required_identifier():
    response = TestClient(app).post(
        "/v2/paid-resource",
        json={"input": "inspection-only"},
    )

    assert response.status_code == 402

    encoded = response.headers["payment-required"]
    payment_required = decode_payment_required_header(encoded)

    assert payment_required.x402_version == 2
    assert payment_required.extensions is not None

    extension = payment_required.extensions["payment-identifier"]
    assert extension["info"]["required"] is True
