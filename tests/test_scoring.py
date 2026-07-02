"""
Tests del motor de scoring puro (sin BD) y del orquestador (con BD en memoria).
5 casos de prueba manuales (T2.5):
  A. Todas las respuestas = 3 → perfil neutro (50 percentil, sin alertas).
  B. Directos=5, inversos=1 (perfil "alto en todo") → percentil 100.
  C. Inversión de ítems R verificada matemáticamente.
  D. Validez baja (deseabilidad + atención) → ≥2 alertas → is_conclusive=False.
  E. Validez alta → 0 alertas → is_conclusive=True.
"""

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import ItemResponse, Report, Score, TestSession
from app.services.scoring_engine import (
    REVERSE_ITEMS,
    _invert,
    compute_dimension_scores,
    compute_facet_scores,
    compute_validity,
    score_test,
)
from app.services.scoring_service import score_session


def _build(default: int, overrides: dict[int, int] | None = None) -> dict[int, int]:
    responses = {i: default for i in range(1, 66)}
    if overrides:
        responses.update(overrides)
    return responses


# ----------------------------------------------------------------------
# Caso A — perfil neutro
# ----------------------------------------------------------------------

def test_caso_a_perfil_neutro():
    r = score_test(_build(3))
    assert all(v == 3.0 for v in r.dimension_scores.values()), r.dimension_scores
    assert all(v == 3.0 for v in r.facet_scores.values()), r.facet_scores
    assert r.percentiles["apertura"] == 50.0
    assert r.alerts == []
    assert r.is_conclusive is True


# ----------------------------------------------------------------------
# Caso B — "alto en todo" (directos=5, inversos=1)
# ----------------------------------------------------------------------

def test_caso_b_perfil_alto_consistente():
    overrides = {item: 1 for item in REVERSE_ITEMS}
    # Coherencia con items 64 y 65 (consistencia con 26 y 28)
    overrides[64] = 5
    overrides[65] = 1  # 65 es inverso conceptual de 28
    # Ítems de validez: respuestas realistas (no "5" → no dispara alertas)
    overrides[61] = 1
    overrides[62] = 1
    overrides[63] = 1
    r = score_test(_build(5, overrides))
    assert all(v == 5.0 for v in r.facet_scores.values()), r.facet_scores
    assert all(v == 5.0 for v in r.dimension_scores.values()), r.dimension_scores
    assert r.percentiles["responsabilidad"] == 100.0
    assert r.percentiles["amabilidad"] == 100.0
    assert r.alerts == []


# ----------------------------------------------------------------------
# Caso C — verificación matemática de inversión
# ----------------------------------------------------------------------

def test_caso_c_inversion_items_R():
    # ítem 4 (R) = 5 → invertido = 1; resto = 3
    r = score_test(_build(3, overrides={4: 5}))
    # curiosidad_intelectual = (3+3+3+1)/4 = 2.5
    assert r.facet_scores["curiosidad_intelectual"] == 2.5
    # Otras facetas no afectadas
    assert r.facet_scores["creatividad"] == 3.0


def test_inversion_1_a_5_y_5_a_1():
    assert _invert(1) == 5
    assert _invert(2) == 4
    assert _invert(3) == 3
    assert _invert(4) == 2
    assert _invert(5) == 1


# ----------------------------------------------------------------------
# Caso D — validez baja (deseabilidad + atención)
# ----------------------------------------------------------------------

def test_caso_d_validez_baja_dos_alertas():
    r = score_test(_build(3, overrides={61: 5, 62: 5, 63: 4}))
    assert "deseabilidad_social_alta" in r.alerts
    assert "posible_respuesta_automatica" in r.alerts
    assert r.is_conclusive is False


# ----------------------------------------------------------------------
# Caso E — validez alta (sin alertas)
# ----------------------------------------------------------------------

def test_caso_e_validez_alta_perfil_coherente():
    # Perfil moderado, sin deseo de "quedar bien", atención correcta
    r = score_test(_build(3, overrides={61: 2, 62: 2, 63: 1}))
    assert r.alerts == []
    assert r.is_conclusive is True


def test_caso_d_inconsistencia_detectada():
    # Ítem 26 = 5, ítem 64 = 1 → diferencia = 4 → alerta
    r = score_test(_build(3, overrides={26: 5, 64: 1}))
    assert "inconsistencia_detectada" in r.alerts


# ----------------------------------------------------------------------
# Validación de errores
# ----------------------------------------------------------------------

def test_faltan_respuestas_lanza_error():
    incomplete = {i: 3 for i in range(1, 65)}  # solo 64 ítems
    with pytest.raises(ValueError, match="Faltan respuestas"):
        score_test(incomplete)


def test_valor_fuera_de_rango_lanza_error():
    bad = _build(3, overrides={10: 6})
    with pytest.raises(ValueError, match="fuera de rango"):
        score_test(bad)


# ----------------------------------------------------------------------
# Estructura: 15 facetas, 5 dimensiones, 4 índices, 3 escalas validez
# ----------------------------------------------------------------------

def test_estructura_completa_del_resultado():
    r = score_test(_build(3))
    assert len(r.facet_scores) == 15
    assert len(r.dimension_scores) == 5
    assert len(r.composite_scores) == 4
    assert len(r.validity) == 3


# ----------------------------------------------------------------------
# Tests del orquestador (BD en memoria SQLite)
# ----------------------------------------------------------------------

@pytest.fixture
def in_memory_db():
    """Engine SQLite en memoria + tablas creadas. Una sesión por test."""
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_orquestador_persiste_27_filas_de_scores(in_memory_db):
    sess = TestSession()
    in_memory_db.add(sess)
    in_memory_db.commit()
    in_memory_db.refresh(sess)
    for item_id in range(1, 66):
        in_memory_db.add(ItemResponse(
            session_id=sess.id, item_id=item_id, raw_value=3, response_time_ms=1000
        ))
    in_memory_db.commit()

    result = score_session(sess.id, in_memory_db)

    scores = in_memory_db.exec(
        select(Score).where(Score.session_id == sess.id)
    ).all()
    # 15 facetas + 5 dimensiones + 4 índices + 3 validez = 27
    assert len(scores) == 27

    # Tipos correctos
    facet_count = sum(1 for s in scores if s.scope_type == "facet")
    dim_count = sum(1 for s in scores if s.scope_type == "dimension")
    idx_count = sum(1 for s in scores if s.scope_type == "composite_index")
    val_count = sum(1 for s in scores if s.scope_type == "validity")
    assert facet_count == 15
    assert dim_count == 5
    assert idx_count == 4
    assert val_count == 3

    # Percentiles solo en facetas, dim e índices (no en validez)
    for s in scores:
        if s.scope_type == "validity":
            assert s.percentile is None
        else:
            assert s.percentile is not None

    assert result["status"] == "completed"
    assert result["is_conclusive"] is True


def test_orquestador_marca_invalid_con_dos_alertas(in_memory_db):
    sess = TestSession()
    in_memory_db.add(sess)
    in_memory_db.commit()
    in_memory_db.refresh(sess)
    overrides = {61: 5, 62: 5, 63: 4}
    for item_id in range(1, 66):
        in_memory_db.add(ItemResponse(
            session_id=sess.id, item_id=item_id,
            raw_value=overrides.get(item_id, 3), response_time_ms=1000,
        ))
    in_memory_db.commit()

    result = score_session(sess.id, in_memory_db)

    assert result["is_conclusive"] is False
    assert result["status"] == "invalid"
    in_memory_db.refresh(sess)
    assert sess.status == "invalid"
    assert sess.completed_at is not None


def test_orquestador_crea_un_report(in_memory_db):
    sess = TestSession()
    in_memory_db.add(sess)
    in_memory_db.commit()
    in_memory_db.refresh(sess)
    for item_id in range(1, 66):
        in_memory_db.add(ItemResponse(
            session_id=sess.id, item_id=item_id, raw_value=3, response_time_ms=1000
        ))
    in_memory_db.commit()

    result = score_session(sess.id, in_memory_db)

    reports = in_memory_db.exec(
        select(Report).where(Report.session_id == sess.id)
    ).all()
    assert len(reports) == 1
    assert reports[0].id == result["report_id"]
    assert reports[0].archetype_label is not None


def test_orquestador_falla_si_sesion_no_existe(in_memory_db):
    with pytest.raises(ValueError, match="not found"):
        score_session("nonexistent-id", in_memory_db)
