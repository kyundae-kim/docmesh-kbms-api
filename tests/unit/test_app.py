import pytest
from fastapi import HTTPException

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
    [(PermissionError("no"), 403), (ValueError("bad"), 422)],
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
