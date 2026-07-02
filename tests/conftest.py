"""
Fixtures compartidos para los tests de la API.

Sobrescribe `get_session` con una BD SQLite en memoria para cada test,
de modo que la suite sea totalmente aislada y rápida.

Uso desde un test:
    def test_x(client):                       # solo HTTP
        r = client.post('/foo')

    def test_y(client, engine):               # HTTP + acceso directo a BD
        with Session(engine) as db: ...
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlmodel import Session, SQLModel

# Forzar SQLite en memoria ANTES de importar la app (settings ya está cargado)
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.config import settings  # noqa: E402
from app.database import get_session  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def client(engine):
    def _override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
