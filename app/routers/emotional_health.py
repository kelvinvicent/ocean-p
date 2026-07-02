"""
emotional_health router — todas las rutas del módulo de salud emocional.

Endpoints:
- GET   /emotional-health/                              → landing + disclaimer
- POST  /emotional-health/start                         → crea assessment (RS-4)
- GET   /emotional-health/quiz/{assessment_id}          → cuestionario
- POST  /emotional-health/answer                        → guarda respuesta(s)
- GET   /emotional-health/crisis                        → pantalla RS-2
- GET   /emotional-health/calculating/{assessment_id}   → loader
- POST  /emotional-health/score/{assessment_id}         → calcula
- GET   /emotional-health/report/{assessment_id}        → informe
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, conint
from sqlmodel import Session as DBSession, select

from app.database import get_session
from app.models import (
    CrisisResource,
    EmotionalAssessment,
    EmotionalResponse,
    EmotionalScore,
    TestSession,
)
from app.services.emotional_scoring_service import compute_and_save_scores

# El motor se importa para tener acceso a los bancos de ítems
import emotional_health_engine as ehe


BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter()


# ----------------------------------------------------------------------
# Definición de los 8 bloques (orden oficial)
# ----------------------------------------------------------------------

# Cada bloque: id, módulo del motor, número de ítems, escala, ventana temporal,
# etiqueta de validación clínica (RF-3.11) y texto del encabezado (RF-1.1).
BLOCKS = [
    {"id": 1, "module": "phq9",      "title": "Síntomas depresivos (PHQ-9)",
     "scale": "0-3_4opciones", "window": "Últimas 2 semanas", "items": 9, "is_clinical": True,
     "instructions": "Durante las últimas 2 semanas, ¿con qué frecuencia te han molestado los siguientes problemas?"},
    {"id": 2, "module": "who5",      "title": "Bienestar general (WHO-5)",
     "scale": "0-5_6opciones", "window": "Últimas 2 semanas", "items": 5, "is_clinical": True,
     "instructions": "Durante las últimas 2 semanas, indica con qué frecuencia te has sentido así."},
    {"id": 3, "module": "phq15",     "title": "Síntomas somáticos (PHQ-15)",
     "scale": "0-2_3opciones", "window": "Últimas 4 semanas", "items": 15, "is_clinical": True,
     "instructions": "Durante las últimas 4 semanas, ¿cuánto te ha molestado cada uno de estos síntomas?"},
    {"id": 4, "module": "cognitive_checklist",  "title": "Funciones cognitivas",
     "scale": "yes_no", "window": "Últimas semanas", "items": 8, "is_clinical": False,
     "instructions": "Marca las señales que hayas notado en las últimas semanas (no es una escala clínica)."},
    {"id": 5, "module": "behavioral_checklist", "title": "Comportamiento",
     "scale": "yes_no", "window": "Últimas semanas", "items": 8, "is_clinical": False,
     "instructions": "Marca los cambios que hayas notado en las últimas semanas (no es una escala clínica)."},
    {"id": 6, "module": "gad7",      "title": "Ansiedad (GAD-7)",
     "scale": "0-3_4opciones", "window": "Últimas 2 semanas", "items": 7, "is_clinical": True,
     "instructions": "Durante las últimas 2 semanas, ¿con qué frecuencia te han molestado los siguientes problemas?"},
    {"id": 7, "module": "irritability_checklist", "title": "Irritabilidad",
     "scale": "yes_no", "window": "Últimas semanas", "items": 4, "is_clinical": False,
     "instructions": "Marca las situaciones que hayas notado en las últimas semanas (no es una escala clínica)."},
    {"id": 8, "module": "rosenberg", "title": "Autoestima (Rosenberg)",
     "scale": "0-3_4opciones", "window": "—", "items": 10, "is_clinical": True,
     "instructions": "Indica tu grado de acuerdo con cada afirmación sobre cómo te ves a ti mismo/a."},
    {"id": 9, "module": "sleep",     "title": "Calidad de sueño",
     "scale": "0-3_4opciones", "window": "Últimas 2 semanas", "items": 4, "is_clinical": False,
     "instructions": "Sobre tu sueño en las últimas 2 semanas (estimación no clínica)."},
    {"id": 10,"module": "context",   "title": "Contexto de vida",
     "scale": "context", "window": "—", "items": 7, "is_clinical": False,
     "instructions": "Información cualitativa sobre tu situación actual. No se puntúa."},
]


def _items_for_block(block: dict) -> dict[int, str]:
    """Devuelve el banco de ítems real (1-id) para un bloque."""
    if block["module"] == "phq9":      return ehe.PHQ9_ITEMS
    if block["module"] == "who5":      return ehe.WHO5_ITEMS
    if block["module"] == "phq15":     return ehe.PHQ15_ITEMS
    if block["module"] == "gad7":      return ehe.GAD7_ITEMS
    if block["module"] == "rosenberg": return ehe.ROSENBERG_ITEMS
    if block["module"] == "sleep":     return ehe.SLEEP_ITEMS
    if block["module"] == "cognitive_checklist":    return ehe.COGNITIVE_CHECKLIST_ITEMS
    if block["module"] == "behavioral_checklist":   return ehe.BEHAVIORAL_CHECKLIST_ITEMS
    if block["module"] == "irritability_checklist": return ehe.IRRITABILITY_CHECKLIST_ITEMS
    if block["module"] == "context":
        return {i + 1: f"{k}: {opts[0]}" for i, (k, opts) in enumerate(ehe.CONTEXT_ITEMS.items())}
    return {}


def _context_options() -> dict[str, list[str]]:
    return ehe.CONTEXT_ITEMS


# ----------------------------------------------------------------------
# Schemas
# ----------------------------------------------------------------------

class StartPayload(BaseModel):
    session_id: str
    disclaimer_accepted: bool
    is_female: bool = True
    country_code: str = "ES"


class AnswerPayload(BaseModel):
    assessment_id: int
    module: str
    item_id: int
    raw_value: int = Field(ge=0, le=5)
    response_time_ms: Optional[int] = None


class AnswerAck(BaseModel):
    assessment_id: int
    module: str
    item_id: int
    crisis_alert_triggered: bool = False  # RS-2: front redirige si True
    next_block: int


# ----------------------------------------------------------------------
# Landing + start
# ----------------------------------------------------------------------

@router.get("/emotional-health/")
def eh_landing(request: Request):
    return templates.TemplateResponse(request, "eh_landing.html", {})


@router.post("/emotional-health/start", response_model=dict)
def eh_start(payload: StartPayload, db: DBSession = Depends(get_session)):
    # RS-4: disclaimer_accepted obligatorio
    if not payload.disclaimer_accepted:
        raise HTTPException(
            status_code=422,
            detail="Debes aceptar el disclaimer para comenzar (RS-4).",
        )
    session = db.get(TestSession, payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    assessment = EmotionalAssessment(
        session_id=payload.session_id,
        disclaimer_accepted=True,
        is_female=payload.is_female,
        country_code=payload.country_code,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return {
        "assessment_id": assessment.id,
        "session_id": payload.session_id,
    }


# ----------------------------------------------------------------------
# Quiz (vista)
# ----------------------------------------------------------------------

@router.get("/emotional-health/quiz/{assessment_id}")
def eh_quiz_view(
    assessment_id: int,
    request: Request,
    block: int = 1,
    db: DBSession = Depends(get_session),
):
    assessment = db.get(EmotionalAssessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if block < 1 or block > len(BLOCKS):
        raise HTTPException(status_code=400, detail="Bloque inválido")

    block_def = BLOCKS[block - 1]
    items = _items_for_block(block_def)

    # Si el bloque es contexto, pasamos también las opciones
    context_options = _context_options() if block_def["module"] == "context" else {}

    return templates.TemplateResponse(
        request,
        "eh_quiz.html",
        {
            "assessment_id": assessment_id,
            "block": block,
            "block_def": block_def,
            "items": items,
            "context_options": context_options,
            "total_blocks": len(BLOCKS),
        },
    )


# ----------------------------------------------------------------------
# Answer endpoint (RS-1 + RS-2 críticos aquí)
# ----------------------------------------------------------------------

@router.post("/emotional-health/answer", response_model=AnswerAck)
def eh_answer(payload: AnswerPayload, db: DBSession = Depends(get_session)):
    assessment = db.get(EmotionalAssessment, payload.assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Upsert: si el item ya estaba respondido, se actualiza
    existing = db.exec(
        select(EmotionalResponse)
        .where(EmotionalResponse.assessment_id == payload.assessment_id)
        .where(EmotionalResponse.module == payload.module)
        .where(EmotionalResponse.item_id == payload.item_id)
    ).first()
    is_scored = payload.module not in (
        "cognitive_checklist", "behavioral_checklist", "irritability_checklist", "context"
    )
    if existing:
        existing.raw_value = payload.raw_value
        existing.response_time_ms = payload.response_time_ms
    else:
        db.add(EmotionalResponse(
            assessment_id=payload.assessment_id,
            module=payload.module,
            item_id=payload.item_id,
            raw_value=payload.raw_value,
            is_scored=is_scored,
        ))

    # RS-1: detección de crisis aislada del total — el ítem 9 del PHQ-9 > 0
    # marca la alerta INMEDIATAMENTE, sin esperar al cálculo final.
    crisis_triggered = False
    if payload.module == "phq9" and payload.item_id == 9 and payload.raw_value > 0:
        if not assessment.crisis_alert:
            assessment.crisis_alert = True
            crisis_triggered = True

    db.commit()
    db.refresh(assessment)

    # Determinar bloque actual
    block_idx = next(
        (i + 1 for i, b in enumerate(BLOCKS) if b["module"] == payload.module),
        len(BLOCKS),
    )

    return AnswerAck(
        assessment_id=payload.assessment_id,
        module=payload.module,
        item_id=payload.item_id,
        crisis_alert_triggered=crisis_triggered,
        next_block=block_idx,
    )


# ----------------------------------------------------------------------
# Crisis screen (RS-2) — siempre debe mostrar al menos 1 opción
# ----------------------------------------------------------------------

@router.get("/emotional-health/crisis")
def eh_crisis_view(
    request: Request,
    assessment_id: int,
    db: DBSession = Depends(get_session),
):
    assessment = db.get(EmotionalAssessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # RS-3: recursos desde BD, nunca hardcodeados
    resources = db.exec(
        select(CrisisResource)
        .where(CrisisResource.country_code == assessment.country_code)
        .where(CrisisResource.active == True)  # noqa: E712
    ).all()

    return templates.TemplateResponse(
        request,
        "eh_crisis.html",
        {
            "assessment_id": assessment_id,
            "resources": resources,
        },
    )


# ----------------------------------------------------------------------
# Calculating (loader) + score + report
# ----------------------------------------------------------------------

@router.get("/emotional-health/calculating/{assessment_id}")
def eh_calculating_view(
    assessment_id: int,
    request: Request,
    db: DBSession = Depends(get_session),
):
    assessment = db.get(EmotionalAssessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if assessment.completed_at is not None:
        return RedirectResponse(
            url=f"/emotional-health/report/{assessment_id}", status_code=302
        )
    return templates.TemplateResponse(
        request, "eh_calculating.html", {"assessment_id": assessment_id}
    )


@router.post("/emotional-health/score/{assessment_id}")
def eh_score(assessment_id: int, db: DBSession = Depends(get_session)):
    assessment = db.get(EmotionalAssessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if not assessment.disclaimer_accepted:
        raise HTTPException(status_code=422, detail="Disclaimer no aceptado")
    if assessment.completed_at is not None:
        raise HTTPException(status_code=409, detail="Assessment ya calculado")

    try:
        result = compute_and_save_scores(assessment_id, db)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return {
        "assessment_id": assessment_id,
        "crisis_alert": result["crisis_alert"],
        "professional_help_recommended": result["professional_help_recommended"],
    }


@router.get("/emotional-health/report/{assessment_id}")
def eh_report_view(
    assessment_id: int,
    request: Request,
    db: DBSession = Depends(get_session),
):
    assessment = db.get(EmotionalAssessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if assessment.completed_at is None:
        return RedirectResponse(
            url=f"/emotional-health/calculating/{assessment_id}", status_code=302
        )

    # Cargar scores
    scores = {
        s.module: s
        for s in db.exec(
            select(EmotionalScore).where(EmotionalScore.assessment_id == assessment_id)
        ).all()
    }

    # Cargar checklists
    checklist_rows = db.exec(
        select(EmotionalResponse)
        .where(EmotionalResponse.assessment_id == assessment_id)
        .where(EmotionalResponse.is_scored == False)  # noqa: E712
    ).all()
    checklists: dict[str, list[int]] = {}
    for r in checklist_rows:
        if r.module == "context":
            continue
        checklists.setdefault(r.module, []).append(r.item_id)

    # Si crisis_alert, traer recursos para el informe
    crisis_resources = []
    if assessment.crisis_alert:
        crisis_resources = db.exec(
            select(CrisisResource)
            .where(CrisisResource.country_code == assessment.country_code)
            .where(CrisisResource.active == True)  # noqa: E712
        ).all()

    return templates.TemplateResponse(
        request,
        "eh_report.html",
        {
            "assessment_id": assessment_id,
            "scores": scores,
            "checklists": checklists,
            "crisis_alert": assessment.crisis_alert,
            "professional_help_recommended": any(
                s.professional_help_recommended for s in scores.values()
            ),
            "crisis_resources": crisis_resources,
            "context_items": ehe.CONTEXT_ITEMS,
            "context_answers": _load_context_answers_for_report(assessment_id, db),
        },
    )


def _load_context_answers_for_report(assessment_id: int, db: DBSession) -> dict[int, int]:
    """Devuelve respuestas de contexto como {item_id: raw_value}."""
    rows = db.exec(
        select(EmotionalResponse)
        .where(EmotionalResponse.assessment_id == assessment_id)
        .where(EmotionalResponse.module == "context")
    ).all()
    return {r.item_id: r.raw_value for r in rows}


# ----------------------------------------------------------------------
# Crisis resources (helper: cargar plantilla con la lista activa)
# ----------------------------------------------------------------------

@router.get("/emotional-health/crisis-resources")
def list_crisis_resources(
    country_code: str = "ES",
    db: DBSession = Depends(get_session),
):
    resources = db.exec(
        select(CrisisResource)
        .where(CrisisResource.country_code == country_code)
        .where(CrisisResource.active == True)  # noqa: E712
    ).all()
    return [
        {
            "id": r.id,
            "name": r.resource_name,
            "contact": r.contact_info,
        }
        for r in resources
    ]


# ----------------------------------------------------------------------
