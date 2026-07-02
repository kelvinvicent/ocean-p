"""
scoring_service — orquestador que conecta el motor puro con la BD.

Responsabilidades:
- Cargar las 65 respuestas de una `TestSession` desde la BD.
- Ejecutar el motor de scoring (cálculos puros, sin I/O).
- Aplicar la conversión a percentil.
- Derivar el arquetipo dimensional.
- Persistir en `scores` y `reports`.
- Actualizar el `status` de la sesión (`completed` o `invalid`).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select, col

from app.models import ItemResponse, Report, Score, TestSession
from app.services import norm_service
from app.services.archetype_service import derive_archetype

# Importación deliberadamente larga para mantener el motor como única fuente
# de verdad sobre la clave de corrección (DRY).
from app.services import scoring_engine


def _load_responses_dict(session_id: str, db: Session) -> dict[int, int]:
    responses = db.exec(
        select(ItemResponse).where(ItemResponse.session_id == session_id)
    ).all()
    return {r.item_id: r.raw_value for r in responses}


def _persist_score(
    db: Session, session_id: str, scope_type: str, scope_key: str,
    raw_score: float, percentile: Optional[float],
) -> None:
    db.add(Score(
        session_id=session_id,
        scope_type=scope_type,
        scope_key=scope_key,
        raw_score=raw_score,
        percentile=percentile,
    ))


def score_session(session_id: str, db: Session) -> dict:
    """Calcula facetas, dimensiones, índices y validez para una sesión.
    Persiste todo en BD y devuelve un dict con el resumen del resultado."""
    session = db.get(TestSession, session_id)
    if session is None:
        raise ValueError(f"Session {session_id} not found")

    responses = _load_responses_dict(session_id, db)
    result = scoring_engine.score_test(responses)

    # Persistir facetas + percentiles
    for facet_key, raw in result.facet_scores.items():
        _persist_score(
            db, session_id, "facet", facet_key, raw,
            norm_service.raw_to_percentile(facet_key, raw),
        )

    # Persistir dimensiones + percentiles
    for dim_key, raw in result.dimension_scores.items():
        _persist_score(
            db, session_id, "dimension", dim_key, raw,
            norm_service.raw_to_percentile(dim_key, raw),
        )

    # Persistir índices compuestos + percentiles
    for idx_key, raw in result.composite_scores.items():
        _persist_score(
            db, session_id, "composite_index", idx_key, raw,
            norm_service.raw_to_percentile(idx_key, raw),
        )

    # Persistir validez (sin percentil — son escalas técnicas)
    for v_key, raw in result.validity.items():
        _persist_score(db, session_id, "validity", v_key, float(raw), None)

    # Arquetipo (usa los percentiles de dimensión)
    dim_percentiles = {
        dk: norm_service.raw_to_percentile(dk, dv)
        for dk, dv in result.dimension_scores.items()
    }
    archetype_label, archetype_description = derive_archetype(dim_percentiles)

    # Actualizar sesión + crear report
    session.status = "completed" if result.is_conclusive else "invalid"
    session.completed_at = datetime.now(timezone.utc)
    session.avg_response_time_ms = _calc_avg_response_time(session_id, db)

    report = Report(
        session_id=session_id,
        archetype_label=archetype_label,
    )
    db.add(report)
    db.add(session)
    db.commit()
    db.refresh(report)

    return {
        "session_id": session_id,
        "report_id": report.id,
        "status": session.status,
        "is_conclusive": result.is_conclusive,
        "archetype_label": archetype_label,
        "archetype_description": archetype_description,
        "facet_scores": result.facet_scores,
        "dimension_scores": result.dimension_scores,
        "composite_scores": result.composite_scores,
        "validity": result.validity,
        "alerts": result.alerts,
    }


def _calc_avg_response_time(session_id: str, db: Session) -> Optional[int]:
    rows = db.exec(
        select(ItemResponse.response_time_ms)
        .where(ItemResponse.session_id == session_id)
        .where(col(ItemResponse.response_time_ms).is_not(None))
    ).all()
    if not rows:
        return None
    times = [t for t in rows if t is not None]
    return int(sum(times) / len(times)) if times else None
