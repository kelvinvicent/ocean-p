"""
Report router — endpoints del informe (vista HTML en Fase 1, PDF/email en Fase 2).

GET /report/{session_id}
    → renderiza report.html con todos los datos calculados.
GET /calculating/{session_id}
    → pantalla de carga con loader SVG, auto-redirect al informe cuando el
      cálculo termina.
"""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session as DBSession, select

from app.database import get_session
from app.models import Report, Score, TestSession
from app.services import interpretation_service

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter()


# ----------------------------------------------------------------------
# Carga de datos del informe desde BD
# ----------------------------------------------------------------------

DIMENSION_KEYS = [
    "apertura", "responsabilidad", "extraversion",
    "amabilidad", "estabilidad_emocional",
]
COMPOSITE_KEYS = [
    "liderazgo_potencial", "trabajo_equipo",
    "tolerancia_riesgo", "estilo_ejecucion",
]


def _load_scores_by_scope(
    db: DBSession, session_id: str, scope_type: str
) -> dict[str, Score]:
    rows = db.exec(
        select(Score)
        .where(Score.session_id == session_id)
        .where(Score.scope_type == scope_type)
    ).all()
    return {r.scope_key: r for r in rows}


def build_report_payload(session_id: str, db: DBSession) -> dict:
    """Arma el dict completo que consume report.html."""
    session = db.get(TestSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    report = db.exec(
        select(Report).where(Report.session_id == session_id)
    ).first()
    if report is None:
        raise HTTPException(
            status_code=409,
            detail="El test no se ha completado todavía",
        )

    facets = _load_scores_by_scope(db, session_id, "facet")
    dimensions = _load_scores_by_scope(db, session_id, "dimension")
    composites = _load_scores_by_scope(db, session_id, "composite_index")
    validity = _load_scores_by_scope(db, session_id, "validity")

    dim_blocks = []
    for key in DIMENSION_KEYS:
        s = dimensions.get(key)
        if not s:
            continue
        dim_blocks.append({
            "key": key,
            "raw": s.raw_score,
            "percentile": s.percentile or 0.0,
            "color": _dimension_color(key),
            "interpretation": interpretation_service.interpret_dimension(
                key, s.percentile or 0.0
            ),
        })

    facet_blocks = []
    for key, s in sorted(facets.items()):
        facet_blocks.append({
            "key": key,
            "raw": s.raw_score,
            "percentile": s.percentile or 0.0,
            "interpretation": interpretation_service.interpret_facet(
                key, s.percentile or 0.0
            ),
        })

    composite_blocks = []
    for key in COMPOSITE_KEYS:
        s = composites.get(key)
        if not s:
            continue
        composite_blocks.append({
            "key": key,
            "raw": s.raw_score,
            "percentile": s.percentile or 0.0,
            "interpretation": interpretation_service.interpret_composite(
                key, s.percentile or 0.0
            ),
        })

    # Validez
    validity_payload = {
        "alerts": [],
        "is_conclusive": session.status == "completed",
    }
    # Recuperamos alertas del raw_score de validity (guardamos alertas en
    # memoria solo durante el cálculo; las inferimos de los scores
    # disponibles a partir de los umbrales)
    deseabilidad = validity.get("deseabilidad_social")
    atencion = validity.get("atencion")
    inconsistencia = validity.get("inconsistencia_max")
    if deseabilidad and deseabilidad.raw_score >= 4.0:
        validity_payload["alerts"].append("deseabilidad_social_alta")
    if atencion and atencion.raw_score >= 4.0:
        validity_payload["alerts"].append("posible_respuesta_automatica")
    if inconsistencia and inconsistencia.raw_score > 2.0:
        validity_payload["alerts"].append("inconsistencia_detectada")

    # Top 2 fortalezas y 2 áreas de desarrollo (facetas con mayor y menor
    # percentil)
    sorted_facets = sorted(
        facet_blocks, key=lambda f: f["percentile"], reverse=True
    )
    top_strengths = sorted_facets[:2]
    growth_areas = sorted_facets[-2:][::-1]  # peor primero

    return {
        "session_id": session_id,
        "status": session.status,
        "is_conclusive": validity_payload["is_conclusive"],
        "alerts": validity_payload["alerts"],
        "archetype_label": report.archetype_label,
        "generated_at": report.generated_at,
        "completed_at": session.completed_at,
        "dimensions": dim_blocks,
        "facets": facet_blocks,
        "composites": composite_blocks,
        "top_strengths": top_strengths,
        "growth_areas": growth_areas,
    }


def _dimension_color(key: str) -> str:
    return {
        "apertura": "var(--color-accent-ocean)",
        "responsabilidad": "var(--color-accent-cons)",
        "extraversion": "var(--color-accent-extra)",
        "amabilidad": "var(--color-accent-agree)",
        "estabilidad_emocional": "var(--color-accent-neuro)",
    }.get(key, "var(--color-accent-ocean)")


# ----------------------------------------------------------------------
# Endpoints
# ----------------------------------------------------------------------

@router.get("/report/{session_id}")
def report_view(
    session_id: str,
    request: Request,
    db: DBSession = Depends(get_session),
):
    payload = build_report_payload(session_id, db)
    return templates.TemplateResponse(
        request, "report.html", payload
    )


@router.get("/calculating/{session_id}")
def calculating_view(
    session_id: str,
    request: Request,
    db: DBSession = Depends(get_session),
):
    """Pantalla de carga: si el informe ya está listo, redirige al
    /report/{session_id}; si no, muestra el loader con auto-refresh."""
    session = db.get(TestSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status in ("completed", "invalid"):
        return RedirectResponse(
            url=f"/report/{session_id}", status_code=302
        )
    return templates.TemplateResponse(
        request, "calculating.html", {"session_id": session_id}
    )


# ----------------------------------------------------------------------
