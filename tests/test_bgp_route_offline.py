import ast
import json
import logging
from pathlib import Path
import unittest

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from x402.extensions.bazaar import OutputConfig
from x402.http import PaymentOption
from x402.http.types import RouteConfig

from app.bazaar_compat import declare_body_discovery_extension
from app.bgp_service import (
    MAX_TEXT_CHARS,
    bgp_brief_output_schema,
    build_bgp_brief,
)


def load_offline_app():
    tree = ast.parse(Path("app/main.py").read_text(encoding="utf-8"))
    selected = [
        node for node in tree.body
        if (
            isinstance(node, ast.ClassDef)
            and node.name == "BgpBriefRequest"
        ) or (
            isinstance(node, ast.AsyncFunctionDef)
            and node.name == "bgp_brief_endpoint"
        )
    ]
    if len(selected) != 2:
        raise AssertionError("Expected exactly one BGP model and handler")

    app = FastAPI()
    namespace = {
        "__name__": "bgp_offline_test",
        "app": app,
        "BaseModel": BaseModel,
        "ConfigDict": ConfigDict,
        "Field": Field,
        "HttpUrl": HttpUrl,
        "Request": Request,
        "JSONResponse": JSONResponse,
        "MAX_TEXT_CHARS": MAX_TEXT_CHARS,
        "build_bgp_brief": build_bgp_brief,
        "logger": logging.getLogger("bgp_offline_test"),
    }
    module = ast.Module(body=selected, type_ignores=[])
    exec(compile(module, "bgp_offline_test", "exec"), namespace)
    return app, tree


class BgpRouteOfflineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app, cls.tree = load_offline_app()

    def post(self, payload):
        with TestClient(self.app) as client:
            return client.post("/api/v1/briefs/bgp-routing", json=payload)

    def test_valid_request(self):
        response = self.post({
            "previous_text": "AS64500 is stable.",
            "current_text": "AS64500 is rerouting.",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

    def test_whitespace_rejected(self):
        response = self.post({
            "previous_text": " ",
            "current_text": "AS64500",
        })
        self.assertEqual(response.status_code, 422)

    def test_extra_field_rejected(self):
        response = self.post({
            "previous_text": "AS64500",
            "current_text": "AS64501",
            "unexpected": True,
        })
        self.assertEqual(response.status_code, 422)

    def test_oversized_rejected(self):
        response = self.post({
            "previous_text": "x" * (MAX_TEXT_CHARS + 1),
            "current_text": "AS64500",
        })
        self.assertEqual(response.status_code, 422)

    def test_invalid_url_rejected(self):
        response = self.post({
            "previous_text": "AS64500",
            "current_text": "AS64501",
            "source_url": "not-a-url",
        })
        self.assertEqual(response.status_code, 422)

    def test_discovery_contract_constructs(self):
        route_nodes = [
            node for node in self.tree.body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "routes"
        ]
        self.assertEqual(len(route_nodes), 1)
        route_dict = route_nodes[0].value
        self.assertIsInstance(route_dict, ast.Dict)

        expression = None
        for key, value in zip(route_dict.keys, route_dict.values):
            if (
                isinstance(key, ast.Constant)
                and key.value == "POST /api/v1/briefs/bgp-routing"
            ):
                expression = value
                break
        self.assertIsNotNone(expression)

        class OfflineSettings:
            network = "eip155:8453"
            pay_to = "0x0000000000000000000000000000000000000001"

        namespace = {
            "RouteConfig": RouteConfig,
            "PaymentOption": PaymentOption,
            "OutputConfig": OutputConfig,
            "declare_body_discovery_extension": declare_body_discovery_extension,
            "build_bgp_brief": build_bgp_brief,
            "bgp_brief_output_schema": bgp_brief_output_schema,
            "MAX_TEXT_CHARS": MAX_TEXT_CHARS,
            "settings": OfflineSettings(),
        }
        route = eval(
            compile(ast.Expression(body=expression), "bgp_contract", "eval"),
            namespace,
        )
        extensions = route.extensions
        self.assertIsInstance(extensions, dict)
        self.assertIn("bazaar", extensions)
        self.assertIn(
            "vennatta.bgp-brief.v0.1",
            json.dumps(extensions),
        )


if __name__ == "__main__":
    unittest.main()
