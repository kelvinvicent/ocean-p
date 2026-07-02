"""
Database engine + session factory.

Configuración portable SQLite ↔ PostgreSQL (Neon):
- SQLite local:  `sqlite:///./ocean_p.db`
- Neon (prod):   `postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require`
"""

from typing import Generator

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.config import settings


def _build_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite"):
        # SQLite local: necesita check_same_thread=False para FastAPI
        return create_engine(
            database_url,
            echo=False,
            connect_args={"check_same_thread": False},
        )
    # PostgreSQL / Neon: pool pequeño + recycle para serverless
    return create_engine(
        database_url,
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=300,
    )


engine: Engine = _build_engine(settings.DATABASE_URL)


def init_db() -> None:
    """Crea todas las tablas (uso: tests, dev rápido). En producción usar Alembic."""
    # Importar los modelos para que SQLModel los registre
    from app.models import (  # noqa: F401
        User,
        TestSession,
        ItemResponse,
        Score,
        Report,
        EmailDelivery,
        NormTable,
    )
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Dependencia FastAPI: yield de una sesión y cierre al final."""
    with Session(engine) as session:
        yield session
