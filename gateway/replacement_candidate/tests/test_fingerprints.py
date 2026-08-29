from app.fingerprints import request_fingerprint


def test_fingerprint_is_stable():
    kwargs = dict(
        method="post",
        route="/v2/paid-resource",
        body={"b": 2, "a": 1},
        network="eip155:8453",
        asset="placeholder",
        amount="$0.001",
        pay_to="0x0000000000000000000000000000000000000001",
        payment_id="pid-1234567890",
    )
    assert request_fingerprint(**kwargs) == request_fingerprint(**kwargs)


def test_body_order_does_not_change_fingerprint():
    base = dict(
        method="POST",
        route="/v2/paid-resource",
        network="eip155:8453",
        asset="placeholder",
        amount="$0.001",
        pay_to="0x0000000000000000000000000000000000000001",
        payment_id="pid-1234567890",
    )
    first = request_fingerprint(body={"a": 1, "b": 2}, **base)
    second = request_fingerprint(body={"b": 2, "a": 1}, **base)
    assert first == second
