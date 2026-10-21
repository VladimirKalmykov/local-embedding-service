from __future__ import annotations

import json
import threading
import unittest
import urllib.error
import urllib.request

from local_embedding_service.config import Settings
from local_embedding_service.server import ServiceHttpServer
from local_embedding_service.service import EmbeddingService


class FakeBackend:
    @property
    def loaded(self) -> bool:
        return True

    @property
    def runtime_version(self) -> str:
        return "test"

    def embed(self, texts, batch_size: int) -> list[list[float]]:
        return [[float(len(text)), 1.0] for text in texts]


class HttpApiTests(unittest.TestCase):
    def setUp(self) -> None:
        settings = Settings(
            host="127.0.0.1",
            port=0,
            dimensions=2,
            bearer_token="test-token",
        )
        service = EmbeddingService(settings, backend=FakeBackend())
        self.server = ServiceHttpServer((settings.host, settings.port), service)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, path: str, payload=None, token: str | None = "test-token"):
        headers = {}
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode("utf-8")
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        request = urllib.request.Request(
            self.base_url + path,
            data=data,
            headers=headers,
            method="POST" if payload is not None else "GET",
        )
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_health(self) -> None:
        status, result = self.request("/health")
        self.assertEqual(200, status)
        self.assertEqual("ready", result["status"])

    def test_create_embeddings(self) -> None:
        status, result = self.request(
            "/v1/embeddings",
            {"input_type": "query", "texts": ["архитектура"]},
        )
        self.assertEqual(200, status)
        self.assertEqual(2, result["dimensions"])
        self.assertEqual(1, len(result["vectors"]))

    def test_requires_token(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as raised:
            self.request("/health", token=None)
        self.assertEqual(401, raised.exception.code)


if __name__ == "__main__":
    unittest.main()

