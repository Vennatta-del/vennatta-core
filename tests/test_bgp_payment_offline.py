import ast
import base64
import json
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from x402 import x402ResourceServer
from x402.extensions.bazaar import (
    OutputConfig,
    bazaar_resource_server_extension,
)
from x402.extensions.payment_identifier import (
    payment_identifier_resource_server_extension,
)
from x402.http import PaymentOption
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.http.types import RouteConfig
from x402.mechanisms.evm.exact import ExactEvmServerScheme
from x402.schemas import SupportedResponse

from app.bazaar_compat import declare_body_discovery_extension
from app.bgp_service import (
    MAX_TEXT_CHARS,
    bgp_brief_output_schema,
    build_bgp_brief,
)
from test_bgp_route_offline import load_offline_app


NETWORK = "eip155:8453"
PAY_TO = "0x0000000000000000000000000000000000000001"
PATH = "/api/v1/briefs/bgp-routing"


class FakeFacilitator:
    def __init__(self):
        self.verify_calls = 0
        self.settle_calls = 0

    def get_supported(self):
        return SupportedResponse.model_validate({
            "kinds": [{
                "x402Version": 2,
                "scheme": "exact",
                "network": NETWORK,
            }],
            "extensions": ["bazaar", "payment-identifier"],
            "signers": {},
        })

    async def verify(self, payload, requirements):
        self.verify_calls += 1
        raise AssertionError("No valid payment should reach verification")

    async def settle(self, payload, requirements):
        self.settle_calls += 1
        raise AssertionError("No payment should reach settlement")


def get_bgp_route(tree):
    class Settings:
        network = NETWORK
        pay_to = PAY_TO

    namespace = {
        "RouteConfig": RouteConfig,
        "PaymentOption": PaymentOption,
        "OutputConfig": OutputConfig,
        "declare_body_discovery_extension": declare_body_discovery_extension,
        "build_bgp_brief": build_bgp_brief,
        "bgp_brief_output_schema": bgp_brief_output_schema,
        "MAX_TEXT_CHARS": MAX_TEXT_CHARS,
        "settings": Settings(),
    }

    for node in tree.body:
        if not (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "routes"
        ):
            continue
        for key, value in zip(node.value.keys, node.value.values):
            if isinstance(key, ast.Constant) and key.value == f"POST {PATH}":
                return eval(
                    compile(ast.Expression(body=value), "bgp_route", "eval"),
                    namespace,
                )
    raise AssertionError("BGP payment route not found")


class BgpPaymentOfflineTests(unittest.TestCase):
    def setUp(self):
        self.network_block = patch(
            "socket.socket.connect",
            side_effect=AssertionError("Outbound network access forbidden"),
        )
        self.network_block.start()
        self.addCleanup(self.network_block.stop)

        app, tree = load_offline_app()
        self.handler = app.routes[-1].endpoint
        self.fulfillment_calls = 0

        async def counted_handler(*args, **kwargs):
            self.fulfillment_calls += 1
            return await self.handler(*args, **kwargs)

        # Count fulfillment at the service boundary without changing routing.
        self.service_patch = patch.dict(
            self.handler.__globals__,
            {"build_bgp_brief": self.counted_service},
        )
        self.service_patch.start()
        self.addCleanup(self.service_patch.stop)

        self.facilitator = FakeFacilitator()
        server = x402ResourceServer(self.facilitator)
        server.register(NETWORK, ExactEvmServerScheme())
        server.register_extension(payment_identifier_resource_server_extension)
        server.register_extension(bazaar_resource_server_extension)
        server.initialize()

        app.add_middleware(
            PaymentMiddlewareASGI,
            routes={f"POST {PATH}": get_bgp_route(tree)},
            server=server,
        )
        self.app = app

    def counted_service(self, **kwargs):
        self.fulfillment_calls += 1
        return build_bgp_brief(**kwargs)

    def request(self, headers=None):
        with TestClient(self.app) as client:
            return client.post(
                PATH,
                headers=headers or {},
                json={
                    "previous_text": "AS64500 is stable.",
                    "current_text": "AS64500 is rerouting.",
                },
            )

    def assert_not_fulfilled(self):
        self.assertEqual(self.fulfillment_calls, 0)
        self.assertEqual(self.facilitator.verify_calls, 0)
        self.assertEqual(self.facilitator.settle_calls, 0)

    def test_unpaid_returns_402_and_correct_quote(self):
        response = self.request()
        self.assertEqual(response.status_code, 402)
        encoded = response.headers.get("payment-required")
        self.assertIsNotNone(encoded)
        required = json.loads(base64.b64decode(encoded))
        self.assertEqual(required["x402Version"], 2)
        self.assertEqual(len(required["accepts"]), 1)
        accepted = required["accepts"][0]
        self.assertEqual(accepted["scheme"], "exact")
        self.assertEqual(accepted["network"], NETWORK)
        self.assertEqual(accepted["payTo"], PAY_TO)
        self.assertEqual(accepted["amount"], "50000")
        self.assertEqual(
            accepted["asset"].lower(),
            "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
        )
        self.assert_not_fulfilled()

    def test_malformed_payment_does_not_fulfill(self):
        response = self.request({"PAYMENT-SIGNATURE": "not-valid-base64!"})
        self.assertIn(response.status_code, (400, 402))
        self.assert_not_fulfilled()


if __name__ == "__main__":
    unittest.main()
