import os
import tempfile
import asyncio
import json
import base64
import unittest
import traceback
from unittest.mock import patch

os.environ["TESTING_MODE"] = "1"

from gateway import x402_gateway_prod

class MockSettlementEvidence:
    def __init__(self, outcome, block_number=123456):
        self.outcome = outcome
        self.block_number = block_number

class TestCanaryASGI(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        x402_gateway_prod.DB_PATH = self.db_path
        x402_gateway_prod.init_db()

    async def asyncTearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    async def _simulate_request(self, method, path, headers=None, body=b""):
        headers_list = []
        if headers:
            for k, v in headers.items():
                headers_list.append((k.lower().encode("latin-1"), v.encode("latin-1")))
        
        scope = {
            "type": "http",
            "method": method,
            "path": path,
            "headers": headers_list,
            "query_string": b""
        }

        response_status = None
        response_headers = {}
        response_body = bytearray()

        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message):
            nonlocal response_status, response_headers
            if message["type"] == "http.response.start":
                response_status = message["status"]
                for k, v in message["headers"]:
                    response_headers[k.decode("latin-1").lower()] = v.decode("latin-1")
            elif message["type"] == "http.response.body":
                response_body.extend(message.get("body", b""))

        try:
            await x402_gateway_prod.app(scope, receive, send)
        except Exception as e:
            print(f"\n--- ASGI Exception Caught ---")
            traceback.print_exc()
            raise
        return response_status, response_headers, bytes(response_body)

    async def test_1_health_and_manifest(self):
        status, headers, body = await self._simulate_request("GET", "/agent-manifest.json")
        self.assertEqual(status, 200)
        manifest = json.loads(body.decode())
        self.assertEqual(manifest["name"], "vennatta-document-extraction")

    async def test_2_unpaid_public_route_returns_402(self):
        status, headers, body = await self._simulate_request("POST", "/api/v1/extract-document", body=json.dumps({"content": "test"}).encode())
        self.assertEqual(status, 402)
        self.assertIn("payment-required", headers)
        
        challenge = json.loads(base64.b64decode(headers["payment-required"]).decode())
        accepts = challenge["accepts"][0]
        self.assertEqual(accepts["network"], "eip155:8453")
        self.assertEqual(accepts["amount"], "10000")
        self.assertEqual(accepts["payTo"], x402_gateway_prod.RECEIVER_WALLET)

    @patch("gateway.gateway_settlement.SettlementVerifier.verify_settlement")
    async def test_3_malformed_json_and_edge_cases(self, mock_verify):
        mock_verify.return_value = MockSettlementEvidence("SETTLEMENT_CONFIRMED")
        dummy_sig = base64.b64encode(json.dumps({
            "nonce": "123", "amount": "10000", "asset": x402_gateway_prod.USDC_BASE_CONTRACT,
            "network": "eip155:8453", "payTo": x402_gateway_prod.RECEIVER_WALLET,
            "resource": "https://agentcitadel.dev/api/v1/extract-document", "payer": "0xBuyer", "txHash": "0xabc"
        }).encode()).decode()

        status, _, body = await self._simulate_request("POST", "/api/v1/extract-document", headers={"PAYMENT-SIGNATURE": dummy_sig}, body=b"{invalid_json")
        self.assertEqual(status, 200)

    @patch("gateway.gateway_settlement.SettlementVerifier.verify_settlement")
    async def test_4_valid_confirmed_settlement_flow(self, mock_verify):
        mock_verify.return_value = MockSettlementEvidence("SETTLEMENT_CONFIRMED")

        payment_sig = base64.b64encode(json.dumps({
            "nonce": "nonce_valid_1", "amount": "10000", "asset": x402_gateway_prod.USDC_BASE_CONTRACT,
            "network": "eip155:8453", "payTo": x402_gateway_prod.RECEIVER_WALLET,
            "resource": "https://agentcitadel.dev/api/v1/extract-document", "payer": "0xBuyer", "txHash": "0x1234567890abcdef"
        }).encode()).decode()

        status, headers, body = await self._simulate_request(
            "POST", "/api/v1/extract-document",
            headers={"PAYMENT-SIGNATURE": payment_sig},
            body=json.dumps({"content": "extractable document text"}).encode()
        )

        self.assertEqual(status, 200)
        self.assertIn("payment-response", headers)
        result = json.loads(body.decode())
        self.assertEqual(result["status"], "success")

    @patch("gateway.gateway_settlement.SettlementVerifier.verify_settlement")
    async def test_5_rpc_disagreement_fails_closed(self, mock_verify):
        mock_verify.return_value = MockSettlementEvidence("SETTLEMENT_UNKNOWN")

        payment_sig = base64.b64encode(json.dumps({
            "nonce": "nonce_unknown_1", "amount": "10000", "asset": x402_gateway_prod.USDC_BASE_CONTRACT,
            "network": "eip155:8453", "payTo": x402_gateway_prod.RECEIVER_WALLET,
            "resource": "https://agentcitadel.dev/api/v1/extract-document", "payer": "0xBuyer", "txHash": "0xbadhash"
        }).encode()).decode()

        status, _, body = await self._simulate_request(
            "POST", "/api/v1/extract-document",
            headers={"PAYMENT-SIGNATURE": payment_sig},
            body=json.dumps({"content": "text"}).encode()
        )

        self.assertEqual(status, 402)
        err_res = json.loads(body.decode())
        self.assertIn("SETTLEMENT_SETTLEMENT_UNKNOWN", err_res["error"]["code"])

    @patch("gateway.gateway_settlement.SettlementVerifier.verify_settlement")
    async def test_6_idempotent_retry_and_payload_mismatch(self, mock_verify):
        mock_verify.return_value = MockSettlementEvidence("SETTLEMENT_CONFIRMED")

        payment_sig = base64.b64encode(json.dumps({
            "nonce": "nonce_idempotent", "amount": "10000", "asset": x402_gateway_prod.USDC_BASE_CONTRACT,
            "network": "eip155:8453", "payTo": x402_gateway_prod.RECEIVER_WALLET,
            "resource": "https://agentcitadel.dev/api/v1/extract-document", "payer": "0xBuyer", "txHash": "0xreplayedhash"
        }).encode()).decode()

        payload_1 = json.dumps({"content": "original content"}).encode()
        payload_2 = json.dumps({"content": "modified content"}).encode()

        status1, headers1, _ = await self._simulate_request(
            "POST", "/api/v1/extract-document", headers={"PAYMENT-SIGNATURE": payment_sig}, body=payload_1
        )
        self.assertEqual(status1, 200)

        status2, headers2, _ = await self._simulate_request(
            "POST", "/api/v1/extract-document", headers={"PAYMENT-SIGNATURE": payment_sig}, body=payload_1
        )
        self.assertEqual(status2, 200)
        self.assertIn("payment-response", headers2)

        status3, _, body3 = await self._simulate_request(
            "POST", "/api/v1/extract-document", headers={"PAYMENT-SIGNATURE": payment_sig}, body=payload_2
        )
        self.assertEqual(status3, 400)
        self.assertIn("RESOURCE_PAYLOAD_MISMATCH", body3.decode())

if __name__ == "__main__":
    unittest.main()
