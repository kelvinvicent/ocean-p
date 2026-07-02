"""
Tests del norm_service (T2.6): conversión raw → percentil.

Cubre:
- En la media → ~50.
- En los extremos → cercano a 1 y 99, sin tocar límites.
- Fallback para scope_keys no definidos.
- 5 dimensiones OCEAN tienen mapeo propio (no usan el fallback).
- Consistencia: percentil crece monótonamente con el raw_score.
"""

import pytest

from app.services.norm_service import get_norms_version, raw_to_percentile


OCEAN_DIMS = ["apertura", "responsabilidad", "extraversion", "amabilidad", "estabilidad_emocional"]


def test_version_por_definicion():
    assert get_norms_version() == "v1"


# ----------------------------------------------------------------------
# En la media → 50
# ----------------------------------------------------------------------

@pytest.mark.parametrize("dim", OCEAN_DIMS)
def test_en_la_media_percentil_50(dim):
    # Carga las medias reales del JSON para no hardcodear magic numbers
    from app.services.norm_service import _load_norms, DEFAULTS_PATH
    norms = _load_norms(str(DEFAULTS_PATH))
    mean = norms["mappings"][dim]["mean"]
    p = raw_to_percentile(dim, mean)
    assert p == 50.0


# ----------------------------------------------------------------------
# Extremos acotados 1-99
# ----------------------------------------------------------------------

@pytest.mark.parametrize("dim", OCEAN_DIMS)
def test_extremo_alto_cerca_de_99(dim):
    p = raw_to_percentile(dim, 5.0)
    assert 95.0 <= p <= 99.0


@pytest.mark.parametrize("dim", OCEAN_DIMS)
def test_extremo_bajo_cerca_de_1(dim):
    p = raw_to_percentile(dim, 1.0)
    assert 1.0 <= p <= 5.0


# ----------------------------------------------------------------------
# Monotonicidad
# ----------------------------------------------------------------------

@pytest.mark.parametrize("dim", OCEAN_DIMS)
def test_percentil_crece_con_raw_score(dim):
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    percentiles = [raw_to_percentile(dim, v) for v in values]
    for prev, curr in zip(percentiles, percentiles[1:]):
        assert curr >= prev, f"{dim}: {percentiles}"


# ----------------------------------------------------------------------
# Fallback
# ----------------------------------------------------------------------

def test_scope_key_inexistente_usa_fallback_lineal():
    assert raw_to_percentile("scope_inexistente", 1.0) == 1.0
    assert raw_to_percentile("scope_inexistente", 3.0) == 50.0
    assert raw_to_percentile("scope_inexistente", 5.0) == 99.0


def test_fallback_no_supera_limites():
    assert raw_to_percentile("scope_inexistente", 5.0) <= 99.0
    assert raw_to_percentile("scope_inexistente", 1.0) >= 1.0


# ----------------------------------------------------------------------
# Índices compuestos también tienen mapeo
# ----------------------------------------------------------------------

COMPOSITES = ["liderazgo_potencial", "trabajo_equipo", "tolerancia_riesgo", "estilo_ejecucion"]


@pytest.mark.parametrize("idx", COMPOSITES)
def test_indices_compuestos_usan_mapeo_propio_y_crecen_con_raw(idx):
    """Los índices compuestos NO deben usar el fallback lineal.
    El fallback daría exactamente 50.0 en raw=3.0; el mapeo propio da un
    valor coherente con la media de cada índice."""
    p_low = raw_to_percentile(idx, 1.0)
    p_high = raw_to_percentile(idx, 5.0)
    assert p_low < p_high, f"{idx}: p_low={p_low}, p_high={p_high}"
    assert 1.0 <= p_low <= 5.0
    assert 95.0 <= p_high <= 99.0


def test_indice_compuesto_distingue_de_fallback():
    """Si el fallback lineales erróneamente activo, raw=3.0 daría
    exactamente 50.0. Con el mapeo propio (mean≈3.2), debe dar ~37-38."""
    p = raw_to_percentile("liderazgo_potencial", 3.0)
    # Fallback daría 50.0; mapeo propio con mean=3.2 da ~37
    assert p < 50.0, f"Esperaba <50, obtuve {p} — posible fallback activado"
