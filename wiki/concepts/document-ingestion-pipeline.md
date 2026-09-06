---
title: Document Ingestion Pipeline
created: 2026-09-06
updated: 2026-09-06
type: concept
tags: [architecture, integration, storage, search, reliability, knowledge-management]
sources: [raw/articles/docmesh-kbms-api-reference.md, raw/articles/docmesh-kbms-examples.md]
confidence: high
---

# Document Ingestion Pipeline

`upload_document` performs a synchronous end-to-end knowledgeization workflow from the caller's perspective: it stores the original, extracts text when the MIME type is supported, chunks the text, creates embeddings, and indexes chunks in Milvus before returning.

## Supported input and state

The documented extraction types are `text/plain`, `text/markdown`, `text/html`, and `application/json`. Other MIME types can be stored as originals but do not produce chunks. Pipeline states are `uploaded`, `indexing`, `indexed`, `failed`, and `deleted`; status includes chunk count, error information, and update time.

## Failure and deletion semantics

If knowledgeization fails, the pipeline records `failed`, hard-deletes the uploaded document, removes partial indexing work, and re-raises the exception. Deletion removes the dms-core original and the document's Milvus vector records, then records `deleted`. This cleanup behavior prevents an apparently available document from leaving stale searchable vectors.

## Operational flow

A typical integration creates the facade, calls `upload_document`, checks for `indexed`, searches with an explicit partition and access context, retrieves metadata or original bytes, and finally calls `delete_document` when required. The host must dispose of the engine and shut down provider clients.

See [[knowledge-management-facade-api]] for the public method contract and [[docmesh-kbms]] for the provider architecture.
