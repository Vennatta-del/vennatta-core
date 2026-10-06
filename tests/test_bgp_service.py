import unittest

from app.bgp_service import build_bgp_brief


class BgpBriefTests(unittest.TestCase):
    def brief(self, previous, current):
        return build_bgp_brief(previous_text=previous, current_text=current)

    def test_unchanged_normalized_text(self):
        result = self.brief("AS64500 is stable.", "  AS64500   is stable. ")
        self.assertFalse(result["change_detected"])
        self.assertEqual(
            result["provenance"]["previous_sha256"],
            result["provenance"]["current_sha256"],
        )

    def test_prefix_change(self):
        result = self.brief(
            "AS64500 advertises 203.0.113.0/24.",
            "AS64500 advertises 198.51.100.0/24.",
        )
        self.assertEqual(result["classification"], "prefix_change")
        self.assertTrue(result["evidence"]["added"])
        self.assertTrue(result["evidence"]["removed"])

    def test_asn_change(self):
        result = self.brief("AS64500 is upstream.", "AS64501 is upstream.")
        self.assertEqual(result["classification"], "asn_change")

    def test_ipv6_and_invalid_identifiers(self):
        text = (
            "as64500 2001:db8::/32 "
            "999.0.0.0/24 203.0.113.1/24 AS4294967296 AS0"
        )
        result = self.brief(text, text)
        self.assertEqual(result["network_identifiers"]["asns"], ["AS64500"])
        self.assertEqual(result["network_identifiers"]["prefixes"], ["2001:db8::/32"])

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            self.brief(" ", "AS64500")

    def test_size_limit(self):
        with self.assertRaises(ValueError):
            self.brief("x" * 50_001, "AS64500")

    def test_unknown_text(self):
        result = self.brief("Notice pending.", "Notice updated.")
        self.assertEqual(result["classification"], "unknown")

    def test_bounds_and_provenance(self):
        result = self.brief("AS64500 is stable.", "AS64500 is rerouting.")
        self.assertEqual(result["schema_version"], "vennatta.bgp-brief.v0.1")
        self.assertEqual(len(result["provenance"]["current_sha256"]), 64)
        self.assertLessEqual(len(result["evidence"]["added"]), 20)
        self.assertTrue(all(len(item) <= 500 for item in result["evidence"]["added"]))
        self.assertTrue(result["limitations"])


if __name__ == "__main__":
    unittest.main()
