import ast
import base64
import copy
import json
import os
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from x402 import x402ResourceServer
from x402.extensions.bazaar import bazaar_resource_server_extension
from x402.extensions.payment_identifier import payment_identifier_resource_server_extension
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.mechanisms.evm.exact import ExactEvmServerScheme
from x402.mechanisms.svm.constants import SOLANA_MAINNET_CAIP2, USDC_MAINNET_ADDRESS

import test_bgp_payment_offline as fixture
from test_bgp_dual_rail import DualFacilitator, RECIPIENT, FEE_PAYER
from app.document_service import extract_document
from app.evidence_service import compare_evidence
from app.solana_payments import configure_solana_routes


SPECS = {
    "POST /api/v1/briefs/bgp-routing": ("$0.05", "50000"),
    "POST /api/v1/evidence/compare": ("$0.01", "10000"),
    "POST /api/v1/extract-document": ("$0.01", "10000"),
}


def route_nodes():
    tree = ast.parse(Path("app/main.py").read_text())
    declaration = next(
        node for node in tree.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "routes"
    )
    return {
        key.value: value
        for key, value in zip(declaration.value.keys, declaration.value.values)
        if isinstance(key, ast.Constant)
    }


def keyword(call, name):
    return next(item.value for item in call.keywords if item.arg == name)


def load_routes():
    namespace = dict(vars(fixture))
    namespace["settings"] = NS(
        network=fixture.NETWORK,
        pay_to=fixture.PAY_TO,
    )
    return {
        name: eval(
            compile(ast.Expression(body=node), "seller-route", "eval"),
            namespace,
        )
        for name, node in route_nodes().items()
        if name in SPECS
    }


def stable(value):
    result = copy.deepcopy(value)
    result["data"]["metadata"].pop("processing_ms", None)
    return result


class SellerQuoteDiscoveryTests(unittest.TestCase):
    def test_all_three_services_quote_both_rails_without_fulfillment(self):
        with patch(
            "socket.socket.connect",
            side_effect=AssertionError("Outbound network forbidden"),
        ), patch.dict(os.environ, {
            "VENNATTA_SOLANA_ENABLED": "true",
            "VENNATTA_SOLANA_PAY_TO": RECIPIENT,
        }, clear=True):
            routes = load_routes()
            facilitator = DualFacilitator()
            server = x402ResourceServer(facilitator)
            server.register(fixture.NETWORK, ExactEvmServerScheme())
            server.register_extension(bazaar_resource_server_extension)
            server.register_extension(payment_identifier_resource_server_extension)
            configure_solana_routes(server, [
                (routes[name], price)
                for name, (price, _) in SPECS.items()
            ])
            server.initialize()

            app = FastAPI()

            async def forbidden_handler():
                raise AssertionError("Unpaid request reached fulfillment")

            for name in routes:
                app.add_api_route(
                    name.split(" ", 1)[1],
                    forbidden_handler,
                    methods=["POST"],
                )
            app.add_middleware(
                PaymentMiddlewareASGI, routes=routes, server=server
            )

            with TestClient(app) as client:
                for name, (_, amount) in SPECS.items():
                    with self.subTest(route=name):
                        response = client.post(
                            name.split(" ", 1)[1], json={}
                        )
                        self.assertEqual(response.status_code, 402)
                        offer = json.loads(base64.b64decode(
                            response.headers["payment-required"]
                        ))
                        self.assertEqual(offer["x402Version"], 2)
                        self.assertEqual(len(offer["accepts"]), 2)
                        options = {
                            item["network"]: item
                            for item in offer["accepts"]
                        }
                        self.assertEqual(
                            set(options),
                            {fixture.NETWORK, str(SOLANA_MAINNET_CAIP2)},
                        )
                        self.assertEqual(
                            options[fixture.NETWORK]["payTo"], fixture.PAY_TO
                        )
                        solana = options[str(SOLANA_MAINNET_CAIP2)]
                        self.assertEqual(solana["payTo"], RECIPIENT)
                        self.assertEqual(solana["asset"], USDC_MAINNET_ADDRESS)
                        self.assertEqual(solana["extra"]["feePayer"], FEE_PAYER)
                        for item in options.values():
                            self.assertEqual(item["amount"], amount)
                            self.assertEqual(item["scheme"], "exact")
                        self.assertIn("bazaar", offer["extensions"])

            self.assertEqual(facilitator.verify_calls, 0)
            self.assertEqual(facilitator.settle_calls, 0)

    def test_examples_match_current_service_functions(self):
        for name, node in route_nodes().items():
            if name not in SPECS:
                continue
            with self.subTest(route=name):
                declaration = keyword(node, "extensions")
                inputs = ast.literal_eval(keyword(declaration, "input"))
                example = keyword(keyword(declaration, "output"), "example")

                if name.endswith("/bgp-routing"):
                    actual = fixture.build_bgp_brief(**inputs)
                    namespace = {"build_bgp_brief": fixture.build_bgp_brief}
                    advertised = eval(
                        compile(ast.Expression(body=example), "example", "eval"),
                        namespace,
                    )
                elif name.endswith("/evidence/compare"):
                    actual = compare_evidence(**inputs)
                    advertised = ast.literal_eval(example)
                else:
                    actual = extract_document(
                        text=inputs["document_text"],
                        source_url=None,
                        extraction_mode=inputs["extraction_mode"],
                    )
                    actual["metadata"]["content_type"] = None
                    advertised = ast.literal_eval(example)

                self.assertEqual(
                    stable(advertised),
                    stable({"status": "success", "data": actual}),
                )
