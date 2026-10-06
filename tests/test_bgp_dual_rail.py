import base64
import json
import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from x402 import x402ResourceServer
from x402.extensions.bazaar import bazaar_resource_server_extension
from x402.extensions.payment_identifier import payment_identifier_resource_server_extension
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.mechanisms.evm.exact import ExactEvmServerScheme
from x402.mechanisms.svm.constants import SOLANA_MAINNET_CAIP2, USDC_MAINNET_ADDRESS
from x402.schemas import SupportedResponse
from app.solana_payments import configure_bgp_solana
from test_bgp_payment_offline import FakeFacilitator, NETWORK, PATH, PAY_TO, get_bgp_route
from test_bgp_route_offline import load_offline_app

RECIPIENT = "2rcgAvgbmVQh279F6EVPeH3gaHNqAq1uU611Wqcxwnq1"
FEE_PAYER = "11111111111111111111111111111111"

class DualFacilitator(FakeFacilitator):
    def get_supported(self):
        return SupportedResponse.model_validate({
            "kinds": [
                {"x402Version": 2, "scheme": "exact", "network": NETWORK},
                {"x402Version": 2, "scheme": "exact", "network": SOLANA_MAINNET_CAIP2,
                 "extra": {"feePayer": FEE_PAYER}},
            ],
            "extensions": ["bazaar", "payment-identifier"],
            "signers": {},
        })

class DualRailTests(unittest.TestCase):
    def test_two_payment_options(self):
        with patch("socket.socket.connect", side_effect=AssertionError("Network forbidden")), patch.dict(
            os.environ, {"VENNATTA_SOLANA_ENABLED": "true",
                         "VENNATTA_SOLANA_PAY_TO": RECIPIENT}, clear=True
        ):
            app, tree = load_offline_app()
            route = get_bgp_route(tree)
            facilitator = DualFacilitator()
            server = x402ResourceServer(facilitator)
            server.register(NETWORK, ExactEvmServerScheme())
            server.register_extension(payment_identifier_resource_server_extension)
            server.register_extension(bazaar_resource_server_extension)
            configure_bgp_solana(server, route)
            server.initialize()
            handler = app.routes[-1].endpoint
            with patch.dict(handler.__globals__, {
                "build_bgp_brief": lambda **kw: self.fail("Unpaid fulfillment")
            }):
                app.add_middleware(PaymentMiddlewareASGI,
                    routes={f"POST {PATH}": route}, server=server)
                with TestClient(app) as client:
                    response = client.post(PATH, json={
                        "previous_text": "AS64500 stable.",
                        "current_text": "AS64500 rerouting.",
                    })
        self.assertEqual(response.status_code, 402)
        header = response.headers.get("payment-required")
        self.assertIsNotNone(header)
        challenge = json.loads(base64.b64decode(header))
        self.assertEqual(challenge["x402Version"], 2)
        self.assertEqual(len(challenge["accepts"]), 2)
        options = {item["network"]: item for item in challenge["accepts"]}
        self.assertEqual(set(options), {NETWORK, SOLANA_MAINNET_CAIP2})
        self.assertEqual(options[NETWORK]["payTo"], PAY_TO)
        solana = options[SOLANA_MAINNET_CAIP2]
        self.assertEqual(solana["payTo"], RECIPIENT)
        self.assertEqual(solana["asset"], USDC_MAINNET_ADDRESS)
        self.assertEqual(solana["extra"]["feePayer"], FEE_PAYER)
        for option in options.values():
            self.assertEqual(option["amount"], "50000")
            self.assertEqual(option["scheme"], "exact")
        self.assertEqual(facilitator.verify_calls, 0)
        self.assertEqual(facilitator.settle_calls, 0)
