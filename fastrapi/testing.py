from __future__ import annotations

import asyncio
import json
from typing import Any

from fastrapi.app import FastrAPI


class Response:
    def __init__(self, status: int, body: bytes):
        self.status_code = status
        self.content = body
        self.text = body.decode()

    def json(self) -> Any:
        return json.loads(self.text or "null")


class TestClient:
    def __init__(self, app: FastrAPI):
        self.app = app

    def request(self, method: str, path: str, json_body: Any = None, raw: bytes | None = None) -> Response:
        raw_path, _, query = path.partition("?")
        if raw is not None:
            body = raw
        else:
            body = b"" if json_body is None else json.dumps(json_body).encode()
        sent: dict[str, Any] = {}

        async def receive() -> dict[str, Any]:
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                sent["status"] = message["status"]
            elif message["type"] == "http.response.body":
                sent["body"] = message.get("body", b"")

        scope = {
            "type": "http",
            "method": method.upper(),
            "path": raw_path or "/",
            "query_string": query.encode(),
            "headers": [],
        }
        asyncio.run(self.app(scope, receive, send))
        return Response(int(sent.get("status", 500)), sent.get("body", b""))

    def get(self, path: str) -> Response:
        return self.request("GET", path)

    def post(self, path: str, json_body: Any = None) -> Response:
        return self.request("POST", path, json_body)
