# Integrating with Local Embedding Service

## Purpose

Local Embedding Service provides one reusable embedding runtime and model cache
for projects on this computer. It does not own client documents, vector indexes,
or search logic.

Client projects are responsible for:

- deciding which text should be embedded;
- storing vectors and their metadata;
- deciding when an input is stale;
- implementing similarity and hybrid search;
- deleting vectors when source data is deleted.

The service is responsible for:

- loading the configured embedding model once;
- applying model-specific query and document prefixes;
- running batched inference;
- validating model and dimension contracts;
- returning stable metadata needed for index invalidation.

## Endpoint

The development endpoint is:

```text
http://127.0.0.1:7342
```

The service binds to loopback by default. It is not intended to be exposed to a
local network or the public internet.

## API

### Health

```http
GET /health
```

Example response:

```json
{
  "status": "ready",
  "model_loaded": false,
  "model_id": "intfloat/multilingual-e5-large",
  "dimensions": 1024
}
```

Calling `/health` does not load the model.

### Models

```http
GET /v1/models
```

The response describes supported input types, vector dimensions, the input
policy version, and a model fingerprint.

### Create embeddings

```http
POST /v1/embeddings
Content-Type: application/json
```

Request:

```json
{
  "model": "intfloat/multilingual-e5-large",
  "input_type": "document",
  "texts": [
    "Created a shared frontend platform for several product teams."
  ]
}
```

Response fields:

```json
{
  "model": "intfloat/multilingual-e5-large",
  "model_fingerprint": "...",
  "dimensions": 1024,
  "input_type": "document",
  "input_policy_version": 1,
  "input_hashes": ["..."],
  "vectors": [[0.01, -0.02]],
  "usage": {
    "inputs": 1,
    "characters": 62
  }
}
```

The example vector is abbreviated. Real vectors contain 1024 numbers.

## Query and document inputs

Clients send raw semantic text. They must not add E5 prefixes themselves.

Use:

- `query` for search queries;
- `document` for indexed records, sections, and claims.

The service currently translates them to:

```text
query: <text>
passage: <text>
```

This behavior is part of `input_policy_version`. A changed policy version must
invalidate vectors stored by clients.

## Batching and limits

One HTTP request accepts at most 64 texts. Clients should use batches of 16 by
default and combine returned vectors in request order.

Current limits:

- request body: 1 MiB;
- texts per request: 64;
- characters per text: 100,000;
- total characters per request: 250,000.

The response preserves the order of `texts`.

## Python example

This example uses only the Python standard library:

```python
import json
import urllib.request

payload = json.dumps(
    {
        "model": "intfloat/multilingual-e5-large",
        "input_type": "query",
        "texts": ["frontend platform architecture"],
    }
).encode("utf-8")

request = urllib.request.Request(
    "http://127.0.0.1:7342/v1/embeddings",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urllib.request.urlopen(request, timeout=120) as response:
    result = json.loads(response.read().decode("utf-8"))

vector = result["vectors"][0]
```

## TypeScript example

```typescript
const response = await fetch("http://127.0.0.1:7342/v1/embeddings", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    model: "intfloat/multilingual-e5-large",
    input_type: "document",
    texts: ["Shared frontend platform for several product teams."],
  }),
});

if (!response.ok) {
  throw new Error(`Embedding service failed with HTTP ${response.status}`);
}

const result = await response.json();
const vector: number[] = result.vectors[0];
```

This example is intended for server-side Node.js code. Browser access is not
supported, and the service does not provide CORS headers.

## Index validity

A stored vector should be considered current only when all of these values
match:

- source input hash;
- model ID;
- model fingerprint;
- dimensions;
- input policy version;
- the client project's own input template version.

The client's input template version represents how its domain data is converted
to semantic text. The service input policy version represents model-specific
encoding performed after that.

## Failure behavior

Clients should treat the following as unavailable semantic search, not as loss
of source data:

- connection refused or timeout;
- HTTP 503;
- unexpected model or dimension;
- invalid response shape.

A client with lexical search should continue in degraded lexical-only mode.
Do not delete existing vectors merely because the service is temporarily
unavailable.

## Local access boundary

The service does not use application-level authentication. It must remain bound
to loopback, must not be exposed through a reverse proxy, and must not enable
browser CORS access.

## Configuration

Supported environment variables:

| Variable | Default | Meaning |
|---|---|---|
| `LOCAL_EMBEDDING_HOST` | `127.0.0.1` | Listen address |
| `LOCAL_EMBEDDING_PORT` | `7342` | Listen port |
| `LOCAL_EMBEDDING_MODEL` | `intfloat/multilingual-e5-large` | Model ID |
| `LOCAL_EMBEDDING_DIMENSIONS` | `1024` | Expected dimensions |
| `LOCAL_EMBEDDING_BATCH_SIZE` | `16` | Inference batch size |
| `LOCAL_EMBEDDING_MODEL_CACHE` | `.models` | Shared model cache |

