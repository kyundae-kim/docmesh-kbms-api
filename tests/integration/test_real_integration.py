import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.settings import Settings


@pytest.mark.real_integration
@pytest.mark.skipif(
    os.getenv("KBMS_RUN_REAL_INTEGRATION") != "1",
    reason="set KBMS_RUN_REAL_INTEGRATION=1 to run live-provider integration",
)
def test_document_lifecycle_against_live_providers(tmp_path):
    document_id = f"integration-{uuid4().hex}"
    settings = Settings(
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'kbms.sqlite'}",
        milvus_uri=str(tmp_path / "milvus.db"),
        collection_name=f"integration_{uuid4().hex}",
    )

    with TestClient(create_app(settings=settings)) as client:
        deleted = False
        try:
            upload = client.post(
                "/documents",
                files={
                    "file": (
                        "integration.txt",
                        b"live knowledge document",
                        "text/plain",
                    )
                },
                data={
                    "title": "Live integration document",
                    "source_uri": "https://example.test/integration",
                    "partition_kind": "personal",
                    "partition_id": "dms",
                    "document_id": document_id,
                    "metadata": '{"suite":"real"}',
                },
            )
            assert upload.status_code == 201, upload.text
            assert upload.json()["document_id"] == document_id

            status = client.get(f"/documents/{document_id}/status")
            assert status.status_code == 200
            assert status.json()["status"] == "indexed"

            listing = client.get(
                "/documents",
                params={"partition_kind": "personal", "partition_id": "dms"},
            )
            assert listing.status_code == 200
            assert any(
                item["document_id"] == document_id
                for item in listing.json()["items"]
            )

            metadata = client.get(
                f"/documents/{document_id}",
                params={"partition_kind": "personal", "partition_id": "dms"},
            )
            assert metadata.status_code == 200
            assert metadata.json()["metadata"]["title"] == (
                "Live integration document"
            )

            content = client.get(
                f"/documents/{document_id}/content",
                params={"partition_kind": "personal", "partition_id": "dms"},
            )
            assert content.status_code == 200
            assert content.content == b"live knowledge document"

            search = client.post(
                "/search",
                json={
                    "query": "knowledge document",
                    "limit": 5,
                    "partition_kind": "personal",
                    "partition_id": "dms",
                },
            )
            assert search.status_code == 200
            assert any(
                hit["document_id"] == document_id for hit in search.json()
            )

            deletion = client.delete(
                f"/documents/{document_id}",
                params={
                    "partition_kind": "personal",
                    "partition_id": "dms",
                    "hard_delete": "true",
                },
            )
            assert deletion.status_code == 204
            deleted = True

            deleted_status = client.get(f"/documents/{document_id}/status")
            assert deleted_status.status_code == 200
            assert deleted_status.json()["status"] == "deleted"
        finally:
            if not deleted:
                client.delete(
                    f"/documents/{document_id}",
                    params={
                        "partition_kind": "personal",
                        "partition_id": "dms",
                        "hard_delete": "true",
                    },
                )
