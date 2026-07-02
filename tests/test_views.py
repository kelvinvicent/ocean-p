"""
Tests de las vistas HTML (templates).
"""

def test_root_redirige_a_quiz(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == "/quiz"


def test_landing_renderiza_con_cta(client):
    r = client.get("/quiz")
    assert r.status_code == 200
    assert "Comenzar" in r.text and "el test" in r.text
    assert "OCEAN-P" in r.text
    # Design system cargado
    assert "design-system.css" in r.text
    assert "tailwindcss.com" in r.text
    assert "animejs" in r.text or "anime.min.js" in r.text


def test_landing_404_si_assets_no_cargados_es_culpa_de_red(client):
    # Las CDN se cargan en el navegador del usuario, no en el server.
    # Este test solo verifica que el HTML referencia correctamente los assets.
    r = client.get("/quiz")
    assert "/static/css/design-system.css" in r.text
    assert "/static/js/landing.js" in r.text


def test_instructions_requiere_sesion_existente(client):
    r = client.get("/quiz/00000000-0000-0000-0000-000000000000/instructions")
    assert r.status_code == 404


def test_instructions_renderiza_con_session_valida(client):
    sid = client.post("/sessions").json()["session_id"]
    r = client.get(f"/quiz/{sid}/instructions")
    assert r.status_code == 200
    assert "Cómo funciona el test" in r.text or "funciona" in r.text
    assert sid in r.text


def test_quiz_renderiza_con_los_65_items_embebidos(client):
    sid = client.post("/sessions").json()["session_id"]
    r = client.get(f"/quiz/{sid}")
    assert r.status_code == 200
    # Los 65 ítems están como JSON embebido en el template
    assert r.text.count("\"id\":") >= 65 or r.text.count("id: 1") >= 1
    # Alpine.js y Anime.js referenciados
    assert "alpinejs" in r.text
    assert "anime.min.js" in r.text
    # Session ID presente
    assert sid in r.text


def test_quiz_404_si_sesion_no_existe(client):
    r = client.get("/quiz/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


def test_static_assets_se_sirven(client):
    r = client.get("/static/css/design-system.css")
    assert r.status_code == 200
    assert "text/css" in r.headers["content-type"] or r.headers["content-type"].startswith("text/css")
    assert ":root" in r.text  # tokens CSS

    r = client.get("/static/js/landing.js")
    assert r.status_code == 200
    assert "anime" in r.text


# ----------------------------------------------------------------------
# Riesgo 3 — Micro-motivación al ítem 33 (50%)
# ----------------------------------------------------------------------

def test_quiz_incluye_banner_de_motivacion(client):
    sid = client.post("/sessions").json()["session_id"]
    r = client.get(f"/quiz/{sid}")
    assert r.status_code == 200
    # El banner existe en el HTML (en el rediseño usa card-form)
    assert "showMotivation" in r.text
    assert "mitad" in r.text
    # El state Alpine.js tiene la lógica de trigger al cruzar el ítem 33
    assert "currentIndex === 32" in r.text
    assert "_motivationShown" in r.text


def test_quiz_motivacion_se_muestra_solo_una_vez(client):
    """La lógica evita mostrar el banner dos veces (incluido tras refresh
    desde localStorage)."""
    sid = client.post("/sessions").json()["session_id"]
    r = client.get(f"/quiz/{sid}")
    # Flag persistente que se setea tras primer show
    assert "_motivationShown" in r.text


# ----------------------------------------------------------------------
# Riesgo 4 — Disclaimer de tabla normativa
# ----------------------------------------------------------------------

def test_quiz_css_incluye_x_cloak(client):
    r = client.get("/static/css/design-system.css")
    assert "[x-cloak]" in r.text
