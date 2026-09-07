---
title: Knowledge Management Facade API
created: 2026-09-06
updated: 2026-09-06
type: concept
tags: [rest, http, endpoint, architecture, integration, knowledge-management, documentation]
sources: [raw/articles/docmesh-kbms-api-reference.md, raw/articles/docmesh-kbms-examples.md]
confidence: high
---

# Knowledge Management Facade API

The `KnowledgeManagement` facade is the public API boundary for document knowledge management. It hides provider-specific coordination while exposing asynchronous operations for ingestion, status, listing, metadata, original content, deletion, and semantic search.

## Contract design

The constructor receives host-owned infrastructure clients: SQLAlchemy `Engine`/`AsyncEngine`, MinIO, Ollama, and Milvus. The API keeps provider lifecycle management outside the facade. Every public method is async, and an async engine/client combination should be used for the native async path.

The document API uses explicit partition parameters. Listing and retrieval require `partition_kind` and `partition_id`; search additionally supports `limit` and optional document filtering. Cursor pagination returns `items`, `next_cursor`, and `has_more`, making `list_documents` suitable for bounded page traversal.

## Search authorization

`AccessContext` carries user, tenant, group, and role information. Authorized search requires a complete partition scope. A personal partition must match `access_context.user_id`; a group partition must match `access_context.groups`. Invalid scope raises `PermissionError`, while an empty query or non-positive limit raises `ValueError`.

## Related concepts

The API's most important state transition is described in [[document-ingestion-pipeline]]. The provider composition and system boundary are summarized in [[docmesh-kbms]].
