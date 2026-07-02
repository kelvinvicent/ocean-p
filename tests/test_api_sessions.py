"""
Tests de los endpoints REST de /sessions (T1.4, T1.5, T1.6, T2.3).
"""

import pytest


def test_crear_sesion_devuelve_uuid(client):
    r = client.post("/sessions")
    assert r.status_code == 201
    body = r.json()
    assert "session_id" in body
    assert len(body["session_id"]) == 36  # UUID v4 con guiones
    assert "started_at" in body


def test_dos_sesiones_tienen_ids_distintos(client):
    a = client.post("/sessions").json()["session_id"]
    b = client.post("/sessions").json()["session_id"]
    assert a != b


def test_guardar_respuesta_incrementa_total(client):
    sid = client.post("/sessions").json()["session_id"]
    r = client.post(
        f"/sessions/{sid}/responses",
        json={"item_id": 1, "raw_value": 4, "response_time_ms": 1200},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["total_answered"] == 1
    assert body["item_id"] == 1


def test_guardar_respuesta_actualiza_si_existe(client):
    sid = client.post("/sessions").json()["session_id"]
    client.post(f"/sessions/{sid}/responses",
                json={"item_id": 1, "raw_value": 3})
    r = client.post(f"/sessions/{sid}/responses",
                    json={"item_id": 1, "raw_value": 5})
    assert r.status_code == 201
    assert r.json()["total_answered"] == 1  # No incrementa, solo actualiza

    state = client.get(f"/sessions/{sid}/state").json()
    assert state["answered"]["1"] == 5


def test_validaciones_payload_respuesta(client):
    sid = client.post("/sessions").json()["session_id"]
    # item_id fuera de rango
    r = client.post(f"/sessions/{sid}/responses",
                    json={"item_id": 0, "raw_value": 3})
    assert r.status_code == 422
    # raw_value fuera de rango
    r = client.post(f"/sessions/{sid}/responses",
                    json={"item_id": 1, "raw_value": 7})
    assert r.status_code == 422


def test_sesion_inexistente_404(client):
    r = client.post(
        "/sessions/00000000-0000-0000-0000-000000000000/responses",
        json={"item_id": 1, "raw_value": 3},
    )
    assert r.status_code == 404


def test_state_vacio_al_inicio(client):
    sid = client.post("/sessions").json()["session_id"]
    r = client.get(f"/sessions/{sid}/state")
    assert r.status_code == 200
    body = r.json()
    assert body["total_answered"] == 0
    assert body["status"] == "in_progress"
    assert body["answered"] == {}
    assert body["total_items"] == 65


def test_state_refleja_respuestas_guardadas(client):
    sid = client.post("/sessions").json()["session_id"]
    for item_id, value in [(1, 5), (10, 3), (65, 1)]:
        client.post(f"/sessions/{sid}/responses",
                    json={"item_id": item_id, "raw_value": value})
    state = client.get(f"/sessions/{sid}/state").json()
    assert state["total_answered"] == 3
    assert state["answered"] == {"1": 5, "10": 3, "65": 1}


def test_state_404_si_sesion_no_existe(client):
    r = client.get("/sessions/00000000-0000-0000-0000-000000000000/state")
    assert r.status_code == 404


# ----------------------------------------------------------------------
# T2.3 — submit y cálculo
# ----------------------------------------------------------------------

def test_submit_falla_si_incompleto(client):
    sid = client.post("/sessions").json()["session_id"]
    client.post(f"/sessions/{sid}/responses", json={"item_id": 1, "raw_value": 3})
    r = client.post(f"/sessions/{sid}/submit")
    assert r.status_code == 422
    assert "1/65" in r.json()["detail"]


def test_submit_exitoso_con_65_respuestas(client):
    sid = client.post("/sessions").json()["session_id"]
    for item_id in range(1, 66):
        client.post(f"/sessions/{sid}/responses",
                    json={"item_id": item_id, "raw_value": 3})
    r = client.post(f"/sessions/{sid}/submit")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "completed"
    assert body["is_conclusive"] is True
    assert "report_id" in body
    assert "archetype_label" in body


def test_submit_marca_invalid_con_deseabilidad_alta(client):
    sid = client.post("/sessions").json()["session_id"]
    for item_id in range(1, 66):
        value = 5 if item_id in (61, 62, 63) else 3
        client.post(f"/sessions/{sid}/responses",
                    json={"item_id": item_id, "raw_value": value})
    r = client.post(f"/sessions/{sid}/submit")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "invalid"
    assert body["is_conclusive"] is False


def test_submit_no_se_puede_repetir(client):
    sid = client.post("/sessions").json()["session_id"]
    for item_id in range(1, 66):
        client.post(f"/sessions/{sid}/responses",
                    json={"item_id": item_id, "raw_value": 3})
    client.post(f"/sessions/{sid}/submit")
    r = client.post(f"/sessions/{sid}/submit")
    assert r.status_code == 409
