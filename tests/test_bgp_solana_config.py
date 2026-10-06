import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.solana_payments import configure_bgp_solana

RECIPIENT = "2rcgAvgbmVQh279F6EVPeH3gaHNqAq1uU611Wqcxwnq1"


class SolanaConfigTests(unittest.TestCase):
    def test_disabled_preserves_base(self):
        server = Mock()
        base = object()
        route = SimpleNamespace(accepts=[base])
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(configure_bgp_solana(server, route))
        server.register.assert_not_called()
        self.assertEqual(route.accepts, [base])

    def test_enabled_adds_solana_without_replacing_base(self):
        from x402.mechanisms.svm.constants import SOLANA_MAINNET_CAIP2

        server = Mock()
        base = object()
        route = SimpleNamespace(accepts=[base])
        with patch.dict(os.environ, {
            "VENNATTA_SOLANA_ENABLED": "true",
            "VENNATTA_SOLANA_PAY_TO": RECIPIENT,
        }, clear=True), patch(
            "socket.socket.connect",
            side_effect=AssertionError("Network access forbidden"),
        ):
            self.assertTrue(configure_bgp_solana(server, route))

        self.assertIs(route.accepts[0], base)
        self.assertEqual(len(route.accepts), 2)
        self.assertEqual(route.accepts[1].network, SOLANA_MAINNET_CAIP2)
        self.assertEqual(route.accepts[1].pay_to, RECIPIENT)
        server.register.assert_called_once()

    def test_missing_recipient_fails_closed(self):
        with patch.dict(os.environ, {
            "VENNATTA_SOLANA_ENABLED": "true",
        }, clear=True):
            with self.assertRaises(RuntimeError):
                configure_bgp_solana(Mock(), SimpleNamespace(accepts=[]))

    def test_invalid_recipient_fails_closed(self):
        with patch.dict(os.environ, {
            "VENNATTA_SOLANA_ENABLED": "true",
            "VENNATTA_SOLANA_PAY_TO": "not-a-solana-address",
        }, clear=True):
            with self.assertRaises(RuntimeError):
                configure_bgp_solana(Mock(), SimpleNamespace(accepts=[]))

    def test_invalid_flag_rejected(self):
        with patch.dict(os.environ, {
            "VENNATTA_SOLANA_ENABLED": "maybe",
        }, clear=True):
            with self.assertRaises(RuntimeError):
                configure_bgp_solana(Mock(), SimpleNamespace(accepts=[]))


if __name__ == "__main__":
    unittest.main()
