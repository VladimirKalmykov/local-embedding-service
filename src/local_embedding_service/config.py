from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_MODEL_ID = "intfloat/multilingual-e5-large"
DEFAULT_DIMENSIONS = 1024
DEFAULT_BATCH_SIZE = 16
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 7342


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    model_id: str = DEFAULT_MODEL_ID
    dimensions: int = DEFAULT_DIMENSIONS
    batch_size: int = DEFAULT_BATCH_SIZE
    model_cache: Path = _project_root() / ".models"
    bearer_token: str | None = None
    max_request_bytes: int = 1_048_576
    max_batch_size: int = 64
    max_text_chars: int = 100_000
    max_total_chars: int = 250_000

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            host=os.environ.get("LOCAL_EMBEDDING_HOST", DEFAULT_HOST),
            port=int(os.environ.get("LOCAL_EMBEDDING_PORT", DEFAULT_PORT)),
            model_id=os.environ.get("LOCAL_EMBEDDING_MODEL", DEFAULT_MODEL_ID),
            dimensions=int(
                os.environ.get("LOCAL_EMBEDDING_DIMENSIONS", DEFAULT_DIMENSIONS)
            ),
            batch_size=int(
                os.environ.get("LOCAL_EMBEDDING_BATCH_SIZE", DEFAULT_BATCH_SIZE)
            ),
            model_cache=Path(
                os.environ.get(
                    "LOCAL_EMBEDDING_MODEL_CACHE",
                    str(_project_root() / ".models"),
                )
            ),
            bearer_token=os.environ.get("LOCAL_EMBEDDING_BEARER_TOKEN") or None,
        )

