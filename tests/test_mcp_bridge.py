import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from app.mcp_bridge import ApiKeyGate, MAX_BODY, gateway_read, get_bridge_status


class GateTests(unittest.IsolatedAsyncioTestCase):
    async def invoke(self, headers, body=b"{}"):
        calls = []
        output = []

        async def inner(scope, receive, send):
            calls.append(await receive())

        receive = AsyncMock(return_value={"type": "http.request", "body": body, "more_body": False})
        send = AsyncMock(side_effect=output.append)
        await ApiKeyGate(inner, "a" * 32)({"type": "http", "headers": headers}, receive, send)
        return calls, output

    async def test_missing_key(self):
        calls, output = await self.invoke([])
        self.assertFalse(calls)
        self.assertEqual(output[0]["status"], 401)

    async def test_wrong_key(self):
        calls, output = await self.invoke([(b"x-api-key", b"b" * 32)])
        self.assertFalse(calls)
        self.assertEqual(output[0]["status"], 401)

    async def test_bearer_and_api_key(self):
        for headers in ([(b"authorization", b"Bearer " + b"a" * 32)],
                        [(b"x-api-key", b"a" * 32)]):
            calls, output = await self.invoke(headers)
            self.assertEqual(calls[0]["body"], b"{}")
            self.assertFalse(output)

    async def test_duplicate_credentials(self):
        calls, output = await self.invoke([(b"x-api-key", b"a" * 32)] * 2)
        self.assertFalse(calls)
        self.assertEqual(output[0]["status"], 401)

    async def test_oversized_body(self):
        calls, output = await self.invoke([(b"x-api-key", b"a" * 32)], b"x" * (MAX_BODY + 1))
        self.assertFalse(calls)
        self.assertEqual(output[0]["status"], 413)

    def test_missing_configuration_fails_closed(self):
        with self.assertRaises(RuntimeError):
            ApiKeyGate(None, "")

    def test_no_execution_authority(self):
        state = get_bridge_status()
        self.assertFalse(state["can_sign"])
        self.assertFalse(state["can_trade"])
        self.assertIn("vault", state["not_connected"])

    async def test_gateway_failure_is_explicit(self):
        import httpx
        with patch("app.mcp_bridge.httpx.AsyncClient", side_effect=httpx.ConnectError("offline")):
            result = await gateway_read("/health")
        self.assertEqual(result["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
