import asyncio
import json
import unittest
import urllib.request

from fastrapi import FastrAPI
from fastrapi.serve import _client
from fastrapi.testing import TestClient


def build():
    app = FastrAPI()

    @app.get("/")
    def root(request):
        return {"ok": True}

    @app.get("/items/{item_id}")
    def item(request):
        return {"item_id": request.path_params["item_id"], "q": request.query.get("q")}

    @app.post("/echo")
    async def echo(request):
        return {"echo": await request.json()}

    @app.get("/boom")
    def boom(request):
        raise RuntimeError("quebrou")

    return app


class AppTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(build())

    def test_root(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["ok"], True)

    def test_path_and_query(self):
        response = self.client.get("/items/abc%20d?q=1")
        self.assertEqual(response.json(), {"item_id": "abc d", "q": "1"})

    def test_post(self):
        response = self.client.post("/echo", {"n": 3})
        self.assertEqual(response.json(), {"echo": {"n": 3}})

    def test_missing(self):
        self.assertEqual(self.client.get("/nope").status_code, 404)

    def test_error_is_json(self):
        response = self.client.get("/boom")
        self.assertEqual(response.status_code, 500)
        self.assertIn("quebrou", response.json()["detail"])

    def test_http_server(self):
        app = build()

        async def main():
            server = await asyncio.start_server(lambda r, w: _client(app, r, w), "127.0.0.1", 0)
            port = server.sockets[0].getsockname()[1]

            def hit():
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/items/9?q=z") as res:
                    return res.status, json.loads(res.read().decode())

            status, payload = await asyncio.to_thread(hit)
            server.close()
            await server.wait_closed()
            return status, payload

        status, payload = asyncio.run(main())
        self.assertEqual(status, 200)
        self.assertEqual(payload["item_id"], "9")
        self.assertEqual(payload["q"], "z")


if __name__ == "__main__":
    unittest.main()
