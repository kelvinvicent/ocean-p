"""
Motor de scoring — Test de Personalidad OCEAN-P
==================================================
Implementa la clave de corrección descrita en el documento de diseño:
- 60 ítems de personalidad (15 facetas x 4 ítems, 1 invertido por faceta)
- 5 ítems de validez (61-65)

Uso:
    from app.services.scoring_engine import score_test
    resultado = score_test(responses)  # responses: dict[int, int] con 65 entradas (valores 1-5)
"""

from dataclasses import dataclass, field
from statistics import mean

# ----------------------------------------------------------------------
# 1. MAPAS DE DATOS (la "clave de corrección" en forma de estructuras)
# ----------------------------------------------------------------------

# Cada faceta = (clave, lista de ítems, set de ítems invertidos dentro de ella)
FACET_ITEMS: dict[str, list[int]] = {
    "curiosidad_intelectual":   [1, 2, 3, 4],
    "creatividad":              [5, 6, 7, 8],
    "apertura_experiencias":    [9, 10, 11, 12],
    "organizacion":             [13, 14, 15, 16],
    "autodisciplina":           [17, 18, 19, 20],
    "orientacion_logro":        [21, 22, 23, 24],
    "sociabilidad":             [25, 26, 27, 28],
    "asertividad":              [29, 30, 31, 32],
    "energia_entusiasmo":       [33, 34, 35, 36],
    "empatia":                  [37, 38, 39, 40],
    "cooperacion":              [41, 42, 43, 44],
    "confianza_interpersonal":  [45, 46, 47, 48],
    "manejo_estres":            [49, 50, 51, 52],
    "regulacion_emocional":     [53, 54, 55, 56],
    "autoconfianza":            [57, 58, 59, 60],
}

# El último ítem de cada faceta es el invertido (R), según el diseño original.
REVERSE_ITEMS: set[int] = {items[-1] for items in FACET_ITEMS.values()}

# Faceta -> dimensión a la que pertenece
FACET_TO_DIMENSION: dict[str, str] = {
    "curiosidad_intelectual": "apertura",
    "creatividad": "apertura",
    "apertura_experiencias": "apertura",
    "organizacion": "responsabilidad",
    "autodisciplina": "responsabilidad",
    "orientacion_logro": "responsabilidad",
    "sociabilidad": "extraversion",
    "asertividad": "extraversion",
    "energia_entusiasmo": "extraversion",
    "empatia": "amabilidad",
    "cooperacion": "amabilidad",
    "confianza_interpersonal": "amabilidad",
    "manejo_estres": "estabilidad_emocional",
    "regulacion_emocional": "estabilidad_emocional",
    "autoconfianza": "estabilidad_emocional",
}

DIMENSIONS: list[str] = [
    "apertura", "responsabilidad", "extraversion", "amabilidad", "estabilidad_emocional"
]

# Índices compuestos profesionales: nombre -> facetas/dimensiones que promedia
# (las dimensiones se referencian con el prefijo "dim:")
COMPOSITE_INDICES: dict[str, list[str]] = {
    "liderazgo_potencial":   ["asertividad", "orientacion_logro", "energia_entusiasmo"],
    "trabajo_equipo":        ["cooperacion", "empatia", "sociabilidad"],
    "tolerancia_riesgo":     ["apertura_experiencias", "creatividad", "dim:estabilidad_emocional"],
    "estilo_ejecucion":      ["organizacion", "autodisciplina", "manejo_estres"],
}

# Ítems de validez
ITEM_DESEABILIDAD = [61, 62]      # esperado: desacuerdo (valores bajos)
ITEM_ATENCION = 63                 # esperado: desacuerdo (valor bajo)
CONSISTENCY_PAIRS = [
    (26, 64, False),  # mismo sentido: item26 alto <-> item64 alto
    (28, 65, False),  # mismo sentido: item28 alto <-> item65 alto
]


@dataclass
class ScoringResult:
    facet_scores: dict[str, float] = field(default_factory=dict)
    dimension_scores: dict[str, float] = field(default_factory=dict)
    composite_scores: dict[str, float] = field(default_factory=dict)
    percentiles: dict[str, float] = field(default_factory=dict)
    validity: dict[str, float] = field(default_factory=dict)
    alerts: list[str] = field(default_factory=list)
    is_conclusive: bool = True


# ----------------------------------------------------------------------
# 2. FUNCIONES PURAS DE CÁLCULO (una por nivel, cada una testeable sola)
# ----------------------------------------------------------------------

def _invert(value: int) -> int:
    """Invierte un valor Likert 1-5: 1<->5, 2<->4, 3 se mantiene."""
    return 6 - value


def _validate_responses(responses: dict[int, int]) -> None:
    expected_ids = set(range(1, 66))
    missing = expected_ids - responses.keys()
    if missing:
        raise ValueError(f"Faltan respuestas para los ítems: {sorted(missing)}")
    out_of_range = [i for i, v in responses.items() if v not in (1, 2, 3, 4, 5)]
    if out_of_range:
        raise ValueError(f"Valores fuera de rango (deben ser 1-5) en ítems: {out_of_range}")


def compute_facet_scores(responses: dict[int, int]) -> dict[str, float]:
    """Calcula el promedio (1-5) de cada una de las 15 facetas, invirtiendo
    primero los ítems marcados como (R)."""
    facet_scores = {}
    for facet, item_ids in FACET_ITEMS.items():
        values = []
        for item_id in item_ids:
            raw = responses[item_id]
            values.append(_invert(raw) if item_id in REVERSE_ITEMS else raw)
        facet_scores[facet] = round(mean(values), 2)
    return facet_scores


def compute_dimension_scores(facet_scores: dict[str, float]) -> dict[str, float]:
    """Promedia las facetas de cada dimensión."""
    dimension_scores = {}
    for dimension in DIMENSIONS:
        facets_in_dim = [f for f, d in FACET_TO_DIMENSION.items() if d == dimension]
        values = [facet_scores[f] for f in facets_in_dim]
        dimension_scores[dimension] = round(mean(values), 2)
    return dimension_scores


def compute_composite_scores(
    facet_scores: dict[str, float], dimension_scores: dict[str, float]
) -> dict[str, float]:
    """Calcula los 4 índices profesionales compuestos."""
    composites = {}
    for index_name, components in COMPOSITE_INDICES.items():
        values = []
        for component in components:
            if component.startswith("dim:"):
                values.append(dimension_scores[component.split(":", 1)[1]])
            else:
                values.append(facet_scores[component])
        composites[index_name] = round(mean(values), 2)
    return composites


def raw_to_percentile(raw_score: float) -> float:
    """Conversión lineal simplificada (1-5 -> 0-100).
    NOTA METODOLÓGICA: esta fórmula es un placeholder de diseño.
    En producción debe reemplazarse por una tabla normativa real (ver PRD, RF-2.7),
    calibrada con una muestra de usuarios reales.
    """
    return round((raw_score - 1) / 4 * 100, 1)


def compute_validity(responses: dict[int, int]) -> tuple[dict[str, float], list[str]]:
    """Calcula las 3 escalas de validez y devuelve también la lista de alertas activadas."""
    alerts: list[str] = []

    deseabilidad = round(mean(responses[i] for i in ITEM_DESEABILIDAD), 2)
    if deseabilidad >= 4.0:
        alerts.append("deseabilidad_social_alta")

    atencion = responses[ITEM_ATENCION]
    if atencion >= 4:
        alerts.append("posible_respuesta_automatica")

    max_inconsistency = 0
    for item_a, item_b, _inverted in CONSISTENCY_PAIRS:
        diff = abs(responses[item_a] - responses[item_b])
        max_inconsistency = max(max_inconsistency, diff)
    if max_inconsistency > 2:
        alerts.append("inconsistencia_detectada")

    validity = {
        "deseabilidad_social": deseabilidad,
        "atencion": float(atencion),
        "inconsistencia_max": float(max_inconsistency),
    }
    return validity, alerts


# ----------------------------------------------------------------------
# 3. FUNCIÓN ORQUESTADORA
# ----------------------------------------------------------------------

def score_test(responses: dict[int, int]) -> ScoringResult:
    """Punto de entrada único: recibe las 65 respuestas y devuelve el resultado completo."""
    _validate_responses(responses)

    facet_scores = compute_facet_scores(responses)
    dimension_scores = compute_dimension_scores(facet_scores)
    composite_scores = compute_composite_scores(facet_scores, dimension_scores)
    validity, alerts = compute_validity(responses)

    percentiles = {}
    for key, score in {**facet_scores, **dimension_scores, **composite_scores}.items():
        percentiles[key] = raw_to_percentile(score)

    is_conclusive = len(alerts) < 2  # regla del documento de diseño: 2+ alertas = no concluyente

    return ScoringResult(
        facet_scores=facet_scores,
        dimension_scores=dimension_scores,
        composite_scores=composite_scores,
        percentiles=percentiles,
        validity=validity,
        alerts=alerts,
        is_conclusive=is_conclusive,
    )


# ----------------------------------------------------------------------
# 4. CASOS DE PRUEBA MANUALES (valido el motor antes de confiar en él)
# ----------------------------------------------------------------------

def _build_responses(default: int, overrides: dict[int, int] | None = None) -> dict[int, int]:
    responses = {i: default for i in range(1, 66)}
    if overrides:
        responses.update(overrides)
    return responses


if __name__ == "__main__":
    print("=" * 60)
    print("CASO A — Todas las respuestas = 3 (perfil neutro)")
    print("=" * 60)
    responses_a = _build_responses(default=3)
    result_a = score_test(responses_a)
    print("Esperado: todas las facetas y dimensiones en 3.0, percentil 50.0")
    print("Facetas:", result_a.facet_scores)
    print("Dimensiones:", result_a.dimension_scores)
    print("Percentil ejemplo (apertura):", result_a.percentiles["apertura"])
    assert all(v == 3.0 for v in result_a.dimension_scores.values())
    assert result_a.percentiles["apertura"] == 50.0
    print("✅ Caso A correcto\n")

    print("=" * 60)
    print("CASO B — Perfil 'alto en todo' consistente (directos=5, inversos=1)")
    print("=" * 60)
    overrides_b = {item: 1 for item in REVERSE_ITEMS}
    responses_b = _build_responses(default=5, overrides=overrides_b)
    # Ajustamos también los ítems de consistencia para que sean coherentes con "alto"
    responses_b[64] = 5  # debe ser coherente con item 26 (=5)
    responses_b[65] = 1  # ítem 65 es la versión inversa conceptual del 28 (=5 directo -> alto en sociabilidad)
    result_b = score_test(responses_b)
    print("Esperado: todas las facetas de personalidad = 5.0, percentil 100.0")
    print("Facetas:", result_b.facet_scores)
    assert all(v == 5.0 for v in result_b.facet_scores.values())
    assert result_b.percentiles["responsabilidad"] == 100.0
    print("✅ Caso B correcto\n")

    print("=" * 60)
    print("CASO C — Respuestas con deseabilidad social alta (debe activar alerta)")
    print("=" * 60)
    responses_c = _build_responses(default=3, overrides={61: 5, 62: 5, 63: 4})
    result_c = score_test(responses_c)
    print("Alertas activadas:", result_c.alerts)
    print("¿Resultado concluyente?:", result_c.is_conclusive)
    assert "deseabilidad_social_alta" in result_c.alerts
    assert "posible_respuesta_automatica" in result_c.alerts
    assert result_c.is_conclusive is False
    print("✅ Caso C correcto — el sistema detecta correctamente un perfil poco fiable\n")

    print("=" * 60)
    print("CASO D — Inconsistencia entre ítems espejo (26 vs 64)")
    print("=" * 60)
    responses_d = _build_responses(default=3, overrides={26: 5, 64: 1})
    result_d = score_test(responses_d)
    print("Alertas activadas:", result_d.alerts)
    assert "inconsistencia_detectada" in result_d.alerts
    print("✅ Caso D correcto — detecta que la persona se contradijo\n")

    print("Todos los casos de prueba pasaron correctamente.")
