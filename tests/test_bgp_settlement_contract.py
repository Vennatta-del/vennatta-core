import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, Mock

from x402.http.middleware.fastapi import PaymentMiddlewareASGI

factory = PaymentMiddlewareASGI.__init__.__globals__["payment_middleware"]
HTTPServer = factory.__globals__["x402HTTPResourceServer"]

NETWORK = "solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp"
PAYER = "9SsbXyjP5G28LzvmUHJzrU9evE94xXBKyeSVUa4SFSW6"


class SettlementContractTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.requirements = NS(network=NETWORK)
        self.payload = object()
        self.server = Mock(spec=HTTPServer)
        self.server._echo_or_skip_after_handler_settlement.return_value = None
        self.server._apply_settlement_overrides.return_value = self.requirements
        self.server._create_settlement_headers.return_value = {
            "payment-response": "test-header"
        }
        self.server._build_settlement_failure_response_async = AsyncMock(
            return_value=NS(status=402, body={}, headers={})
        )
        self.server._server = NS(settle_payment=AsyncMock())

    async def process(self):
        return await HTTPServer.process_settlement(
            self.server,
            self.payload,
            self.requirements,
            declared_extensions={},
            phase="after-handler",
        )

    async def test_pending_preserves_transaction_and_does_not_retry(self):
        response = NS(
            success=False,
            error_reason="settlement_pending",
            transaction="test-pending-signature",
            network=NETWORK,
            payer=PAYER,
        )
        self.server._server.settle_payment.return_value = response

        result = await self.process()

        self.assertFalse(result.success)
        self.assertEqual(result.error_reason, "settlement_pending")
        self.assertEqual(result.transaction, "test-pending-signature")
        self.assertEqual(result.network, NETWORK)
        self.assertEqual(result.payer, PAYER)
        self.assertIs(result.settle_response, response)
        self.server._server.settle_payment.assert_awaited_once()
        self.server._build_settlement_failure_response_async.assert_awaited_once()

    async def test_timeout_returns_failure_without_automatic_retry(self):
        self.server._server.settle_payment.side_effect = TimeoutError(
            "facilitator response timed out"
        )

        result = await self.process()

        self.assertFalse(result.success)
        self.assertEqual(result.transaction, "")
        self.assertEqual(result.network, NETWORK)
        self.assertIn("timed out", result.error_reason)
        self.server._server.settle_payment.assert_awaited_once()
        self.server._build_settlement_failure_response_async.assert_awaited_once()

    async def test_success_preserves_receipt_metadata(self):
        response = NS(
            success=True,
            transaction="test-success-signature",
            network=NETWORK,
            payer=PAYER,
        )
        self.server._server.settle_payment.return_value = response

        result = await self.process()

        self.assertTrue(result.success)
        self.assertEqual(result.transaction, "test-success-signature")
        self.assertEqual(result.network, NETWORK)
        self.assertEqual(result.payer, PAYER)
        self.server._server.settle_payment.assert_awaited_once()
        self.server._build_settlement_failure_response_async.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
