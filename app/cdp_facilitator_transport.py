from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any

from .cdp_config import CDPConfig


class CDPFacilitatorTransport:
    def __init__(
        self,
        *,
        config: CDPConfig,
        http_request: Any | None = None,
    ) -> None:
        self._config = config
        self._http_request = http_request

    def _make_jwt(self) -> str:
        header = {
            "alg": "HS256",
            "typ": "JWT",
            "kid": self._config.api_key_name,
        }

        now = int(time.time())
        payload = {
            "iss": "cdp",
            "sub": self._config.api_key_name,
            "exp": now + 60,
            "iat": now,
            "aud": ["cdp"],
        }

        header_b64 = _base64url_encode(json.dumps(header).encode("utf-8"))
        payload_b64 = _base64url_encode(json.dumps(payload).encode("utf-8"))

        message = f"{header_b64}.{payload_b64}"
        signature = hmac.new(
            self._config.api_key_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        signature_b64 = _base64url_encode(signature)

        return f"{header_b64}.{payload_b64}.{signature_b64}"

    def request(
        self,
        *,
        method: str,
        url: str,
        json: dict[str, Any],
        headers: dict[str, str],
    ) -> dict[str, Any]:
        if self._http_request is None:
            raise RuntimeError(
                "CDP transport requires an explicit http_request callable"
            )

        jwt = self._make_jwt()
        merged_headers = {
            **headers,
            "authorization": f"Bearer {jwt}",
            "content-type": "application/json",
        }

        response = self._http_request(
            method=method,
            url=url,
            json=json,
            headers=merged_headers,
        )

        if not isinstance(response, dict):
            raise RuntimeError("CDP response must be an object")

        return response


def _base64url_encode(data: bytes) -> str:
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")
