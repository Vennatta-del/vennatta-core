import unittest

from jsonschema import Draft202012Validator

from app.bgp_service import bgp_brief_output_schema, build_bgp_brief


class BgpSchemaTests(unittest.TestCase):
    def test_output_schema(self):
        schema = bgp_brief_output_schema()
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)

        for source_url in (None, "https://example.com/routing"):
            with self.subTest(source_url=source_url):
                payload = {
                    "status": "success",
                    "data": build_bgp_brief(
                        previous_text="AS64500 advertises 203.0.113.0/24.",
                        current_text="AS64500 advertises 198.51.100.0/24.",
                        source_url=source_url,
                    ),
                }
                validator.validate(payload)
                payload["data"]["change_detected"] = "yes"
                self.assertFalse(validator.is_valid(payload))
