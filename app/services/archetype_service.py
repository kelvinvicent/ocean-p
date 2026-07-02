"""
archetype_service — etiqueta descriptiva basada en las 2 dimensiones más altas.

El arquetipo NO es el resultado en sí (siguen siendo los percentiles
continuos). Es una capa de comunicación para que el informe sea memorable,
sin caer en la trampa de MBTI de "forzar a una caja" — dos personas con
el mismo arquetipo pueden tener percentiles muy distintos en las dimensiones
que lo componen.
"""

from __future__ import annotations


DIMENSION_LABELS = {
    "apertura": "Apertura",
    "responsabilidad": "Responsabilidad",
    "extraversion": "Extraversión",
    "amabilidad": "Amabilidad",
    "estabilidad_emocional": "Estabilidad",
}


# 25 combinaciones de las 2 dimensiones dominantes (orden dentro de la tupla
# canónico: alfabético, para que la misma combinación siempre dé el mismo
# nombre, independientemente de cuál quedó más alta en un percentil concreto).
ARCHETYPES: dict[tuple[str, str], str] = {
    ("amabilidad", "apertura"):              "Explorador/a Empático/a",
    ("amabilidad", "estabilidad_emocional"): "Mediador/a",
    ("amabilidad", "extraversion"):          "Conector/a Social",
    ("amabilidad", "responsabilidad"):       "Cooperador/a Confiable",
    ("apertura", "estabilidad_emocional"):   "Innovador/a Sereno/a",
    ("apertura", "extraversion"):            "Estratega Creativo/a",
    ("apertura", "responsabilidad"):         "Innovador/a Disciplinado/a",
    ("estabilidad_emocional", "extraversion"): "Líder Calmado/a",
    ("estabilidad_emocional", "responsabilidad"): "Ejecutor/a Metódico/a",
    ("extraversion", "responsabilidad"):     "Líder Operativo/a",
}


def _normalize_pair(dim_a: str, dim_b: str) -> tuple[str, str]:
    """Ordena alfabéticamente para canónica la combinación."""
    return tuple(sorted([dim_a, dim_b]))  # type: ignore[return-value]


def derive_archetype(
    dimension_percentiles: dict[str, float],
    threshold: float = 55.0,
) -> tuple[str, str]:
    """Devuelve (etiqueta, descripción_corta) según las 2 dimensiones más
    altas en percentil. Si ninguna dimensión supera `threshold`, devuelve
    un arquetipo neutro "Perfil Equilibrado"."""
    sorted_dims = sorted(
        dimension_percentiles.items(), key=lambda kv: kv[1], reverse=True
    )
    top1_key, top1_val = sorted_dims[0]
    top2_key, top2_val = sorted_dims[1]

    if top1_val < threshold:
        return "Perfil Equilibrado", (
            "No mostrás una dominancia marcada en ninguna dimensión. Tu perfil "
            "es versátil y adaptable según el contexto."
        )

    pair = _normalize_pair(top1_key, top2_key)
    archetype = ARCHETYPES.get(pair, f"Perfil {DIMENSION_LABELS[top1_key]} + {DIMENSION_LABELS[top2_key]}")
    description = (
        f"Dominancia alta en {DIMENSION_LABELS[top1_key]} "
        f"(P{top1_val:.0f}) y {DIMENSION_LABELS[top2_key]} "
        f"(P{top2_val:.0f}). Esta combinación sugiere un estilo de trabajo "
        f"característico que conviene reconocer."
    )
    return archetype, description
