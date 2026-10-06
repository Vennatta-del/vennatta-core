import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, patch
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
import test_bgp_payment_offline as fixture

factory = PaymentMiddlewareASGI.__init__.__globals__["payment_middleware"]
HTTPServer = factory.__globals__["x402HTTPResourceServer"]

class PaymentBoundaryTests(unittest.TestCase):
    setUp = fixture.BgpPaymentOfflineTests.setUp
    request = fixture.BgpPaymentOfflineTests.request
    counted_service = fixture.BgpPaymentOfflineTests.counted_service

    def test_verification_rejection_blocks_handler(self):
        response = NS(is_html=False, body={"error": "rejected"}, status=402, headers={})
        result = NS(type="payment-error", response=response)
        with patch.object(HTTPServer, "process_http_request", new=AsyncMock(return_value=result)), patch.object(HTTPServer, "process_settlement", new=AsyncMock()) as settle:
            reply = self.request()
        self.assertEqual(reply.status_code, 402)
        self.assertEqual(self.fulfillment_calls, 0)
        settle.assert_not_awaited()

    def test_settlement_failure_withholds_brief(self):
        verified = NS(type="payment-verified", payment_payload=None, payment_requirements=None, cancellation_dispatcher=None, before_handler_settlement=None, declared_extensions={})
        failure = NS(success=False, response=NS(is_html=False, body={}, status=402, headers={}))
        with patch.object(HTTPServer, "process_http_request", new=AsyncMock(return_value=verified)), patch.object(HTTPServer, "process_settlement", new=AsyncMock(return_value=failure)) as settle:
            reply = self.request()
        self.assertEqual(self.fulfillment_calls, 1)
        settle.assert_awaited_once()
        self.assertEqual(reply.status_code, 402)
        self.assertEqual(reply.json(), {})
        self.assertNotIn("vennatta.bgp-brief", reply.text)
