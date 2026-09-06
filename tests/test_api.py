from datetime import UTC, datetime
from types import SimpleNamespace

from dms import DocumentContent
from fastapi.testclient import TestClient
from kbms.facade import (
    KnowledgeDocument,
    KnowledgeDocumentPage,
    PipelineState,
    SearchHit,
)

from app.main import create_app
from app.settings import Settings


class FakeFacade:
    def __init__(self):
        self.upload_args = None

    async def upload_document(self, **kwargs):
        self.upload_args = kwargs
        return SimpleNamespace(document_id="doc-1", metadata={})

    async def get_pipeline_status(self, document_id):
        return PipelineState(document_id="doc-1", status="indexed", chunks_count=1,
                             error=None, updated_at=datetime.now(UTC))

    async def list_documents(self, **kwargs):
        return KnowledgeDocumentPage([], None, False)

    async def get_document_metadata(self, document_id, **kwargs):
        return KnowledgeDocument(
            document_id="doc-1", filename="a.txt", content_type="text/plain",
            file_size=3, status="indexed", created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC), partition_kind="personal",
            partition_id="dms", checksum=None, created_by="dms", metadata={},
        )

    async def get_document_content(self, document_id, **kwargs):
        return DocumentContent(document_id="doc-1", content=b"abc", content_type="text/plain",
                               filename="a.txt", size=3, checksum=None)

    async def delete_document(self, document_id, **kwargs):
        return None

    async def search(self, query, **kwargs):
        return [SearchHit("doc-1", 0, "abc", 0.9)]


def test_search_endpoint_returns_domain_hits():
    app = create_app(facade=FakeFacade(), settings=Settings())

    with TestClient(app) as client:
        response = client.post(
            "/search",
            json={"query": "abc", "limit": 5, "partition_kind": "personal", "partition_id": "dms"},
        )

    assert response.status_code == 200
    assert response.json() == [{"document_id": "doc-1", "chunk_index": 0, "text": "abc", "score": 0.9, "start": None, "end": None, "source_uri": None}]


def test_upload_endpoint_forwards_multipart_document():
    facade = FakeFacade()
    app = create_app(facade=facade, settings=Settings())

    with TestClient(app) as client:
        response = client.post(
            "/documents",
            files={"file": ("a.txt", b"abc", "text/plain")},
            data={
                "title": "A",
                "source_uri": "https://example.test/a",
                "partition_kind": "personal",
                "partition_id": "dms",
                "document_id": "doc-1",
                "metadata": '{"team":"platform"}',
            },
        )

    assert response.status_code == 201
    assert response.json()["document_id"] == "doc-1"
    assert facade.upload_args["content"] == b"abc"
    assert facade.upload_args["owner_id"] == "dms"
    assert facade.upload_args["created_by"] == "dms"
    assert facade.upload_args["document_id"] == "doc-1"
    assert facade.upload_args["metadata"] == {"team": "platform"}


def test_upload_endpoint_rejects_non_object_metadata():
    app = create_app(facade=FakeFacade(), settings=Settings())
    with TestClient(app) as client:
        response = client.post(
            "/documents",
            files={"file": ("a.txt", b"abc", "text/plain")},
            data={
                "title": "A",
                "source_uri": "https://example.test/a",
                "partition_kind": "personal",
                "partition_id": "dms",
                "metadata": "[]",
            },
        )
    assert response.status_code == 422


def test_content_endpoint_returns_original_bytes():
    app = create_app(facade=FakeFacade(), settings=Settings())

    with TestClient(app) as client:
        response = client.get("/documents/doc-1/content?partition_kind=personal&partition_id=dms")

    assert response.status_code == 200
    assert response.content == b"abc"
    assert response.headers["content-type"] == "text/plain; charset=utf-8"


def test_list_endpoint_returns_page():
    app = create_app(facade=FakeFacade(), settings=Settings())
    with TestClient(app) as client:
        response = client.get("/documents?partition_kind=personal&partition_id=dms")
    assert response.status_code == 200
    assert response.json() == {"items": [], "next_cursor": None, "has_more": False}


def test_metadata_endpoint_returns_document():
    app = create_app(facade=FakeFacade(), settings=Settings())
    with TestClient(app) as client:
        response = client.get(
            "/documents/doc-1?partition_kind=personal&partition_id=dms"
        )
    assert response.status_code == 200
    assert response.json()["document_id"] == "doc-1"


def test_status_endpoint_returns_pipeline_state():
    app = create_app(facade=FakeFacade(), settings=Settings())
    with TestClient(app) as client:
        response = client.get("/documents/doc-1/status")
    assert response.status_code == 200
    assert response.json()["status"] == "indexed"


def test_delete_endpoint_returns_no_content():
    app = create_app(facade=FakeFacade(), settings=Settings())
    with TestClient(app) as client:
        response = client.delete(
            "/documents/doc-1?partition_kind=personal&partition_id=dms"
        )
    assert response.status_code == 204
