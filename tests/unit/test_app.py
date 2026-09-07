import pytest
from dms import DocumentDeletedError
from fastapi import HTTPException
from fastapi.testclient import TestClient

import app.main as main_module
from app.main import _content_disposition, _parse_metadata, _raise_http
from app.settings import Settings


def test_parse_metadata_accepts_json_object():
    assert _parse_metadata('{"source":"manual"}') == {"source": "manual"}
    assert _parse_metadata(None) is None


@pytest.mark.parametrize("raw_metadata", ["[]", '"text"', "invalid"])
def test_parse_metadata_rejects_non_object_json(raw_metadata):
    with pytest.raises((TypeError, ValueError), match="metadata must be a JSON object"):
        _parse_metadata(raw_metadata)


def test_content_disposition_removes_header_injection_characters():
    assert _content_disposition('a"\r\n.txt') == 'attachment; filename="a\'.txt"'


@pytest.mark.parametrize(
    ("error", "status_code"),
    [
        (PermissionError("no"), 403),
        (DocumentDeletedError("gone"), 410),
        (ValueError("bad"), 422),
    ],
)
def test_domain_input_errors_are_http_errors(error, status_code):
    with pytest.raises(HTTPException) as raised:
        _raise_http(error)
    assert raised.value.status_code == status_code


def test_settings_reads_environment_when_instantiated(monkeypatch):
    monkeypatch.setenv("KBMS_OLLAMA_ENDPOINT", "http://ollama.test:11434")
    monkeypatch.setenv("KBMS_VECTOR_DIMENSION", "768")
    settings = Settings()
    assert settings.ollama_endpoint == "http://ollama.test:11434"
    assert settings.vector_dimension == 768


def test_lifespan_closes_host_owned_clients(monkeypatch):
    class FakeEngine:
        def __init__(self):
            self.disposed = False

        async def dispose(self):
            self.disposed = True

    class FakeMilvus:
        def __init__(self):
            self.closed = False

        def has_collection(self, *, collection_name):
            return False

        def load_collection(self, *, collection_name):
            pass

        def close(self):
            self.closed = True

    class FakeOllama:
        def __init__(self):
            self.closed = False

        async def close(self):
            self.closed = True

    class FakeFacade:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    engine = FakeEngine()
    milvus = FakeMilvus()
    ollama_client = FakeOllama()

    monkeypatch.setattr(main_module, "create_async_engine", lambda _: engine)
    monkeypatch.setattr(main_module, "Minio", lambda *args, **kwargs: object())
    monkeypatch.setattr(
        main_module.ollama,
        "AsyncClient",
        lambda *args, **kwargs: ollama_client,
    )
    monkeypatch.setattr(main_module, "_create_milvus_client", lambda _: milvus)
    monkeypatch.setattr(main_module, "KnowledgeManagement", FakeFacade)

    with TestClient(main_module.create_app(settings=Settings())) as client:
        assert client.get("/health").json() == {"status": "ok"}

    assert engine.disposed
    assert milvus.closed
    assert ollama_client.closed


def test_lifespan_loads_existing_milvus_collection(monkeypatch):
    class FakeEngine:
        async def dispose(self):
            pass

    class FakeMilvus:
        def __init__(self):
            self.loaded_collection = None

        def has_collection(self, *, collection_name):
            return collection_name == "kbms_documents"

        def load_collection(self, *, collection_name):
            self.loaded_collection = collection_name

        def close(self):
            pass

    class FakeOllama:
        async def close(self):
            pass

    class FakeFacade:
        def __init__(self, **kwargs):
            pass

    engine = FakeEngine()
    milvus = FakeMilvus()

    monkeypatch.setattr(main_module, "create_async_engine", lambda _: engine)
    monkeypatch.setattr(main_module, "Minio", lambda *args, **kwargs: object())
    monkeypatch.setattr(
        main_module.ollama,
        "AsyncClient",
        lambda *args, **kwargs: FakeOllama(),
    )
    monkeypatch.setattr(main_module, "_create_milvus_client", lambda _: milvus)
    monkeypatch.setattr(main_module, "KnowledgeManagement", FakeFacade)

    with TestClient(main_module.create_app(settings=Settings())):
        pass

    assert milvus.loaded_collection == "kbms_documents"
