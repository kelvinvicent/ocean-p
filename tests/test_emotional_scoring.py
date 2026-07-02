"""
Tests de scoring del módulo de salud emocional (RF-2.x).
"""

import pytest
from sqlmodel import Session, select

from app.models import (
    EmotionalAssessment,
    EmotionalChecklistSelection,
    EmotionalResponse,
    EmotionalScore,
)

import emotional_health_engine as ehe
from app.services.emotional_scoring_service import (
    CHECKLIST_MODULES,
    SCORED_MODULES,
    compute_and_save_scores,
)


# ----------------------------------------------------------------------
# Tests del motor (replican los casos A-I ya validados en runtime)
# ----------------------------------------------------------------------

def test_motor_phq9_alerta_aun_con_total_bajo():
    """Caso C del motor — el más importante."""
    phq9 = {i: 0 for i in ehe.PHQ9_ITEMS}
    phq9[9] = 1
    result, crisis, _ = ehe.score_phq9(phq9)
    assert result.severity_band == "minima_o_ninguna"
    assert crisis is True


def test_motor_phq9_sin_alerta_con_severidad_alta_sin_item_9():
    """Caso B — severidad alta sin ideación."""
    phq9 = {i: 3 for i in ehe.PHQ9_ITEMS}
    phq9[9] = 0
    result, crisis, _ = ehe.score_phq9(phq9)
    assert result.severity_band == "severa"
    assert crisis is False


def test_motor_phq15_excluye_item_15_en_hombres():
    phq15 = {i: 1 for i in ehe.PHQ15_ITEMS}
    r = ehe.score_phq15(phq15, is_female=False)
    assert r.total_score == 14.0


def test_motor_phq15_incluye_item_15_en_mujeres():
    phq15 = {i: 1 for i in ehe.PHQ15_ITEMS}
    r = ehe.score_phq15(phq15, is_female=True)
    assert r.total_score == 15.0


def test_motor_who5_bienestar_maximo_es_100():
    r = ehe.score_who5({i: 5 for i in ehe.WHO5_ITEMS})
    assert r.total_score == 100.0
    assert r.severity_band == "bienestar_adecuado"


def test_motor_rosenberg_inversion_items_negativos():
    """Caso G — autoestima alta."""
    rosenberg = {i: 3 for i in ehe.ROSENBERG_ITEMS}
    for ri in ehe.ROSENBERG_REVERSE_ITEMS:
        rosenberg[ri] = 0
    r = ehe.score_rosenberg(rosenberg)
    assert r.total_score == 30.0
    assert r.severity_band == "rango_normal"


# ----------------------------------------------------------------------
# Tests del adaptador (RF-2.2: módulos nunca combinados, RF-2.4: checklists sin puntaje)
# ----------------------------------------------------------------------

@pytest.fixture
def assessment_with_all_zeros(engine):
    """Inserta un assessment + respuestas de todos los módulos en valor 0."""
    with Session(engine) as db:
        a = EmotionalAssessment(
            session_id="dummy-uuid-test",
            disclaimer_accepted=True,
            is_female=True,
        )
        db.add(a)
        db.commit()
        db.refresh(a)
        aid = a.id

        for module, n_items in [
            ("phq9", 9), ("who5", 5), ("phq15", 15), ("gad7", 7),
            ("rosenberg", 10), ("sleep", 4),
            ("cognitive_checklist", 8), ("behavioral_checklist", 8),
            ("irritability_checklist", 4), ("context", 7),
        ]:
            for i in range(1, n_items + 1):
                db.add(EmotionalResponse(
                    assessment_id=aid, module=module, item_id=i, raw_value=0,
                    is_scored=module not in (
                        "cognitive_checklist", "behavioral_checklist",
                        "irritability_checklist", "context"
                    ),
                ))
        db.commit()
        return aid


def test_RF_2_2_modulos_puntuados_crean_fila_separada(engine, assessment_with_all_zeros):
    aid = assessment_with_all_zeros
    with Session(engine) as db:
        compute_and_save_scores(aid, db)

    with Session(engine) as db:
        scores = db.exec(
            select(EmotionalScore).where(EmotionalScore.assessment_id == aid)
        ).all()
        modules = {s.module for s in scores}
        expected = set(SCORED_MODULES.keys())
        assert len(scores) == 6
        assert modules == expected


def test_RF_2_4_checklists_no_generan_fila_en_emotional_scores(engine, assessment_with_all_zeros):
    aid = assessment_with_all_zeros
    with Session(engine) as db:
        compute_and_save_scores(aid, db)

    with Session(engine) as db:
        scores = db.exec(
            select(EmotionalScore).where(EmotionalScore.assessment_id == aid)
        ).all()
        score_modules = {s.module for s in scores}
        for cl in CHECKLIST_MODULES:
            assert cl not in score_modules, f"{cl} no debería estar en emotional_scores"
        assert "context" not in score_modules


def test_checklists_persistidos_en_tabla_separada(engine, assessment_with_all_zeros):
    aid = assessment_with_all_zeros
    with Session(engine) as db:
        compute_and_save_scores(aid, db)

    with Session(engine) as db:
        selections = db.exec(
            select(EmotionalChecklistSelection).where(
                EmotionalChecklistSelection.assessment_id == aid
            )
        ).all()
        modules = {s.module for s in selections}
        assert "cognitive_checklist" in modules
        assert "behavioral_checklist" in modules
        assert "irritability_checklist" in modules


def test_RF_2_3_bandas_de_severidad_publicadas(engine, assessment_with_all_zeros):
    aid = assessment_with_all_zeros
    with Session(engine) as db:
        compute_and_save_scores(aid, db)
    with Session(engine) as db:
        phq9 = db.exec(
            select(EmotionalScore).where(
                EmotionalScore.assessment_id == aid,
                EmotionalScore.module == "phq9",
            )
        ).first()
        assert phq9 is not None
        assert phq9.severity_band == "minima_o_ninguna"
        assert phq9.is_clinically_validated is True


def test_sleep_es_no_clinico(engine, assessment_with_all_zeros):
    aid = assessment_with_all_zeros
    with Session(engine) as db:
        compute_and_save_scores(aid, db)
    with Session(engine) as db:
        sleep = db.exec(
            select(EmotionalScore).where(
                EmotionalScore.assessment_id == aid,
                EmotionalScore.module == "sleep",
            )
        ).first()
        assert sleep is not None
        assert sleep.is_clinically_validated is False


def test_cada_modulo_puntuado_tiene_response_scale(engine, assessment_with_all_zeros):
    aid = assessment_with_all_zeros
    with Session(engine) as db:
        compute_and_save_scores(aid, db)
    with Session(engine) as db:
        scores = db.exec(
            select(EmotionalScore).where(EmotionalScore.assessment_id == aid)
        ).all()
        for s in scores:
            assert s.response_scale in SCORED_MODULES.values(), s.module
