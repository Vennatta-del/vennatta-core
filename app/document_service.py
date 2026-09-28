import hashlib
import re
import time
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup


MAX_DOCUMENT_BYTES = 2_000_000
FETCH_TIMEOUT = 20.0
ALLOWED_SCHEMES = {"http", "https"}


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES or not parsed.netloc:
        raise ValueError("document_url must be a valid HTTP(S) URL")


async def load_document(
    *,
    document_url: str | None,
    document_text: str | None,
) -> tuple[str, str | None]:
    if document_text:
        if len(document_text.encode("utf-8")) > MAX_DOCUMENT_BYTES:
            raise ValueError("document_text exceeds the size limit")
        return document_text, None

    if not document_url:
        raise ValueError("Provide document_url or document_text")

    _validate_url(document_url)

    timeout = httpx.Timeout(FETCH_TIMEOUT)
    limits = httpx.Limits(max_connections=4, max_keepalive_connections=2)

    async with httpx.AsyncClient(
        timeout=timeout,
        limits=limits,
        follow_redirects=False,
        headers={"User-Agent": "VennattaDocumentAgent/1.0"},
    ) as client:
        response = await client.get(document_url)
        response.raise_for_status()

        body = response.content
        if len(body) > MAX_DOCUMENT_BYTES:
            raise ValueError("remote document exceeds the size limit")

        content_type = response.headers.get("content-type", "")
        if "html" in content_type:
            text = BeautifulSoup(body, "html.parser").get_text(" ", strip=True)
        else:
            text = body.decode("utf-8", errors="replace")

    return text, content_type


def extract_document(
    *,
    text: str,
    source_url: str | None,
    extraction_mode: str,
) -> dict[str, Any]:
    started = time.perf_counter()
    normalized = re.sub(r"\s+", " ", text).strip()
    words = normalized.split()

    entities = sorted(
        {
            match.group(0)
            for match in re.finditer(
                r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b",
                normalized,
            )
        }
    )[:50]

    return {
        "source_url": source_url,
        "mode": extraction_mode,
        "text": normalized[:10000],
        "summary": normalized[:500],
        "entities": entities,
        "metadata": {
            "characters": len(normalized),
            "words": len(words),
            "sha256": hashlib.sha256(
                normalized.encode("utf-8")
            ).hexdigest(),
            "processing_ms": round(
                (time.perf_counter() - started) * 1000
            ),
        },
    }
