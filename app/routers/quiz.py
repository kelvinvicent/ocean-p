"""
Quiz router — gestión de sesiones y respuestas del test OCEAN-P.

Endpoints:
- POST   /sessions                       → crear nueva sesión (T1.4)
- POST   /sessions/{id}/responses        → guardar respuesta (T1.5)
- GET    /sessions/{id}/state            → restaurar progreso (T1.6)
- POST   /sessions/{id}/submit           → calcular perfil (T2.3)
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, conint
from sqlmodel import Session as DBSession, select

from app.database import get_session
from app.models import ItemResponse, TestSession
from app.services.scoring_service import score_session


router = APIRouter()


# ----------------------------------------------------------------------
# Schemas de request/response
# ----------------------------------------------------------------------

class SessionCreated(BaseModel):
    session_id: str
    started_at: datetime


class ResponseInput(BaseModel):
    item_id: int = Field(ge=1, le=65)
    raw_value: int = Field(ge=1, le=5)
    response_time_ms: Optional[int] = Field(default=None, ge=0)


class ResponseAck(BaseModel):
    session_id: str
    item_id: int
    total_answered: int


class StateResponse(BaseModel):
    session_id: str
    status: str
    answered: dict[str, int]  # JSON: claves como string (1-65)
    total_answered: int
    total_items: int = 65


# ----------------------------------------------------------------------
# T1.4 — Crear nueva sesión
# ----------------------------------------------------------------------

@router.post("/sessions", response_model=SessionCreated, status_code=status.HTTP_201_CREATED)
def create_session(db: DBSession = Depends(get_session)):
    session = TestSession()
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionCreated(session_id=session.id, started_at=session.started_at)


# ----------------------------------------------------------------------
# T1.5 — Guardar una respuesta individual
# ----------------------------------------------------------------------

@router.post(
    "/sessions/{session_id}/responses",
    response_model=ResponseAck,
    status_code=status.HTTP_201_CREATED,
)
def save_response(
    session_id: str,
    payload: ResponseInput,
    db: DBSession = Depends(get_session),
):
    session = db.get(TestSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "in_progress":
        raise HTTPException(
            status_code=409,
            detail=f"Session is {session.status}, cannot accept responses",
        )

    # Upsert: si el ítem ya estaba respondido, se actualiza (permite "Atrás"
    # del frontend para corregir)
    existing = db.exec(
        select(ItemResponse)
        .where(ItemResponse.session_id == session_id)
        .where(ItemResponse.item_id == payload.item_id)
    ).first()
    if existing:
        existing.raw_value = payload.raw_value
        existing.response_time_ms = payload.response_time_ms
    else:
        db.add(ItemResponse(
            session_id=session_id,
            item_id=payload.item_id,
            raw_value=payload.raw_value,
            response_time_ms=payload.response_time_ms,
        ))

    db.commit()

    total = len(db.exec(
        select(ItemResponse).where(ItemResponse.session_id == session_id)
    ).all())

    return ResponseAck(
        session_id=session_id,
        item_id=payload.item_id,
        total_answered=total,
    )


# ----------------------------------------------------------------------
# T1.6 — Restaurar progreso
# ----------------------------------------------------------------------

@router.get("/sessions/{session_id}/state", response_model=StateResponse)
def get_state(session_id: str, db: DBSession = Depends(get_session)):
    session = db.get(TestSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    rows = db.exec(
        select(ItemResponse).where(ItemResponse.session_id == session_id)
    ).all()
    answered = {str(r.item_id): r.raw_value for r in rows}

    return StateResponse(
        session_id=session_id,
        status=session.status,
        answered=answered,
        total_answered=len(answered),
    )


# ----------------------------------------------------------------------
# T2.3 — Calcular perfil (disparado por el frontend al completar los 65 ítems)
# ----------------------------------------------------------------------

class SubmitResult(BaseModel):
    session_id: str
    report_id: str
    status: str
    is_conclusive: bool
    archetype_label: str


@router.post("/sessions/{session_id}/submit", response_model=SubmitResult)
def submit_session(session_id: str, db: DBSession = Depends(get_session)):
    session = db.get(TestSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status == "completed" or session.status == "invalid":
        raise HTTPException(
            status_code=409, detail=f"Session already {session.status}"
        )

    total = len(db.exec(
        select(ItemResponse).where(ItemResponse.session_id == session_id)
    ).all())
    if total < 65:
        raise HTTPException(
            status_code=422,
            detail=f"Solo {total}/65 respuestas. Completa todos los ítems.",
        )

    result = score_session(session_id, db)
    return SubmitResult(
        session_id=session_id,
        report_id=result["report_id"],
        status=result["status"],
        is_conclusive=result["is_conclusive"],
        archetype_label=result["archetype_label"],
    )
