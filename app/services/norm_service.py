"""
norm_service — conversión raw_score → percentil (RF-2.6, RF-2.7).

Carga la tabla normativa v1 desde `app/data/norms_v1.json` por defecto.
La estructura permite reemplazar el JSON por una versión calibrada con datos
reales sin tocar el motor de scoring (se cambia el archivo, o más adelante
se carga desde la tabla `norm_tables` de la BD).

Métodos soportados:
- "linear": percentil = clamp(round(z * 25 + 50), 1, 99) usando mean/sd del
  scope_key; si no hay parámetros, cae a la fórmula (raw-1)/4*100.
- "lookup": tabla explícita {raw: percentile} (para futuras calibraciones
  no-lineales).
"""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Optional


DEFAULTS_PATH = Path(__file__).resolve().parent.parent / "data" / "norms_v1.json"


@lru_cache(maxsize=1)
def _load_norms(path_str: str) -> dict:
    with open(path_str, encoding="utf-8") as f:
        return json.load(f)


def _clamp(value: float, lo: float = 1.0, hi: float = 99.0) -> float:
    return max(lo, min(hi, value))


def _linear_percentile(raw: float, mean: float, sd: float) -> float:
    """Convierte raw (1-5) a percentil asumiendo distribución normal(mean, sd).
    Limitado a 1-99 para no mostrar 0/100 (interpretación psicométrica)."""
    if sd <= 0:
        return 50.0
    z = (raw - mean) / sd
    # CDF normal estándar aproximada (Abramowitz & Stegun 7.1.26)
    percentile = 50.0 * (1.0 + math.erf(z / math.sqrt(2.0)))
    return _clamp(round(percentile, 1))


def _fallback_percentile(raw: float) -> float:
    """Fórmula lineal (raw-1)/4*100 cuando no hay mean/sd para el scope_key."""
    return _clamp(round((raw - 1.0) / 4.0 * 100.0, 1))


def raw_to_percentile(
    scope_key: str,
    raw_score: float,
    version: str = "v1",
    norms_path: Optional[Path] = None,
) -> float:
    """Convierte una puntuación bruta (1-5) a percentil (1-99) según la tabla
    normativa activa."""
    norms = _load_norms(str(norms_path or DEFAULTS_PATH))
    mapping = norms.get("mappings", {}).get(scope_key)

    if not mapping:
        return _fallback_percentile(raw_score)

    method = mapping.get("method", "linear")
    if method == "lookup":
        # Tabla explícita (futuro: calibración no-lineal)
        table = mapping.get("table", {})
        key = f"{raw_score:.1f}"
        if key in table:
            return _clamp(float(table[key]))
        return _fallback_percentile(raw_score)

    if method == "linear":
        mean = mapping.get("mean")
        sd = mapping.get("sd")
        if mean is not None and sd is not None:
            return _linear_percentile(raw_score, mean, sd)
        return _fallback_percentile(raw_score)

    return _fallback_percentile(raw_score)


def get_norms_version(norms_path: Optional[Path] = None) -> str:
    norms = _load_norms(str(norms_path or DEFAULTS_PATH))
    return norms.get("version", "v1")
