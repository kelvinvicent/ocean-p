from fastapi import FastAPI
from app.config import settings

app = FastAPI(
    title="OCEAN-P Personality Test API",
    description="Backend API for the OCEAN-P Psychometric Personality Test",
    version="1.0.0"
)

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
        "database_configured": settings.DATABASE_URL.startswith("sqlite") or "postgres_configured"
    }
