"""Bounded routing-notice evidence; no fetching or threat detection."""

from __future__ import annotations

import ipaddress
import re
from typing import Any

from .evidence_service import (
    MAX_EVIDENCE_CHARS,
    MAX_EVIDENCE_ITEMS,
    compare_evidence,
)

MAX_TEXT_CHARS = 50_000
MAX_IDENTIFIERS = 100
MAX_ASN = 4_294_967_295

ASN_PATTERN = re.compile(r"(?<!\w)AS([0-9]{1,10})(?!\w)", re.I)
PREFIX_PATTERN = re.compile(
    r"(?<![\w:.])([0-9A-Fa-f:.]+/[0-9]{1,3})(?![\w/])"
)


def _identifiers(text: str) -> tuple[list[str], list[str]]:
    asns = set()
    prefixes = set()

    for match in ASN_PATTERN.finditer(text):
        number = int(match.group(1))
        if 1 <= number <= MAX_ASN:
            asns.add(f"AS{number}")

    for match in PREFIX_PATTERN.finditer(text):
        try:
            network = ipaddress.ip_network(match.group(1), strict=True)
        except ValueError:
            continue
        prefixes.add(str(network))

    if len(asns) > MAX_IDENTIFIERS or len(prefixes) > MAX_IDENTIFIERS:
        raise ValueError("too many network identifiers")

    return sorted(asns, key=lambda value: int(value[2:])), sorted(prefixes)


def build_bgp_brief(
    *,
    previous_text: str,
    current_text: str,
    source_url: str | None = None,
) -> dict[str, Any]:
    for text in (previous_text, current_text):
        if not isinstance(text, str) or not text.strip():
            raise ValueError("both source versions must contain text")
        if len(text) > MAX_TEXT_CHARS:
            raise ValueError(f"each source version is limited to {MAX_TEXT_CHARS} characters")

    previous_asns, previous_prefixes = _identifiers(previous_text)
    current_asns, current_prefixes = _identifiers(current_text)

    evidence = compare_evidence(
        previous_text=previous_text,
        current_text=current_text,
        source_url=source_url,
        comparison_type="auto",
    )

    if not evidence["change_detected"]:
        classification = "unknown"
    elif previous_prefixes != current_prefixes:
        classification = "prefix_change"
    elif previous_asns != current_asns:
        classification = "asn_change"
    elif previous_asns or current_asns or previous_prefixes or current_prefixes:
        classification = "routing_notice_change"
    else:
        classification = "unknown"

    return {
        "schema_version": "vennatta.bgp-brief.v0.1",
        "source_url": source_url,
        "change_detected": evidence["change_detected"],
        "classification": classification,
        "summary": (
            "Detected a normalized text change in the supplied routing notice versions."
            if evidence["change_detected"]
            else "No normalized text change detected."
        ),
        "network_identifiers": {
            "asns": sorted(
                set(previous_asns + current_asns),
                key=lambda value: int(value[2:]),
            ),
            "prefixes": sorted(set(previous_prefixes + current_prefixes)),
        },
        "evidence": {
            "added": evidence["added_evidence"],
            "removed": evidence["removed_evidence"],
        },
        "provenance": {
            "previous_sha256": evidence["previous_sha256"],
            "current_sha256": evidence["current_sha256"],
        },
        "limitations": [
            "Analysis is limited to the supplied text versions.",
            "The source URL is a client-supplied label; it was not fetched or verified.",
            "Extracted identifiers do not establish a hijack, route leak, or ownership.",
            "Prefix extraction accepts canonical network addresses only.",
            "This endpoint does not provide live monitoring or global routing visibility.",
        ],
        "metadata": evidence["metadata"],
    }

def bgp_brief_output_schema() -> dict[str, Any]:
    def closed_object(properties: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": properties,
            "required": list(properties),
        }

    identifiers = {
        "type": "array",
        "uniqueItems": True,
        "maxItems": MAX_IDENTIFIERS * 2,
        "items": {"type": "string"},
    }
    evidence_items = {
        "type": "array",
        "maxItems": MAX_EVIDENCE_ITEMS,
        "items": {"type": "string", "maxLength": MAX_EVIDENCE_CHARS},
    }
    digest = {"type": "string", "pattern": "^[0-9a-f]{64}$"}

    return closed_object({
        "status": {"type": "string", "enum": ["success"]},
        "data": closed_object({
            "schema_version": {
                "type": "string",
                "enum": ["vennatta.bgp-brief.v0.1"],
            },
            "source_url": {"type": ["string", "null"]},
            "change_detected": {"type": "boolean"},
            "classification": {
                "type": "string",
                "enum": [
                    "unknown",
                    "prefix_change",
                    "asn_change",
                    "routing_notice_change",
                ],
            },
            "summary": {"type": "string"},
            "network_identifiers": closed_object({
                "asns": identifiers,
                "prefixes": identifiers,
            }),
            "evidence": closed_object({
                "added": evidence_items,
                "removed": evidence_items,
            }),
            "provenance": closed_object({
                "previous_sha256": digest,
                "current_sha256": digest,
            }),
            "limitations": {
                "type": "array",
                "items": {"type": "string"},
            },
            "metadata": closed_object({
                "previous_characters": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": MAX_TEXT_CHARS,
                },
                "current_characters": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": MAX_TEXT_CHARS,
                },
                "processing_ms": {"type": "integer", "minimum": 0},
            }),
        }),
    })
