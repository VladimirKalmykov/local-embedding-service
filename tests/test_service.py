from __future__ import annotations

import unittest

from local_embedding_service.config import Settings
from local_embedding_service.errors import ValidationError
from local_embedding_service.service import EmbeddingService


class FakeBackend:
    def __init__(self) -> None:
        self.inputs: list[str] = []

    @property
    def loaded(self) -> bool:
        return True

    @property
    def runtime_version(self) -> str:
        return "test"

    def embed(self, texts, batch_size: int) -> list[list[float]]:
        self.inputs = list(texts)
        return [[float(len(text)), 1.0] for text in texts]


class EmbeddingServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.backend = FakeBackend()
        self.service = EmbeddingService(
            Settings(dimensions=2, max_batch_size=2),
            backend=self.backend,
        )

    def test_applies_query_prefix(self) -> None:
        result = self.service.create_embeddings(
            {"input_type": "query", "texts": ["архитектура интерфейсов"]}
        )
        self.assertEqual(["query: архитектура интерфейсов"], self.backend.inputs)
        self.assertEqual(2, result["dimensions"])
        self.assertEqual(1, result["usage"]["inputs"])

    def test_applies_document_prefix(self) -> None:
        self.service.create_embeddings(
            {"input_type": "document", "texts": ["Платформа расширений"]}
        )
        self.assertEqual(["passage: Платформа расширений"], self.backend.inputs)

    def test_rejects_unknown_model(self) -> None:
        with self.assertRaises(ValidationError) as raised:
            self.service.create_embeddings(
                {
                    "model": "another-model",
                    "input_type": "query",
                    "texts": ["test"],
                }
            )
        self.assertEqual("UNSUPPORTED_MODEL", raised.exception.code)

    def test_rejects_oversized_batch(self) -> None:
        with self.assertRaises(ValidationError) as raised:
            self.service.create_embeddings(
                {"input_type": "query", "texts": ["one", "two", "three"]}
            )
        self.assertEqual("BATCH_TOO_LARGE", raised.exception.code)


if __name__ == "__main__":
    unittest.main()

