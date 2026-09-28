from collections.abc import Awaitable, Callable

from starlette.types import ASGIApp, Message, Receive, Scope, Send


class ContentSizeLimitMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int = 2_500_000):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        content_length = None
        for key, value in scope.get("headers", []):
            if key.lower() == b"content-length":
                try:
                    content_length = int(value)
                except ValueError:
                    content_length = -1
                break

        if content_length is not None and content_length > self.max_bytes:
            await self._send_json(
                send,
                413,
                "request body exceeds the maximum allowed size",
            )
            return

        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()

            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise RequestTooLarge

            return message

        try:
            await self.app(scope, limited_receive, send)
        except RequestTooLarge:
            await self._send_json(
                send,
                413,
                "request body exceeds the maximum allowed size",
            )

    async def _send_json(
        self,
        send: Send,
        status: int,
        detail: str,
    ) -> None:
        body = (
            '{"status":"error",'
            '"error":"request_too_large",'
            f'"detail":"{detail}"}}'
        ).encode()

        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"cache-control", b"no-store"),
                ],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": body,
            }
        )


class RequestTooLarge(Exception):
    pass
