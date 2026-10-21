from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from .backend import EmbeddingBackend, FastEmbedBackend
from .config import Settings
from .errors import BackendUnavailableError, ValidationError


INPUT_POLICY_VERSION = 1
SUPPORTED_INPUT_TYPES = {
    "query": "query: ",
    "document": "passage: ",
}


class EmbeddingService:
    def __init__(
        self,
        settings: Settings,
        backend: EmbeddingBackend | None = None,
    ) -> None:
        self.settings = settings
        self.backend = backend or FastEmbedBackend(
            settings.model_id,
            settings.model_cache,
        )

    def model_fingerprint(self) -> str:
        payload = {
            "provider": "fastembed",
            "runtime_version": self.backend.runtime_version,
            "model_id": self.settings.model_id,
            "dimensions": self.settings.dimensions,
            "input_policy_version": INPUT_POLICY_VERSION,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def health(self) -> dict[str, Any]:
        return {
            "status": "ready",
            "model_loaded": self.backend.loaded,
            "model_id": self.settings.model_id,
            "dimensions": self.settings.dimensions,
        }

    def models(self) -> dict[str, Any]:
        return {
            "models": [
                {
                    "id": self.settings.model_id,
                    "provider": "fastembed",
                    "dimensions": self.settings.dimensions,
                    "input_types": sorted(SUPPORTED_INPUT_TYPES),
                    "input_policy_version": INPUT_POLICY_VERSION,
                    "fingerprint": self.model_fingerprint(),
                }
            ]
        }

    def create_embeddings(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        model_id = payload.get("model", self.settings.model_id)
        if model_id != self.settings.model_id:
            raise ValidationError(
                "UNSUPPORTED_MODEL",
                f"Only {self.settings.model_id} is currently supported.",
            )

        input_type = payload.get("input_type")
        if input_type not in SUPPORTED_INPUT_TYPES:
            raise ValidationError(
                "INVALID_INPUT_TYPE",
                "input_type must be query or document.",
            )

        texts = payload.get("texts")
        if not isinstance(texts, list) or not texts:
            raise ValidationError(
                "INVALID_TEXTS",
                "texts must be a non-empty array of strings.",
            )
        if len(texts) > self.settings.max_batch_size:
            raise ValidationError(
                "BATCH_TOO_LARGE",
                f"At most {self.settings.max_batch_size} texts are allowed per request.",
            )

        cleaned: list[str] = []
        total_chars = 0
        for index, value in enumerate(texts):
            if not isinstance(value, str) or not value.strip():
                raise ValidationError(
                    "INVALID_TEXT",
                    f"texts[{index}] must be a non-empty string.",
                )
            text = value.strip()
            if len(text) > self.settings.max_text_chars:
                raise ValidationError(
                    "TEXT_TOO_LARGE",
                    f"texts[{index}] exceeds the per-text character limit.",
                )
            total_chars += len(text)
            cleaned.append(text)

        if total_chars > self.settings.max_total_chars:
            raise ValidationError(
                "REQUEST_TOO_LARGE",
                "The combined text size exceeds the request limit.",
            )

        prefix = SUPPORTED_INPUT_TYPES[input_type]
        prepared = [prefix + text for text in cleaned]
        vectors = self.backend.embed(prepared, self.settings.batch_size)
        if len(vectors) != len(prepared):
            raise BackendUnavailableError(
                "The embedding backend returned an unexpected vector count."
            )
        for vector in vectors:
            if len(vector) != self.settings.dimensions:
                raise BackendUnavailableError(
                    "The embedding backend returned an unexpected vector dimension."
                )

        return {
            "model": self.settings.model_id,
            "model_fingerprint": self.model_fingerprint(),
            "dimensions": self.settings.dimensions,
            "input_type": input_type,
            "input_policy_version": INPUT_POLICY_VERSION,
            "input_hashes": [
                hashlib.sha256(text.encode("utf-8")).hexdigest()
                for text in prepared
            ],
            "vectors": vectors,
            "usage": {"inputs": len(prepared), "characters": total_chars},
        }

