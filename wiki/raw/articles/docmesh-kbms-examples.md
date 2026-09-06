---
source_url: https://github.com/kyundae-kim/docmesh-kbms/wiki/Examples
ingested: 2026-09-06
sha256: 09506ee8bd8b0ed521e5db52de02cc6c19f0435f910b6a558318e5aecc769f53
---

# Examples

These examples target `docmesh-kbms==0.1.0` and baseline commit `d8a78296262adb3baecdb1cc952495a0d8868b7`.

## Async facade setup
The host owns infrastructure client and engine lifecycles. The example uses SQLite and Milvus Lite; production can replace them with PostgreSQL, Milvus server, MinIO, and an Ollama endpoint.

```python
from pathlib import Path
import ollama
from minio import Minio
from pymilvus import AsyncMilvusClient
from sqlalchemy.ext.asyncio import create_async_engine
from kbms import KnowledgeManagement

engine = create_async_engine("sqlite+aiosqlite:///kbms.db")
facade = KnowledgeManagement(
    engine=engine,
    minio_client=Minio("localhost:9000", access_key="minioadmin", secret_key="minioadmin", secure=False),
    bucket_name="kbms-documents",
    ollama_client=ollama.AsyncClient(host="http://localhost:11434"),
    milvus_client=AsyncMilvusClient(uri=str(Path("milvus.db"))),
    embedding_model="bge-m3",
    collection_name="kbms_documents",
    vector_dimension=1024,
    chunk_size=1000,
    overlap=100,
)
```

Before execution, the MinIO bucket, Ollama model, and Milvus endpoint must be available. The application host manages client creation and shutdown.

## Upload and check status
```python
from dms import AccessContext

async def ingest() -> str:
    result = await facade.upload_document(
        content=b"Knowledge management systems organize searchable documents.",
        filename="intro.txt",
        content_type="text/plain",
        title="Knowledge management introduction",
        source_uri="https://example.com/intro",
        owner_id="user-001",
        partition_kind="personal",
        partition_id="user-001",
        created_by="user-001",
        metadata={"team": "platform"},
        access_context=AccessContext(user_id="user-001"),
    )
    status = await facade.get_pipeline_status(result.document_id)
    assert status is not None and status.status == "indexed"
    return result.document_id
```

`upload_document()` returns only after upload and knowledgeization finish. On failure it records `failed`, cleans up original and index, and raises the exception.

## Search and retrieve
```python
async def retrieve(document_id: str) -> None:
    context = AccessContext(user_id="user-001")
    hits = await facade.search(
        "searchable document", limit=5,
        partition_kind="personal", partition_id="user-001",
        access_context=context,
    )
    for hit in hits:
        print(hit.document_id, hit.chunk_index, hit.score, hit.source_uri)
        print(hit.text)
    metadata = await facade.get_document_metadata(
        document_id, partition_kind="personal", partition_id="user-001",
        access_context=context,
    )
    original = await facade.get_document_content(
        document_id, partition_kind="personal", partition_id="user-001",
        access_context=context,
    )
    Path(original.filename).write_bytes(original.content)
```

When an access context is supplied to search, both partition fields are mandatory. Personal partitions must equal the context user ID.

## Cursor pagination
```python
async def list_all_documents() -> list[str]:
    cursor = None
    document_ids: list[str] = []
    while True:
        page = await facade.list_documents(
            partition_kind="personal", partition_id="user-001",
            cursor=cursor, limit=100,
            access_context=AccessContext(user_id="user-001"),
        )
        document_ids.extend(item.document_id for item in page.items)
        if not page.has_more:
            break
        cursor = page.next_cursor
    return document_ids
```

## Delete and full flow
```python
async def remove(document_id: str) -> None:
    await facade.delete_document(
        document_id, partition_kind="personal", partition_id="user-001",
        hard_delete=True, access_context=AccessContext(user_id="user-001"),
    )
    status = await facade.get_pipeline_status(document_id)
    assert status is not None and status.status == "deleted"

async def main() -> None:
    document_id = await ingest()
    await retrieve(document_id)
    await remove(document_id)
# asyncio.run(main())
```

Deletion removes both the dms-core original and Milvus vector records. The host should call `await engine.dispose()` and each provider's shutdown procedure.
