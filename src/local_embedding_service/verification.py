from __future__ import annotations

import argparse
import json
from typing import Any

from .config import Settings
from .service import EmbeddingService


def verify(skip_model: bool = False) -> dict[str, Any]:
    settings = Settings.from_environment()
    service = EmbeddingService(settings)
    result: dict[str, Any] = {
        "status": "ready",
        "host": settings.host,
        "port": settings.port,
        "model": settings.model_id,
        "dimensions": settings.dimensions,
        "model_cache": str(settings.model_cache),
        "model_checked": False,
    }
    if not skip_model:
        response = service.create_embeddings(
            {
                "model": settings.model_id,
                "input_type": "document",
                "texts": ["local embedding service verification"],
            }
        )
        vector = response["vectors"][0]
        result["model_checked"] = True
        result["model_loaded"] = service.backend.loaded
        result["dimensions_ok"] = len(vector) == settings.dimensions
        result["model_fingerprint"] = response["model_fingerprint"]
        result["status"] = "ready" if result["dimensions_ok"] else "failed"
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify Local Embedding Service")
    parser.add_argument(
        "--skip-model",
        action="store_true",
        help="verify configuration without loading the embedding model",
    )
    args = parser.parse_args()
    result = verify(skip_model=args.skip_model)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "ready":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

