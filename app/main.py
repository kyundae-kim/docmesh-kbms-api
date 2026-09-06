import inspect
import json
from contextlib import asynccontextmanager
from typing import Annotated, Any, NoReturn

import ollama
from dms import (
    AccessDeniedError,
    DocumentNotFoundError,
    DuplicateDocumentError,
    PayloadTooLargeError,
    ValidationError,
)
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response
from kbms import KnowledgeManagement
from minio import Minio
from pydantic import BaseModel, Field
from pymilvus import AsyncMilvusClient, MilvusClient
from sqlalchemy.ext.asyncio import create_async_engine

from .settings import Settings

_API_ERRORS = (
    AccessDeniedError,
    DocumentNotFoundError,
    DuplicateDocumentError,
    PayloadTooLargeError,
    PermissionError,
    TypeError,
    ValidationError,
    ValueError,
)


class SearchRequest(BaseModel):
    query: str
    limit: int = Field(default=5, gt=0)
    document_id: str | None = None
    partition_kind: str | None = None
    partition_id: str | None = None


def _encode(value: Any) -> Any:
    return jsonable_encoder(value)


def _raise_http(error: Exception) -> NoReturn:
    if isinstance(error, (AccessDeniedError, PermissionError)):
        raise HTTPException(status_code=403, detail=str(error)) from error
    if isinstance(error, DocumentNotFoundError):
        raise HTTPException(status_code=404, detail=str(error)) from error
    if isinstance(error, DuplicateDocumentError):
        raise HTTPException(status_code=409, detail=str(error)) from error
    if isinstance(error, PayloadTooLargeError):
        raise HTTPException(status_code=413, detail=str(error)) from error
    if isinstance(error, (TypeError, ValidationError, ValueError)):
        raise HTTPException(status_code=422, detail=str(error)) from error
    raise error


def _parse_metadata(raw_metadata: str | None) -> dict[str, Any] | None:
    if raw_metadata is None or not raw_metadata.strip():
        return None
    try:
        metadata = json.loads(raw_metadata)
    except json.JSONDecodeError as error:
        raise ValueError("metadata must be a JSON object") from error
    if not isinstance(metadata, dict):
        raise TypeError("metadata must be a JSON object")
    return metadata


def _content_disposition(filename: str) -> str:
    safe_filename = filename.replace("\\", "_").replace('"', "'")
    safe_filename = safe_filename.replace("\r", "").replace("\n", "")
    return f'attachment; filename="{safe_filename}"'


def _create_milvus_client(uri: str) -> MilvusClient | AsyncMilvusClient:
    if "://" in uri:
        return AsyncMilvusClient(uri=uri)
    return MilvusClient(uri=uri)


async def _close_milvus_client(client: MilvusClient | AsyncMilvusClient) -> None:
    result = client.close()
    if inspect.isawaitable(result):
        await result


def create_app(*, facade: Any | None = None, settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()
    resources: dict[str, Any] = {}

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if facade is None:
            engine = create_async_engine(config.database_url)
            minio_client = Minio(
                config.minio_endpoint,
                access_key=config.minio_access_key,
                secret_key=config.minio_secret_key,
                secure=config.minio_secure,
            )
            ollama_client = ollama.AsyncClient(host=config.ollama_endpoint)
            milvus_client = _create_milvus_client(config.milvus_uri)
            resources.update(engine=engine, milvus=milvus_client)
            app.state.facade = KnowledgeManagement(
                engine=engine,
                minio_client=minio_client,
                bucket_name=config.minio_bucket,
                ollama_client=ollama_client,
                milvus_client=milvus_client,
                embedding_model=config.ollama_model,
                collection_name=config.collection_name,
                vector_dimension=config.vector_dimension,
                chunk_size=config.chunk_size,
                overlap=config.overlap,
            )
        else:
            app.state.facade = facade
        yield
        if resources:
            await _close_milvus_client(resources["milvus"])
            await resources["engine"].dispose()

    app = FastAPI(title="docmesh-kbms REST API", version="0.1.0", lifespan=lifespan)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/documents", status_code=201)
    async def upload_document(
        file: Annotated[UploadFile, File()],
        title: Annotated[str, Form()],
        source_uri: Annotated[str, Form()],
        partition_kind: Annotated[str, Form()],
        partition_id: Annotated[str, Form()],
        document_id: Annotated[str | None, Form()] = None,
        metadata: Annotated[str | None, Form()] = None,
    ) -> Any:
        try:
            result = await app.state.facade.upload_document(
                content=await file.read(), filename=file.filename or "upload",
                content_type=file.content_type or "application/octet-stream",
                title=title, source_uri=source_uri, owner_id=config.user_id,
                partition_kind=partition_kind, partition_id=partition_id,
                document_id=document_id, created_by=config.user_id,
                metadata=_parse_metadata(metadata),
            )
            return _encode(result)
        except _API_ERRORS as error:
            _raise_http(error)

    @app.get("/documents")
    async def list_documents(
        partition_kind: str, partition_id: str, cursor: str | None = None,
        limit: Annotated[int, Query(gt=0, le=1000)] = 100,
    ) -> Any:
        try:
            return _encode(await app.state.facade.list_documents(
                partition_kind=partition_kind, partition_id=partition_id,
                cursor=cursor, limit=limit,
            ))
        except _API_ERRORS as error:
            _raise_http(error)

    @app.get("/documents/{document_id}/status")
    async def pipeline_status(document_id: str) -> Any:
        try:
            result = await app.state.facade.get_pipeline_status(document_id)
        except _API_ERRORS as error:
            _raise_http(error)
        if result is None:
            raise HTTPException(status_code=404, detail="Document not found")
        return _encode(result)

    @app.get("/documents/{document_id}")
    async def document_metadata(document_id: str, partition_kind: str, partition_id: str) -> Any:
        try:
            return _encode(await app.state.facade.get_document_metadata(
                document_id, partition_kind=partition_kind, partition_id=partition_id,
            ))
        except _API_ERRORS as error:
            _raise_http(error)

    @app.get("/documents/{document_id}/content")
    async def document_content(document_id: str, partition_kind: str, partition_id: str) -> Response:
        try:
            content = await app.state.facade.get_document_content(
                document_id, partition_kind=partition_kind, partition_id=partition_id,
            )
            return Response(content=content.content, media_type=content.content_type,
                            headers={"Content-Disposition": _content_disposition(content.filename)})
        except _API_ERRORS as error:
            _raise_http(error)

    @app.delete("/documents/{document_id}", status_code=204)
    async def delete_document(document_id: str, partition_kind: str, partition_id: str,
                              hard_delete: bool = False) -> None:
        try:
            await app.state.facade.delete_document(
                document_id, partition_kind=partition_kind, partition_id=partition_id,
                hard_delete=hard_delete,
            )
        except _API_ERRORS as error:
            _raise_http(error)

    @app.post("/search")
    async def search(request: SearchRequest) -> Any:
        try:
            hits = await app.state.facade.search(
                request.query, limit=request.limit, document_id=request.document_id,
                partition_kind=request.partition_kind, partition_id=request.partition_id,
            )
            return _encode(hits)
        except _API_ERRORS as error:
            _raise_http(error)

    return app


app = create_app()
