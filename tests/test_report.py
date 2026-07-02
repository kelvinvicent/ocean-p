"""
Tests del informe en pantalla (T3.1-T3.4) y del interpretation_service.
"""

import pytest

from app.services.interpretation_service import (
    interpret_composite,
    interpret_dimension,
    interpret_facet,
)


# ----------------------------------------------------------------------
# Helper: completa un test en una sesión
# ----------------------------------------------------------------------

@pytest.fixture
def completed_session(client):
    sid = client.post("/sessions").json()["session_id"]
    for item_id in range(1, 66):
        client.post(f"/sessions/{sid}/responses",
                    json={"item_id": item_id, "raw_value": 3})
    client.post(f"/sessions/{sid}/submit")
    return sid


@pytest.fixture
def invalid_session(client):
    sid = client.post("/sessions").json()["session_id"]
    for item_id in range(1, 66):
        value = 5 if item_id in (61, 62, 63) else 3
        client.post(f"/sessions/{sid}/responses",
                    json={"item_id": item_id, "raw_value": value})
    client.post(f"/sessions/{sid}/submit")
    return sid


# ----------------------------------------------------------------------
# /report/{session_id}
# ----------------------------------------------------------------------

def test_report_404_si_sesion_no_existe(client):
    r = client.get("/report/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


def test_report_409_si_sesion_sin_submit(client):
    sid = client.post("/sessions").json()["session_id"]
    r = client.get(f"/report/{sid}")
    assert r.status_code == 409


def test_report_200_si_completado(client, completed_session):
    sid = completed_session
    r = client.get(f"/report/{sid}")
    assert r.status_code == 200
    body = r.text
    # Secciones principales
    assert "Dimensiones OCEAN" in body
    assert "Detalle por faceta" in body
    assert "Índices profesionales" in body
    # 5 dimensiones con sus nombres
    for dim in ["Apertura a la experiencia", "Responsabilidad",
                "Extraversión", "Amabilidad", "Estabilidad emocional"]:
        assert dim in body
    # Percentiles
    assert "P50" in body
    # 4 índices profesionales
    for idx in ["Liderazgo potencial", "Trabajo en equipo",
                "Tolerancia al riesgo", "Estilo de ejecución"]:
        assert idx in body


def test_report_muestra_banner_si_invalid(client, invalid_session):
    sid = invalid_session
    r = client.get(f"/report/{sid}")
    assert r.status_code == 200
    assert "Resultado no concluyente" in r.text
    assert "Repetir el test" in r.text


def test_report_no_muestra_banner_si_completado(client, completed_session):
    sid = completed_session
    r = client.get(f"/report/{sid}")
    assert r.status_code == 200
    assert "Resultado no concluyente" not in r.text


def test_report_incluye_grafico_de_dimensiones(client, completed_session):
    r = client.get(f"/report/{completed_session}")
    # 5 barras de dimensión con data-dimension
    assert r.text.count("data-dimension=") == 5
    # El JS de animación está enlazado
    assert "/static/js/report.js" in r.text
    assert "dimension-bar-fill" in r.text


def test_report_tiene_fortalezas_y_areas_desarrollo(client, completed_session):
    r = client.get(f"/report/{completed_session}")
    assert "Fortalezas principales" in r.text
    assert "Áreas de desarrollo" in r.text


def test_report_ctas_exportacion_placeholders(client, completed_session):
    r = client.get(f"/report/{completed_session}")
    assert "Descargar PDF" in r.text
    assert "próximamente" in r.text
    # Los botones están deshabilitados (Fase 2)
    assert 'disabled' in r.text


# ----------------------------------------------------------------------
# Riesgo 4 — Disclaimer de tabla normativa inicial
# ----------------------------------------------------------------------

def test_report_incluye_disclaimer_normativo(client, completed_session):
    """El informe debe advertir que los percentiles son una referencia
    inicial que se recalibrará (transparencia estadística)."""
    r = client.get(f"/report/{completed_session}")
    assert r.status_code == 200
    body = r.text
    assert "norm-disclaimer" in body
    assert "Sobre los percentiles" in body
    assert "muestra de referencia inicial" in body
    # Contiene el ID del bloque para tests visuales
    assert 'id="norm-disclaimer"' in body


def test_report_disclaimer_en_sesion_invalid_tambien(client, invalid_session):
    r = client.get(f"/report/{invalid_session}")
    assert r.status_code == 200
    # El disclaimer aparece siempre, no solo en sesiones válidas
    assert "Sobre los percentiles" in r.text


def test_report_disclaimer_tiene_id_para_anchor_y_seo(client, completed_session):
    """ID estable para que el PDF (Fase 2) pueda incluir el mismo bloque."""
    r = client.get(f"/report/{completed_session}")
    assert 'id="norm-disclaimer"' in r.text


# ----------------------------------------------------------------------
# /calculating/{session_id}
# ----------------------------------------------------------------------

def test_calculating_redirige_si_sesion_ya_completada(client, completed_session):
    r = client.get(f"/calculating/{completed_session}", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == f"/report/{completed_session}"


def test_calculating_muestra_loader_si_sesion_in_progress(client):
    sid = client.post("/sessions").json()["session_id"]
    r = client.get(f"/calculating/{sid}")
    assert r.status_code == 200
    assert "Calculando tu perfil" in r.text
    # 5 anillos OCEAN en el SVG
    for ring in ["ring-O", "ring-C", "ring-E", "ring-A", "ring-N"]:
        assert ring in r.text
    # JS de polling incluido
    assert "pollStatus" in r.text


def test_calculating_404_si_sesion_inexistente(client):
    r = client.get("/calculating/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


# ----------------------------------------------------------------------
# interpretation_service
# ----------------------------------------------------------------------

def test_interpretacion_dimension_banda_baja():
    r = interpret_dimension("apertura", 25)
    assert r["band"] == "bajo"
    assert r["name"] == "Apertura a la experiencia"
    assert "práctico" in r["text"].lower() or "concreto" in r["text"].lower()
    assert r["behavioral"]


def test_interpretacion_dimension_banda_media():
    r = interpret_dimension("responsabilidad", 50)
    assert r["band"] == "medio"
    assert "equilibrio" in r["text"].lower() or "disciplina" in r["text"].lower()


def test_interpretacion_dimension_banda_alta():
    r = interpret_dimension("extraversion", 90)
    assert r["band"] == "alto"
    assert "energ" in r["text"].lower() or "lider" in r["text"].lower()


def test_interpretacion_dimension_limite_35_es_medio():
    # Percentil 35 debe caer en "mid" (35 <= p <= 65)
    r = interpret_dimension("amabilidad", 35)
    assert r["band"] == "medio"


def test_interpretacion_dimension_limite_65_es_medio():
    r = interpret_dimension("amabilidad", 65)
    assert r["band"] == "medio"


def test_interpretacion_facet_incluye_text_y_behavioral():
    r = interpret_facet("asertividad", 75)
    assert r["name"]
    assert r["behavioral"]
    assert r["text"]
    assert r["band"] == "alto"


def test_interpretacion_composite_incluye_text_y_behavioral():
    r = interpret_composite("liderazgo_potencial", 45)
    assert r["name"] == "Liderazgo potencial"
    assert r["band"] == "medio"
    assert "asertivi" in r["behavioral"].lower() or "logro" in r["behavioral"].lower()


def test_interpretacion_scope_inexistente_devuelve_dict_basico():
    r = interpret_dimension("xyz_inexistente", 50)
    assert r["band"] == "medio"
    assert r["name"] == "xyz_inexistente"
    assert r["text"] == ""
