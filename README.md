# docmesh-kbms REST API

FastAPI application layer for the `docmesh-kbms` knowledge-management facade.
The application exposes one fixed DMS identity (`dms`) and one fixed partition
(`personal` / `kbms`). It does not accept caller identities, access contexts, or
partition values from clients.

## Run locally

```bash
uv sync
uv run fastapi dev
```

The default application configuration uses:

- SQLite: `sqlite+aiosqlite:///./kbms.db`
- Milvus Lite: `./milvus.db`
- MinIO: `minio:9000` (`minioadmin` / `minioadmin123`)
- Ollama: `http://192.168.219.106:11434`, model `bge-m3`

When running the application outside the Docker Compose network, set
`KBMS_MINIO_ENDPOINT=localhost:9000`.

Start the development MinIO service with:

```bash
docker compose -f .devcontainer/docker-compose.minio.yml up -d
```

All settings can be overridden with `KBMS_*` environment variables. See
`app/settings.py` for the complete list.

## REST endpoints

- `POST /documents` — multipart upload (`file`, `title`, `source_uri`; optional
  `document_id`, JSON `metadata`)
- `GET /documents` — cursor-based document listing
- `GET /documents/{document_id}/status` — pipeline status
- `GET /documents/{document_id}` — metadata
- `GET /documents/{document_id}/content` — original bytes
- `DELETE /documents/{document_id}` — delete vectors and DMS document
- `POST /search` — semantic search with optional document/partition filters
- `GET /health` — process health

Interactive API documentation is available at `/docs`.

## Tests

```bash
# Unit and application integration tests
uv run pytest -q

# SQLite, local Milvus Lite, and live Ollama connection checks
KBMS_RUN_CONNECTION_TESTS=1 uv run pytest tests/connection -q

# Full live-provider API lifecycle; requires configured MinIO and Ollama
KBMS_RUN_REAL_INTEGRATION=1 uv run pytest tests/integration/test_real_integration.py -q
```

The live-provider suites are opt-in so ordinary CI does not require external
services.

## Docker

```bash
docker build -t docmesh-kbms-api .
docker run --rm -p 8000:8000 \
  --add-host=host.docker.internal:host-gateway \
  -e KBMS_MINIO_ENDPOINT=host.docker.internal:9000 \
  docmesh-kbms-api
```
