---
title: docmesh-kbms
created: 2026-09-06
updated: 2026-09-06
type: entity
tags: [entity, rest, architecture, integration, knowledge-management]
sources: [raw/articles/docmesh-kbms-api-reference.md, raw/articles/docmesh-kbms-examples.md]
confidence: high
---

# docmesh-kbms

`docmesh-kbms` exposes the `kbms.KnowledgeManagement` async facade for document storage, text extraction, chunking, embedding, vector indexing, metadata access, semantic search, and deletion. The documented contract targets version `0.1.0` and baseline commit `d8a78296262adb3baecdb1cc952495a0d8868b7`.

## Architecture role

The host application owns the SQLAlchemy engine and provider lifecycles. The facade coordinates dms-core for document state and original content, MinIO for object storage, Ollama for embeddings, and Milvus for vector records. SQLite/Milvus Lite are suitable for examples; production deployments can substitute PostgreSQL, Milvus server, MinIO, and an Ollama endpoint.

## Public surface

The main operations are `upload_document`, `get_pipeline_status`, `list_documents`, `get_document_metadata`, `get_document_content`, `delete_document`, and `search`. All are asynchronous. The constructor defaults to the `bge-m3` embedding model, `kbms_documents` collection, 1024-dimensional vectors, 1000-character chunks, and 100-character overlap.

## Integration and security

Documents are scoped by `partition_kind` (`personal` or `group`) and `partition_id`. When an `AccessContext` is supplied, authorized searches require both partition fields: personal partitions must match `user_id`, while group partitions must match the caller's groups. Failed indexing records a failed pipeline state, cleans up the uploaded document, and re-raises the exception.

See [[knowledge-management-facade-api]] for operation contracts and [[document-ingestion-pipeline]] for the upload-to-index lifecycle.
