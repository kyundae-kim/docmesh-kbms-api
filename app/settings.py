import os
from dataclasses import dataclass, field


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


def _env_bool(name: str, default: bool) -> bool:
    return _env(name, str(default)).lower() == "true"


def _env_int(name: str, default: int) -> int:
    return int(_env(name, str(default)))


@dataclass(frozen=True)
class Settings:
    database_url: str = field(
        default_factory=lambda: _env(
            "KBMS_DATABASE_URL", "sqlite+aiosqlite:///./kbms.db"
        )
    )
    minio_endpoint: str = field(
        default_factory=lambda: _env("KBMS_MINIO_ENDPOINT", "minio:9000")
    )
    minio_access_key: str = field(
        default_factory=lambda: _env("KBMS_MINIO_ACCESS_KEY", "minioadmin")
    )
    minio_secret_key: str = field(
        default_factory=lambda: _env("KBMS_MINIO_SECRET_KEY", "minioadmin123")
    )
    minio_bucket: str = field(
        default_factory=lambda: _env("KBMS_MINIO_BUCKET", "kbms-documents")
    )
    minio_secure: bool = field(
        default_factory=lambda: _env_bool("KBMS_MINIO_SECURE", False)
    )
    ollama_endpoint: str = field(
        default_factory=lambda: _env(
            "KBMS_OLLAMA_ENDPOINT", "http://192.168.219.106:11434"
        )
    )
    ollama_model: str = field(
        default_factory=lambda: _env("KBMS_OLLAMA_MODEL", "bge-m3")
    )
    milvus_uri: str = field(
        default_factory=lambda: _env("KBMS_MILVUS_URI", "./milvus.db")
    )
    user_id: str = field(default_factory=lambda: _env("KBMS_USER_ID", "dms"))
    collection_name: str = field(
        default_factory=lambda: _env("KBMS_COLLECTION_NAME", "kbms_documents")
    )
    vector_dimension: int = field(
        default_factory=lambda: _env_int("KBMS_VECTOR_DIMENSION", 1024)
    )
    chunk_size: int = field(
        default_factory=lambda: _env_int("KBMS_CHUNK_SIZE", 1000)
    )
    overlap: int = field(
        default_factory=lambda: _env_int("KBMS_CHUNK_OVERLAP", 100)
    )
