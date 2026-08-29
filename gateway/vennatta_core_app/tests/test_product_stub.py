from app.product_stub import fulfill_inert_contract


def test_stub_is_candidate_only():
    result = fulfill_inert_contract({"input": "test"})

    assert result["status"] == "candidate-only"
    assert result["product"] == "temporary-inert-resource"
    assert result["fulfillment_enabled"] is False
    assert result["accepted_input_keys"] == ["input"]
