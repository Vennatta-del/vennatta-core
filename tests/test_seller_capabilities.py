import unittest
from types import SimpleNamespace as NS

from app.seller_capabilities import seller_capabilities

BASE = "eip155:8453"
SOLANA = "solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp"


def route(*networks):
    return NS(accepts=[NS(network=network) for network in networks])


class SellerCapabilitiesTests(unittest.TestCase):
    def test_base_only(self):
        result = seller_capabilities({"POST /brief": route(BASE)})
        self.assertEqual(result["chains"], ["Base"])
        self.assertEqual(
            result["payment_networks_by_route"],
            {"POST /brief": [BASE]},
        )

    def test_dual_rail_is_scoped_to_the_correct_route(self):
        result = seller_capabilities({
            "POST /brief": route(BASE, SOLANA),
            "POST /document": route(BASE),
        })
        self.assertEqual(result["chains"], ["Base", "Solana"])
        self.assertEqual(
            result["payment_networks_by_route"]["POST /brief"],
            sorted([BASE, SOLANA]),
        )
        self.assertEqual(
            result["payment_networks_by_route"]["POST /document"],
            [BASE],
        )

    def test_deduplicates_without_mutating_routes(self):
        routes = {"POST /brief": route(BASE, BASE, SOLANA)}
        result = seller_capabilities(routes)
        self.assertEqual(
            result["payment_networks_by_route"]["POST /brief"],
            sorted([BASE, SOLANA]),
        )
        self.assertEqual(len(routes["POST /brief"].accepts), 3)


if __name__ == "__main__":
    unittest.main()
