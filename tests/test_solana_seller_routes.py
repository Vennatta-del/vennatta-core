import os
import unittest
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

from app.solana_payments import configure_solana_routes
from x402.mechanisms.svm.constants import SOLANA_MAINNET_CAIP2

RECIPIENT = "2rcgAvgbmVQh279F6EVPeH3gaHNqAq1uU611Wqcxwnq1"
ENV = {
    "VENNATTA_SOLANA_ENABLED": "true",
    "VENNATTA_SOLANA_PAY_TO": RECIPIENT,
}


def route():
    return NS(accepts=[NS(network="eip155:8453")])


class SolanaSellerRouteTests(unittest.TestCase):
    def test_three_routes_keep_base_and_individual_prices(self):
        server = Mock()
        routes = [route(), route(), route()]
        prices = ["$0.05", "$0.01", "$0.01"]
        original_base = [item.accepts[0] for item in routes]
        with patch.dict(os.environ, ENV, clear=True):
            self.assertTrue(
                configure_solana_routes(server, list(zip(routes, prices)))
            )
        server.register.assert_called_once()
        for item, base, price in zip(routes, original_base, prices):
            self.assertIs(item.accepts[0], base)
            self.assertEqual(len(item.accepts), 2)
            self.assertEqual(str(item.accepts[1].network), str(SOLANA_MAINNET_CAIP2))
            self.assertEqual(item.accepts[1].pay_to, RECIPIENT)
            self.assertEqual(item.accepts[1].price, price)

    def test_disabled_leaves_routes_unchanged(self):
        server = Mock()
        item = route()
        with patch.dict(os.environ, {
            "VENNATTA_SOLANA_ENABLED": "false",
        }, clear=True):
            self.assertFalse(configure_solana_routes(server, [(item, "$0.01")]))
        server.register.assert_not_called()
        self.assertEqual(len(item.accepts), 1)

    def test_duplicate_route_rejected_before_mutation(self):
        server = Mock()
        item = route()
        with patch.dict(os.environ, ENV, clear=True):
            with self.assertRaises(RuntimeError):
                configure_solana_routes(
                    server, [(item, "$0.01"), (item, "$0.01")]
                )
        server.register.assert_not_called()
        self.assertEqual(len(item.accepts), 1)

    def test_existing_solana_option_rejected_before_mutation(self):
        server = Mock()
        item = route()
        item.accepts.append(NS(network=SOLANA_MAINNET_CAIP2))
        with patch.dict(os.environ, ENV, clear=True):
            with self.assertRaises(RuntimeError):
                configure_solana_routes(server, [(item, "$0.01")])
        server.register.assert_not_called()
        self.assertEqual(len(item.accepts), 2)
