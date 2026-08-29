import pytest

from app.extraction_service import extract_product
from app.facilitator_adapter import FacilitatorAdapter
from app.facilitator_http import FacilitatorHttpClient
from app.idempotency_store import IdempotencyStore
from app.review_gate import review_product_result
from app.settlement_gate import SettlementAdapter, fulfill_after_settlement
from app.x402_config import get_network, get_scheme


class MockPolygonFacilitator:
    def __init__(self) -> None:
        self.calls = []

    def request(self, **kwargs):
        self.calls.append(kwargs)

        path = kwargs["url"].split("/")[-1]

        if path == "verify":
            return {
                "isValid": True,
                "network": "polygon-amoy",
                "scheme": "exact",
                "paymentId": "polygon-payment-1",
            }
        if path == "settle":
            return {
                "success": True,
                "transaction": "polygon-tx-1",
            }

        raise RuntimeError(f"unexpected path: {path}")


@pytest.fixture
def polygon_sandbox_stack(tmp_path):
    transport = MockPolygonFacilitator()

    http_client = FacilitatorHttpClient(
        request=transport.request,
        base_url="https://sandbox-polygon.facilitator.example",
        expected_network="polygon-amoy",
        expected_scheme="exact",
        live_enabled=True,
    )

    adapter = FacilitatorAdapter(http_client=http_client)

    idempotency = IdempotencyStore(tmp_path / "idempotency-polygon.sqlite3")

    settlement = SettlementAdapter(
        verify=adapter.verify,
        settle=adapter.settle,
        dry_run=False,
        idempotency_store=idempotency,
    )

    return {
        "transport": transport,
        "settlement": settlement,
        "idempotency": idempotency,
    }


def test_full_polygon_sandbox_flow(polygon_sandbox_stack):
    document = "title: Polygon Report"
    fields = ["title"]

    product = extract_product(
        document=document,
        fields=fields,
        env={},
    )

    reviewed = review_product_result(
        product=product,
        document=document,
        requested_fields=fields,
    )

    receipt = polygon_sandbox_stack["settlement"].execute(
        reviewed_product=reviewed,
        request_id="polygon-req-1",
        payment={"payload": "polygon-test"},
    )

    assert receipt.status == "settled"
    assert receipt.settlement_id == "polygon-tx-1"
    assert receipt.dry_run is False

    calls = polygon_sandbox_stack["transport"].calls
    assert len(calls) == 2
    assert calls[0]["url"].endswith("/v2/x402/verify")
    assert calls[1]["url"].endswith("/v2/x402/settle")

    output = fulfill_after_settlement(
        receipt=receipt,
        fulfill=lambda: "polygon-fulfilled",
    )

    assert output == "polygon-fulfilled"


def test_polygon_network_config_is_valid():
    net = get_network("polygon-amoy")
    scheme = get_scheme("exact")

    assert net.name == "Polygon Amoy"
    assert net.is_testnet is True
    assert scheme.id == "exact"
