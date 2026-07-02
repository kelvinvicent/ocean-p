"""
Tests de seguridad del módulo de salud emocional (RS-1 a RS-7).
Prioridad máxima — estos tests bloquean el deploy si fallan.
"""

import pytest
from sqlmodel import Session, select

from app.models import EmotionalAssessment


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------

@pytest.fixture
def started_assessment(client):
    """Crea un assessment aceptado (disclaimer=True) y devuelve su ID."""
    sid = client.post("/sessions").json()["session_id"]
    r = client.post("/emotional-health/start", json={
        "session_id": sid,
        "disclaimer_accepted": True,
        "is_female": True,
    })
    return r.json()["assessment_id"]


def _answer_all_except_phq9_item9(client, aid: int, phq9_value_9: int = 0) -> None:
    """Llena todos los módulos con valor 0 (o el valor que se pida para el ítem 9)."""
    modules = {
        "phq9": [(i, phq9_value_9) for i in range(1, 10)],
        "who5": [(i, 0) for i in range(1, 6)],
        "phq15": [(i, 0) for i in range(1, 16)],
        "gad7": [(i, 0) for i in range(1, 8)],
        "rosenberg": [(i, 0) for i in range(1, 11)],
        "sleep": [(i, 0) for i in range(1, 5)],
        "cognitive_checklist": [(i, 0) for i in range(1, 9)],
        "behavioral_checklist": [(i, 0) for i in range(1, 9)],
        "irritability_checklist": [(i, 0) for i in range(1, 5)],
        "context": [(i, 0) for i in range(7)],
    }
    for module, items in modules.items():
        for i, v in items:
            client.post("/emotional-health/answer", json={
                "assessment_id": aid, "module": module, "item_id": i, "raw_value": v,
            })


# ----------------------------------------------------------------------
# RS-4: Disclaimer obligatorio antes de empezar
# ----------------------------------------------------------------------

def test_RS4_start_sin_disclaimer_es_422(client):
    sid = client.post("/sessions").json()["session_id"]
    r = client.post("/emotional-health/start", json={
        "session_id": sid, "disclaimer_accepted": False,
    })
    assert r.status_code == 422


def test_RS4_start_con_disclaimer_aceptado_es_201(client):
    sid = client.post("/sessions").json()["session_id"]
    r = client.post("/emotional-health/start", json={
        "session_id": sid, "disclaimer_accepted": True,
    })
    assert r.status_code == 200
    assert r.json()["assessment_id"] > 0


def test_RS4_landing_no_premarca_checkbox(client):
    """El checkbox del disclaimer NO debe venir premarcado (RS-4)."""
    r = client.get("/emotional-health/")
    # El input checkbox existe pero NO tiene atributo 'checked'
    assert 'id="disclaimer-accepted"' in r.text
    assert 'id="disclaimer-accepted" checked' not in r.text
    assert 'id="disclaimer-accepted" checked=""' not in r.text


# ----------------------------------------------------------------------
# RS-1: Detección de crisis aislada del puntaje total
# ----------------------------------------------------------------------

def test_RS1_item_9_phq9_mayor_a_cero_activa_crisis_alert(client, engine, started_assessment):
    aid = started_assessment
    r = client.post("/emotional-health/answer", json={
        "assessment_id": aid, "module": "phq9", "item_id": 9, "raw_value": 1,
    })
    body = r.json()
    assert body["crisis_alert_triggered"] is True
    with Session(engine) as db:
        a = db.get(EmotionalAssessment, aid)
        assert a.crisis_alert is True


def test_RS1_item_9_phq9_en_cero_NO_activa_crisis(client, started_assessment):
    aid = started_assessment
    r = client.post("/emotional-health/answer", json={
        "assessment_id": aid, "module": "phq9", "item_id": 9, "raw_value": 0,
    })
    assert r.json()["crisis_alert_triggered"] is False


def test_RS1_item_9_de_otros_modulos_NO_activa_crisis(client, started_assessment):
    aid = started_assessment
    r = client.post("/emotional-health/answer", json={
        "assessment_id": aid, "module": "gad7", "item_id": 7, "raw_value": 3,
    })
    assert r.json()["crisis_alert_triggered"] is False


def test_RS1_persistencia_no_se_desactiva(client, engine, started_assessment):
    aid = started_assessment
    client.post("/emotional-health/answer", json={
        "assessment_id": aid, "module": "phq9", "item_id": 9, "raw_value": 2,
    })
    client.post("/emotional-health/answer", json={
        "assessment_id": aid, "module": "phq9", "item_id": 9, "raw_value": 0,
    })
    with Session(engine) as db:
        a = db.get(EmotionalAssessment, aid)
        assert a.crisis_alert is True


# ----------------------------------------------------------------------
# RS-2: Pantalla de crisis con recursos desde BD
# ----------------------------------------------------------------------

def test_RS2_crisis_screen_existe_y_carga_recursos(client, started_assessment):
    aid = started_assessment
    r = client.get(f"/emotional-health/crisis?assessment_id={aid}")
    assert r.status_code == 200
    # Tono cálido, no alarmista (RS-6)
    assert "Gracias por compartir esto" in r.text
    # Botón para continuar
    assert "Continuar con el cribado" in r.text
    # Disclaimer presente incluso en la pantalla de crisis
    assert "no es un diagnóstico" in r.text or "no constituye un diagnóstico" in r.text


def test_RS2_crisis_screen_sin_recursos_muestra_fallback(client, started_assessment):
    """Si no hay recursos en BD para el país, debe haber fallback genérico."""
    aid = started_assessment
    r = client.get(f"/emotional-health/crisis?assessment_id={aid}")
    # No hay crisis_resources cargados por defecto
    assert "línea de crisis" in r.text or "Recursos de ayuda" in r.text


def test_RS2_crisis_screen_404_si_assessment_no_existe(client):
    r = client.get("/emotional-health/crisis?assessment_id=999999")
    assert r.status_code == 404


# ----------------------------------------------------------------------
# RS-5: Recomendación de ayuda profesional en severidad alta
# ----------------------------------------------------------------------

def test_RS5_phq9_severo_recomienda_ayuda_profesional(client, started_assessment):
    aid = started_assessment
    # PHQ-9 = 24 (severo: 9 ítems x 3 = 27, 24 es alto)
    for i in range(1, 10):
        client.post("/emotional-health/answer", json={
            "assessment_id": aid, "module": "phq9", "item_id": i, "raw_value": 3 if i != 9 else 0,
        })
    # GAD-7 = 0 para que solo PHQ-9 dispare
    for i in range(1, 8):
        client.post("/emotional-health/answer", json={
            "assessment_id": aid, "module": "gad7", "item_id": i, "raw_value": 0,
        })
    for i in range(1, 5):
        client.post("/emotional-health/answer", json={
            "assessment_id": aid, "module": "sleep", "item_id": i, "raw_value": 0,
        })
    r = client.post(f"/emotional-health/score/{aid}")
    assert r.json()["professional_help_recommended"] is True


def test_RS5_phq9_leve_NO_recomienda_ayuda(client, started_assessment):
    aid = started_assessment
    for i in range(1, 10):
        client.post("/emotional-health/answer", json={
            "assessment_id": aid, "module": "phq9", "item_id": i, "raw_value": 1 if i != 9 else 0,
        })
    for i in range(1, 8):
        client.post("/emotional-health/answer", json={
            "assessment_id": aid, "module": "gad7", "item_id": i, "raw_value": 0,
        })
    for i in range(1, 5):
        client.post("/emotional-health/answer", json={
            "assessment_id": aid, "module": "sleep", "item_id": i, "raw_value": 0,
        })
    r = client.post(f"/emotional-health/score/{aid}")
    assert r.json()["professional_help_recommended"] is False


# ----------------------------------------------------------------------
# RS-6: Lenguaje no diagnóstico en los templates
# ----------------------------------------------------------------------

def test_RS6_landing_no_usa_lenguaje_diagnostico(client):
    r = client.get("/emotional-health/")
    body = r.text.lower()
    # Frases prohibidas
    assert "tienes depresión" not in body
    assert "estás diagnosticado" not in body
    assert "sufres de" not in body
    assert "padeces" not in body
    # Frases correctas
    assert "cribado de apoyo" in body
    assert "no constituye un diagnóstico" in body


def test_RS6_report_no_usa_lenguaje_diagnostico(client, started_assessment):
    aid = started_assessment
    _answer_all_except_phq9_item9(client, aid, phq9_value_9=0)
    client.post(f"/emotional-health/score/{aid}")
    r = client.get(f"/emotional-health/report/{aid}")
    body = r.text.lower()
    assert "tienes depresión" not in body
    assert "estás diagnosticado" not in body
    assert "sufres de" not in body
    # Frases compatibles con RS-6
    assert "sugieren síntomas compatibles" in body or "sugieren" in body


# ----------------------------------------------------------------------
# RS-7: Pendiente bloqueante (no testeable automáticamente)
# ----------------------------------------------------------------------

def test_bloque_context_renderiza_sin_error(client, started_assessment):
    """El bloque 10 (contexto) debe renderizar sin 500.

    Bug previo: el template usaba `context_options.values` (método)
    en vez de iterar por item_id.
    """
    aid = started_assessment
    # El bloque 10 es el de contexto (1-indexed en BLOCKS)
    r = client.get(f"/emotional-health/quiz/{aid}?block=10")
    assert r.status_code == 200
    # Las opciones del primer ítem (carga_laboral_academica) deben aparecer
    assert "Baja" in r.text
    assert "Manejable" in r.text
    assert "Alta" in r.text
    assert "Extrema" in r.text


# ----------------------------------------------------------------------

def test_RS7_recordatorio_en_codigo():
    """El código del motor contiene el recordatorio sobre la revisión profesional."""
    from pathlib import Path
    src = Path("emotional_health_engine.py").read_text(encoding="utf-8")
    assert "profesional" in src.lower()
    assert "cribado" in src.lower()
