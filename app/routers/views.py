"""
Views router — renderiza las páginas del flujo del usuario.

GET /
    → redirige a /quiz (landing)
GET /quiz
    → landing
GET /quiz/{session_id}/instructions
    → pantalla de instrucciones
GET /quiz/{session_id}
    → cuestionario
GET /report/{session_id}
    → informe (placeholder por ahora; T3 lo implementa completo)
"""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session as DBSession

from app.database import get_session
from app.models import TestSession

BASE_DIR = Path(__file__).resolve().parent.parent  # app/
TEMPLATES_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

ITEMS_PATH = BASE_DIR / "data" / "items.json"
_ITEMS_CACHE: list[dict] | None = None


def _load_items() -> list[dict]:
    global _ITEMS_CACHE
    if _ITEMS_CACHE is None:
        with open(ITEMS_PATH, encoding="utf-8") as f:
            _ITEMS_CACHE = json.load(f)["items"]
    return _ITEMS_CACHE or []


router = APIRouter()


@router.get("/")
def root_redirect():
    return RedirectResponse(url="/quiz", status_code=307)


@router.get("/quiz")
def landing(request: Request):
    return templates.TemplateResponse(request, "landing.html", {})


@router.get("/quiz/{session_id}/instructions")
def instructions(
    session_id: str,
    request: Request,
    db: DBSession = Depends(get_session),
):
    session = db.get(TestSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return templates.TemplateResponse(
        request, "instructions.html", {"session_id": session_id}
    )


@router.get("/quiz/{session_id}")
def quiz_page(
    session_id: str,
    request: Request,
    db: DBSession = Depends(get_session),
):
    session = db.get(TestSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return templates.TemplateResponse(
        request,
        "quiz.html",
        {"session_id": session_id, "items": _load_items()},
    )
