import hashlib
import json

import pytest

from app.extraction_service import extract_product
from app.review_gate import ReviewGateError, review_product_result


def make_product():
    return extract_product(
        document="title: Report A",
        fields=["title"],
        env={},
    )


def test_valid_product_result_is_approved():
    product = make_product()

    reviewed = review_product_result(
        product=product,
        document="title: Report A",
        requested_fields=["title"],
    )

    assert reviewed["reviewed"] is True
    assert reviewed["review_status"] == "approved"


def test_tampered_hash_is_rejected():
    product = make_product()
    product["result_sha256"] = "0" * 64

    with pytest.raises(ReviewGateError, match="hash mismatch"):
        review_product_result(
            product=product,
            document="title: Report A",
            requested_fields=["title"],
        )


def test_fabricated_field_is_rejected():
    product = make_product()
    product["result"]["fields"]["author"] = "Invented"

    with pytest.raises(ReviewGateError, match="unrequested field"):
        review_product_result(
            product=product,
            document="title: Report A",
            requested_fields=["title"],
        )


def test_missing_source_span_is_rejected():
    product = make_product()
    product["result"]["source_spans"] = []

    canonical = json.dumps(
        product["result"],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    product["result_sha256"] = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()

    with pytest.raises(ReviewGateError, match="exactly one source span"):
        review_product_result(
            product=product,
            document="title: Report A",
            requested_fields=["title"],
        )


def test_document_change_is_rejected():
    product = make_product()

    with pytest.raises(ReviewGateError, match="source span"):
        review_product_result(
            product=product,
            document="title: Changed",
            requested_fields=["title"],
        )
