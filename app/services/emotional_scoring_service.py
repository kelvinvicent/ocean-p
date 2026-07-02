"""
emotional_scoring_service — adaptador entre el motor puro y la BD.

Responsabilidades:
- Cargar las respuestas de la BD y agruparlas por módulo.
- Llamar al motor `emotional_health_engine.score_assessment()`.
- Persistir los resultados en `emotional_scores` (instrumentos validados) y
  `emotional_checklist_selections` (checklists no clínicos).
- Marcar `crisis_alert` y `professional_help_recommended` en el assessment.

Reglas (no negociables):
- Nunca mezclar scores de módulos distintos.
- Los checklists no clínicos van a `emotional_checklist_selections`, NUNCA a
  `emotional_scores` (RF-2.4).
- `crisis_alert` se setea también a nivel de fila de `emotional_scores` del
  módulo phq9, para que la query del informe sea trivial.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session as DBSession, select

from app.models import (
    EmotionalAssessment,
    EmotionalChecklistSelection,
    EmotionalResponse,
    EmotionalScore,
)

# El motor se importa tal cual — NO se modifica.
import emotional_health_engine as ehe


# Módulos que sí se puntúan (cada uno con su escala documentada)
SCORED_MODULES = {
    "phq9":      "0-3_4opciones",
    "who5":      "0-5_6opciones",
    "phq15":     "0-2_3opciones",
    "gad7":      "0-3_4opciones",
    "rosenberg": "0-3_4opciones",
    "sleep":     "0-3_4opciones",
}

# Módulos que NO se puntúan: se procesan como lista de items marcados
CHECKLIST_MODULES = {
    "cognitive_checklist",
    "behavioral_checklist",
    "irritability_checklist",
}

# Módulo sin puntaje ni checklist: se guarda como opciones cualitativas
CONTEXT_MODULE = "context"


def _load_responses_by_module(assessment_id: int, db: DBSession) -> dict[str, dict[int, int]]:
    rows = db.exec(
        select(EmotionalResponse).where(EmotionalResponse.assessment_id == assessment_id)
    ).all()
    by_module: dict[str, dict[int, int]] = defaultdict(dict)
    for r in rows:
        by_module[r.module][r.item_id] = r.raw_value
    return by_module


def _load_context_answers(assessment_id: int, db: DBSession) -> dict[str, str]:
    """Las respuestas de contexto guardan item_id como índice sobre las claves
    de CONTEXT_ITEMS. Devolvemos un dict {clave_pregunta: respuesta}."""
    rows = db.exec(
        select(EmotionalResponse)
        .where(EmotionalResponse.assessment_id == assessment_id)
        .where(EmotionalResponse.module == CONTEXT_MODULE)
    ).all()
    context_keys = list(ehe.CONTEXT_ITEMS.keys())
    return {
        context_keys[r.item_id]: str(r.raw_value)
        for r in rows
        if r.item_id < len(context_keys)
    }


def _persist_score(
    db: DBSession, assessment_id: int, module: str, scale: str,
    total: float, band: str, is_validated: bool,
    crisis_alert: bool = False, professional_help: bool = False,
) -> None:
    db.add(EmotionalScore(
        assessment_id=assessment_id,
        module=module,
        response_scale=scale,
        total_score=total,
        severity_band=band,
        is_clinically_validated=is_validated,
        crisis_alert=crisis_alert,
        professional_help_recommended=professional_help,
    ))


def _persist_checklist(
    db: DBSession, assessment_id: int, module: str, selections: dict[int, int]
) -> None:
    """Los checklists son respuestas 0/1 (No/Sí) — solo guardamos los marcados."""
    for item_id, value in selections.items():
        db.add(EmotionalChecklistSelection(
            assessment_id=assessment_id,
            module=module,
            item_id=item_id,
            selected=bool(value),
        ))


def compute_and_save_scores(
    assessment_id: int, db: DBSession
) -> dict[str, Any]:
    """Carga respuestas, ejecuta el motor, persiste resultados, retorna resumen."""
    assessment = db.get(EmotionalAssessment, assessment_id)
    if assessment is None:
        raise ValueError(f"Assessment {assessment_id} not found")

    responses = _load_responses_by_module(assessment_id, db)

    # 1) Módulos puntuados — cada uno con su escala
    phq9 = responses.get("phq9", {})
    gad7 = responses.get("gad7", {})
    sleep = responses.get("sleep", {})
    who5 = responses.get("who5", {})
    phq15 = responses.get("phq15", {})
    rosenberg = responses.get("rosenberg", {})

    # El motor ya está validado con 9 casos. Si faltan respuestas para
    # un módulo, capturamos y devolvemos error claro (la API traducirá a 422).
    try:
        result = ehe.score_assessment(
            phq9_responses=phq9 or {i: 0 for i in ehe.PHQ9_ITEMS},
            gad7_responses=gad7 or {i: 0 for i in ehe.GAD7_ITEMS},
            sleep_responses=sleep or {i: 0 for i in ehe.SLEEP_ITEMS},
            who5_responses=who5 or {i: 0 for i in ehe.WHO5_ITEMS},
            phq15_responses=phq15 or {i: 0 for i in ehe.PHQ15_ITEMS},
            rosenberg_responses=rosenberg or {i: 0 for i in ehe.ROSENBERG_ITEMS},
            is_female=assessment.is_female,
            context_answers=_load_context_answers(assessment_id, db),
        )
    except ValueError as e:
        raise ValueError(f"Scoring failed: {e}") from e

    # 2) Persistir scores (uno por módulo — NUNCA combinados)
    if result.phq9:
        _persist_score(db, assessment_id, "phq9", "0-3_4opciones",
                       result.phq9.total_score, result.phq9.severity_band,
                       is_validated=True, crisis_alert=result.crisis_alert,
                       professional_help=result.professional_help_recommended)
    if result.who5:
        _persist_score(db, assessment_id, "who5", "0-5_6opciones",
                       result.who5.total_score, result.who5.severity_band,
                       is_validated=True)
    if result.phq15:
        _persist_score(db, assessment_id, "phq15", "0-2_3opciones",
                       result.phq15.total_score, result.phq15.severity_band,
                       is_validated=True)
    if result.gad7:
        _persist_score(db, assessment_id, "gad7", "0-3_4opciones",
                       result.gad7.total_score, result.gad7.severity_band,
                       is_validated=True,
                       professional_help=result.professional_help_recommended)
    if result.rosenberg:
        _persist_score(db, assessment_id, "rosenberg", "0-3_4opciones",
                       result.rosenberg.total_score, result.rosenberg.severity_band,
                       is_validated=True)
    if result.sleep:
        _persist_score(db, assessment_id, "sleep", "0-3_4opciones",
                       result.sleep.total_score, result.sleep.severity_band,
                       is_validated=False)  # Sueño es no-clínico

    # 3) Persistir checklists (sin puntaje)
    for module in CHECKLIST_MODULES:
        _persist_checklist(db, assessment_id, module, responses.get(module, {}))

    # 4) Actualizar assessment
    assessment.crisis_alert = result.crisis_alert
    assessment.completed_at = datetime.now(timezone.utc)
    db.add(assessment)
    db.commit()

    return {
        "assessment_id": assessment_id,
        "crisis_alert": result.crisis_alert,
        "professional_help_recommended": result.professional_help_recommended,
        "phq9": _serialize(result.phq9) if result.phq9 else None,
        "who5": _serialize(result.who5) if result.who5 else None,
        "phq15": _serialize(result.phq15) if result.phq15 else None,
        "gad7": _serialize(result.gad7) if result.gad7 else None,
        "rosenberg": _serialize(result.rosenberg) if result.rosenberg else None,
        "sleep": _serialize(result.sleep) if result.sleep else None,
        "checklists": {
            module: list(responses.get(module, {}).keys())
            for module in CHECKLIST_MODULES
        },
        "context": _load_context_answers(assessment_id, db),
    }


def _serialize(s: ehe.ScaleResult) -> dict:
    return {
        "total_score": s.total_score,
        "severity_band": s.severity_band,
        "is_clinically_validated": s.is_clinically_validated,
    }
