from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.routers import emotional_health, quiz, report, views


@asynccontextmanager
async def lifespan(_: FastAPI):
    # En producción, las migraciones se aplican con `alembic upgrade head`
    # antes de arrancar la app. `init_db()` es un fallback para dev local
    # rápido sin Alembic (e idempotente: usa create_all que no rompe si
    # las tablas ya existen).
    init_db()
    yield


app = FastAPI(
    title="OCEAN-P Personality Test API",
    description="Backend API for the OCEAN-P Psychometric Personality Test",
    version="1.0.0",
    lifespan=lifespan,
)

# Frontend: templates Jinja2 + archivos estáticos
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).resolve().parent / "static"),
    name="static",
)
app.include_router(quiz.router, tags=["quiz"])
app.include_router(report.router, tags=["report"])
app.include_router(emotional_health.router, tags=["emotional-health"])
app.include_router(views.router, tags=["views"])


@app.get("/")
def read_root():
    return {
        "message": "Welcome to OCEAN-P Personality Test API",
        "status": "active"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database_configured": settings.DATABASE_URL.startswith("sqlite") or "postgres_configured",
    }
