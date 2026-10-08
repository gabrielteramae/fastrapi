from __future__ import annotations

import inspect
import json
import re
from typing import Any, Awaitable, Callable
from urllib.parse import parse_qs, unquote

Handler = Callable[["Request"], Any | Awaitable[Any]]

_PARAM = re.compile(r"^\{([A-Za-z_][A-Za-z0-9_]*)\}$")


def compile_path(path: str) -> tuple[re.Pattern[str], list[str]]:
    if path == "/":
        return re.compile(r"^/$"), []
    names: list[str] = []
    parts: list[str] = []
    for seg in path.strip("/").split("/"):
        match = _PARAM.fullmatch(seg)
        if match:
            names.append(match.group(1))
            parts.append(r"([^/]+)")
        else:
            parts.append(re.escape(seg))
    return re.compile("^/" + "/".join(parts) + "/?$"), names


class Request:
    def __init__(self, scope: dict[str, Any], receive: Callable[..., Awaitable[dict[str, Any]]]):
        self.scope = scope
        self.method = scope.get("method", "GET")
        self.path = scope.get("path", "/")
        raw_query = scope.get("query_string", b"")
        if isinstance(raw_query, bytes):
            raw_query = raw_query.decode()
        self.query = {key: values[-1] for key, values in parse_qs(raw_query).items()}
        self.path_params: dict[str, str] = {}
        self._receive = receive
        self._body: bytes | None = None

    async def body(self) -> bytes:
        if self._body is None:
            chunks: list[bytes] = []
            while True:
                message = await self._receive()
                if message["type"] == "http.disconnect":
                    break
                if message["type"] != "http.request":
                    continue
                chunks.append(message.get("body", b""))
                if not message.get("more_body", False):
                    break
            self._body = b"".join(chunks)
        return self._body

    async def json(self) -> Any:
        raw = await self.body()
        if not raw:
            return None
        return json.loads(raw.decode())


class JSONResponse:
    def __init__(self, data: Any, status: int = 200):
        self.status = status
        self.body = json.dumps(data, ensure_ascii=False).encode()
        self.headers = [
            (b"content-type", b"application/json; charset=utf-8"),
            (b"content-length", str(len(self.body)).encode()),
        ]


class _Route:
    def __init__(self, method: str, path: str, endpoint: Handler):
        self.method = method
        self.path = path
        self.endpoint = endpoint
        self.regex, self.names = compile_path(path)


class FastrAPI:
    """Aplicação ASGI. `app` entra direto num servidor ASGI, ou em `fastrapi.serve`."""

    def __init__(self) -> None:
        self.routes: list[_Route] = []

    def route(self, method: str, path: str) -> Callable[[Handler], Handler]:
        def decorator(endpoint: Handler) -> Handler:
            self.routes.append(_Route(method.upper(), path, endpoint))
            return endpoint

        return decorator

    def get(self, path: str) -> Callable[[Handler], Handler]:
        return self.route("GET", path)

    def post(self, path: str) -> Callable[[Handler], Handler]:
        return self.route("POST", path)

    def put(self, path: str) -> Callable[[Handler], Handler]:
        return self.route("PUT", path)

    def delete(self, path: str) -> Callable[[Handler], Handler]:
        return self.route("DELETE", path)

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            return
        method = scope.get("method", "GET").upper()
        path = scope.get("path", "/")
        for route in self.routes:
            if route.method != method:
                continue
            match = route.regex.match(path)
            if not match:
                continue
            request = Request(scope, receive)
            request.path_params = {
                name: unquote(match.group(index + 1)) for index, name in enumerate(route.names)
            }
            try:
                result = route.endpoint(request)
                if inspect.isawaitable(result):
                    result = await result
                response = _coerce(result)
            except Exception as exc:  # noqa: BLE001 — vira JSON 500, sem stack no cliente
                response = JSONResponse({"detail": str(exc)}, 500)
            await _send(send, response)
            return
        await _send(send, JSONResponse({"detail": "Not Found"}, 404))


def _coerce(result: Any) -> JSONResponse:
    if isinstance(result, JSONResponse):
        return result
    if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], int):
        return JSONResponse(result[0], result[1])
    return JSONResponse(result)


async def _send(send: Any, response: JSONResponse) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": response.status,
            "headers": response.headers,
        }
    )
    await send({"type": "http.response.body", "body": response.body})
