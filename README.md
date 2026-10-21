# Local Embedding Service

Local per-user HTTP service for reusable text embeddings on this computer.

The service owns the embedding runtime and model cache. Client projects own
their source data, vector indexes, and embedding lifecycle.

Dependencies are pinned in `requirements/service.lock.txt`. The model cache is
stored in `.models/`, ignored by Git, and shared by every local client through
the HTTP API instead of being copied into each project.

## Initial API

- `GET /health`
- `GET /v1/models`
- `POST /v1/embeddings`

The first supported model is `intfloat/multilingual-e5-large` through
FastEmbed. Query and document prefixes are applied by the service.

## Development

```powershell
.\scripts\setup.ps1
.\scripts\run.ps1
```

Use `.\scripts\verify.ps1` to verify the installed environment and model
without starting the HTTP server. Pass `-SkipModel` for a configuration-only
check.

## Windows autostart

Install a per-user Scheduled Task and immediately verify the running service:

```powershell
.\scripts\install-autostart.ps1
```

The task runs only for the current interactive user, uses no administrator
privileges, starts in a hidden window, and keeps the model lazy-loaded until
the first embedding request.

```powershell
.\scripts\status-autostart.ps1
.\scripts\uninstall-autostart.ps1
```

Configuration is provided through environment variables:

- `LOCAL_EMBEDDING_HOST`, defaults to `127.0.0.1`
- `LOCAL_EMBEDDING_PORT`, defaults to `7342`
- `LOCAL_EMBEDDING_MODEL_CACHE`, defaults to `.models` in this repository

See [the integration guide](docs/integration.md) for the complete HTTP
contract, batching rules, index invalidation metadata, and client examples.

