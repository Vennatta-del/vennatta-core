"""Deterministic, bounded evidence comparison for Vennatta."""

from __future__ import annotations

import difflib
import hashlib
import re
import time
from typing import Any

SCHEMA_VERSION = "vennatta.evidence-event.v0.1"
MAX_EVIDENCE_ITEMS = 20
MAX_EVIDENCE_CHARS = 500

CATEGORY_KEYWORDS = {
    "pricing_change": (
        "price",
        "pricing",
        "plan",
        "plans",
        "monthly",
        "annual",
        "annually",
        "billing",
        "discount",
        "cost",
    ),
    "product_change": (
        "feature",
        "features",
        "product",
        "release",
        "released",
        "launch",
        "launched",
    ),
    "integration_change": (
        "integration",
        "integrations",
        "api",
        "webhook",
        "connector",
        "connectors",
        "plugin",
        "plugins",
    ),
    "security_change": (
        "security",
        "secure",
        "soc 2",
        "soc2",
        "iso 27001",
        "encryption",
        "vulnerability",
        "incident",
        "compliance",
    ),
    "policy_change": (
        "policy",
        "privacy",
        "terms",
        "subprocessor",
        "data processing",
        "acceptable use",
    ),
}


def normalize_text(text: str) -> str:
    """Collapse whitespace so comparisons and hashes are deterministic."""
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        raise ValueError("text contains no comparable content")
    return normalized


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [part.strip() for part in parts if part.strip()]


def _bounded(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for item in items:
        compact = re.sub(r"\s+", " ", item).strip()
        if not compact or compact in seen:
            continue

        seen.add(compact)
        result.append(compact[:MAX_EVIDENCE_CHARS])

        if len(result) >= MAX_EVIDENCE_ITEMS:
            break

    return result


def _evidence_diff(
    previous: str,
    current: str,
) -> tuple[list[str], list[str]]:
    previous_sentences = _sentences(previous)
    current_sentences = _sentences(current)

    matcher = difflib.SequenceMatcher(
        a=previous_sentences,
        b=current_sentences,
        autojunk=False,
    )

    added: list[str] = []
    removed: list[str] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ("replace", "delete"):
            removed.extend(previous_sentences[i1:i2])
        if tag in ("replace", "insert"):
            added.extend(current_sentences[j1:j2])

    return _bounded(added), _bounded(removed)


def _classify_change(
    added: list[str],
    removed: list[str],
    comparison_type: str,
) -> str:
    if comparison_type != "auto":
        return f"{comparison_type}_change"

    evidence = " ".join(added + removed).lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in evidence for keyword in keywords):
            return category

    return "unknown"


def compare_evidence(
    *,
    previous_text: str,
    current_text: str,
    source_url: str | None,
    comparison_type: str = "auto",
) -> dict[str, Any]:
    started = time.perf_counter()
    previous = normalize_text(previous_text)
    current = normalize_text(current_text)

    changed = previous != current
    added, removed = (
        _evidence_diff(previous, current) if changed else ([], [])
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "source_url": source_url,
        "change_detected": changed,
        "previous_sha256": sha256_text(previous),
        "current_sha256": sha256_text(current),
        "change_type": (
            _classify_change(added, removed, comparison_type)
            if changed
            else "unknown"
        ),
        "summary": (
            "Detected a normalized text change in the submitted versions."
            if changed
            else "No normalized text change detected."
        ),
        "added_evidence": added,
        "removed_evidence": removed,
        "metadata": {
            "previous_characters": len(previous),
            "current_characters": len(current),
            "processing_ms": round(
                (time.perf_counter() - started) * 1000
            ),
        },
    }
