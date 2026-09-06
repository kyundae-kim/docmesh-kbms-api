---
source_url: https://github.com/kyundae-kim/docmesh-kbms/wiki/API-Reference
ingested: 2026-09-06
sha256: 1053962ecb0be804e78fde16861e988d6c6cef3e556db19b13d4f8d764725581
---

# API Reference

## Contract identifiers
- Package: `docmesh-kbms`
- Documentation version: `0.1.0`
- Baseline commit: `d8a78296262adb3baecdb1cc952495a0d8868b7b`
- Facade definition: `kbms/facade.py#L82-L575`
- Public export: `kbms/__init__.py#L2-L4`

The supported contract is `kbms.KnowledgeManagement` and its public methods. Internal `kbms.dms.*` implementation classes are not public API.

## Constructor
```python
KnowledgeManagement(
    *,
    engine: Engine | AsyncEngine,
    minio_client: Minio,
    bucket_name: str,
    ollama_client: Client | AsyncClient,
    milvus_client: MilvusClient | AsyncMilvusClient,
    access_policy: AccessPolicy | None = None,
    embedding_model: str = "bge-m3",
    collection_name: str = "kbms_documents",
    vector_dimension: int = 1024,
    chunk_size: int = 1000,
    overlap: int = 100,
) -> None
```

`engine` accepts SQLAlchemy `Engine` or `AsyncEngine`; async engines use the native async provider path. `minio_client` stores original documents, `bucket_name` is the dms-core bucket, `ollama_client` provides embeddings, and `milvus_client` stores vectors. Defaults are `bge-m3`, `kbms_documents`, dimension `1024`, chunk size `1000`, and overlap `100`. `overlap` must be non-negative and smaller than `chunk_size`.

## Public methods
All methods are async:

| Method | Purpose | Return |
|---|---|---|
| `upload_document` | Store original, extract text, chunk, embed, and index in Milvus | `dms.UploadDocumentResult` |
| `get_pipeline_status` | Read knowledgeization status | `PipelineState` |
| `list_documents` | Cursor-based document listing within a partition | `KnowledgeDocumentPage` |
| `get_document_metadata` | Read document metadata | `KnowledgeDocument` |
| `get_document_content` | Read original bytes | `dms.DocumentContent` |
| `delete_document` | Delete dms-core document and vector chunks | provider result |
| `search` | Semantic search | `list[SearchHit]` |

## Method contracts
`upload_document` requires non-empty `title` and `source_uri`; `partition_kind` is `personal` or `group`, and `partition_id` must be non-empty. The original is stored first. Supported extraction MIME types are `text/plain`, `text/markdown`, `text/html`, and `application/json`. Unsupported types are stored but produce no chunks. On knowledgeization failure, pipeline status becomes `failed`, the uploaded document is hard-deleted, and the exception is re-raised.

`get_pipeline_status(document_id)` returns `None` for an unknown ID and raises `ValueError` for an empty ID. `PipelineState` contains `document_id`, `status` (`uploaded | indexing | indexed | failed | deleted`), `chunks_count`, `error`, and `updated_at`.

`list_documents` accepts `partition_kind`, `partition_id`, optional `cursor`, and `limit` (default `100`). Its page has `items`, `next_cursor`, and `has_more`. A document has `document_id`, `filename`, `content_type`, `file_size`, `status`, timestamps, partition fields, optional `checksum`, optional `created_by`, and metadata.

`get_document_metadata` and `get_document_content` require document and partition identifiers. `DocumentContent` contains `document_id`, bytes, content type, filename, size, and checksum.

`delete_document` accepts `hard_delete=False`; it removes vector records, updates pipeline status to `deleted`, and can request a hard delete from dms-core.

`search` accepts a query, `limit` (default `5`), optional document and partition filters, and an optional access context. Empty queries and non-positive limits raise `ValueError`. `SearchHit` contains `document_id`, `chunk_index`, `text`, `score`, optional `start` and `end`, and optional `source_uri`.

## Authorization
`access_context` is a dms-core `AccessContext` with `user_id`, `tenant`, `groups`, and `roles`. Authorized search requires both `partition_kind` and `partition_id`. Personal partitions must match `access_context.user_id`; group partitions must match `access_context.groups`. Mismatches raise `PermissionError`.
