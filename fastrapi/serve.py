from __future__ import annotations

import asyncio
from typing import Any

from fastrapi.app import FastrAPI


async def _client(app: FastrAPI, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        request_line = await asyncio.wait_for(reader.readline(), timeout=15)
        if not request_line:
            return
        method, raw_target, *_rest = request_line.decode("latin1").split(" ")
        path, _, query = raw_target.partition("?")
        headers: list[tuple[bytes, bytes]] = []
        while True:
            line = await reader.readline()
            if line in (b"\r\n", b"\n", b""):
                break
            name, _, value = line.decode("latin1").partition(":")
            headers.append((name.strip().lower().encode(), value.strip().encode()))
        length = 0
        try:
            for name, value in headers:
                if name == b"content-length":
                    length = int(value)
            if length < 0:
                raise ValueError(length)
        except ValueError:
            writer.write(b"HTTP/1.1 400 Error\r\ncontent-length: 0\r\nconnection: close\r\n\r\n")
            await writer.drain()
            return
        body = await reader.readexactly(length) if length else b""
        messages: list[dict[str, Any]] = []

        async def receive() -> dict[str, Any]:
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message: dict[str, Any]) -> None:
            messages.append(message)

        await app(
            {
                "type": "http",
                "http_version": "1.1",
                "method": method,
                "scheme": "http",
                "path": path or "/",
                "raw_path": (path or "/").encode(),
                "query_string": query.encode(),
                "headers": headers,
            },
            receive,
            send,
        )
        status = 500
        resp_headers: list[tuple[bytes, bytes]] = []
        chunks: list[bytes] = []
        for message in messages:
            if message["type"] == "http.response.start":
                status = int(message["status"])
                resp_headers = list(message.get("headers", []))
            elif message["type"] == "http.response.body":
                chunks.append(message.get("body", b""))
        reason = "OK" if status < 400 else "Error"
        writer.write(f"HTTP/1.1 {status} {reason}\r\n".encode())
        for key, value in resp_headers:
            writer.write(key + b": " + value + b"\r\n")
        writer.write(b"connection: close\r\n\r\n")
        for chunk in chunks:
            writer.write(chunk)
        await writer.drain()
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass


async def serve(app: FastrAPI, host: str = "127.0.0.1", port: int = 8000) -> None:
    server = await asyncio.start_server(lambda r, w: _client(app, r, w), host, port)
    sockets = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
    print(f"fastrapi em {sockets}")
    async with server:
        await server.serve_forever()


def serve_blocking(app: FastrAPI, host: str = "127.0.0.1", port: int = 8000) -> None:
    asyncio.run(serve(app, host, port))
