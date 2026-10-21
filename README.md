# Local Embedding Service

Local per-user HTTP service for reusable text embeddings on this computer.

The service owns the embedding runtime and model cache. Client projects own
their source data, vector indexes, and embedding lifecycle.

## Initial API

- `GET /health`
- `GET /v1/models`
- `POST /v1/embeddings`

The first supported model is `intfloat/multilingual-e5-large` through
FastEmbed. Query and document prefixes are applied by the service.

## Development

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
$env:PYTHONPATH = "src"
python -m unittest discover -s tests
python -m local_embedding_service
```

Configuration is provided through environment variables:

- `LOCAL_EMBEDDING_HOST`, defaults to `127.0.0.1`
- `LOCAL_EMBEDDING_PORT`, defaults to `7342`
- `LOCAL_EMBEDDING_MODEL_CACHE`, defaults to `.models` in this repository
- `LOCAL_EMBEDDING_BEARER_TOKEN`, optional during development

See [the integration guide](docs/integration.md) for the complete HTTP
contract, batching rules, index invalidation metadata, and client examples.

