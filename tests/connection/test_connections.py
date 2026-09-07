import os

import ollama
import pytest
from pymilvus import MilvusClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.settings import Settings

pytestmark = [
    pytest.mark.connection,
    pytest.mark.skipif(
        os.getenv("KBMS_RUN_CONNECTION_TESTS") != "1",
        reason="set KBMS_RUN_CONNECTION_TESTS=1 to run provider checks",
    ),
]


@pytest.mark.asyncio
async def test_sqlite_memory_connection():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("select 1"))
            assert result.scalar_one() == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_sqlite_disk_connection(tmp_path):
    database_path = tmp_path / "connection.sqlite"
    engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}")
    try:
        async with engine.begin() as connection:
            await connection.execute(text("create table probe (value integer)"))
            await connection.execute(text("insert into probe values (1)"))
        async with engine.connect() as connection:
            result = await connection.execute(text("select value from probe"))
            assert result.scalar_one() == 1
    finally:
        await engine.dispose()
    assert database_path.exists()


@pytest.mark.asyncio
async def test_milvus_local_connection(tmp_path):
    client = MilvusClient(uri=str(tmp_path / "milvus.db"))
    try:
        assert client.list_collections() == []
    finally:
        client.close()


@pytest.mark.asyncio
async def test_ollama_connection_and_embedding_model():
    settings = Settings()
    client = ollama.AsyncClient(host=settings.ollama_endpoint)
    models = await client.list()
    model_names = {(model.model or "").split(":", 1)[0] for model in models.models}
    assert settings.ollama_model in model_names
