"""
interpretation_service — textos descriptivos según percentil.

Devuelve, para una dimensión/faceta/índice y un percentil dado:
- name (legible)
- band ("bajo" | "medio" | "alto")
- behavioral (descripción fija de qué mide)
- text (texto específico para esa banda)

Los textos viven en app/data/interpretations.json para poder actualizarlos
sin tocar código.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

Band = Literal["low", "mid", "high"]

DEFAULTS_PATH = Path(__file__).resolve().parent.parent / "data" / "interpretations.json"


@lru_cache(maxsize=1)
def _load(path_str: str) -> dict:
    with open(path_str, encoding="utf-8") as f:
        return json.load(f)


def _band_for(percentile: float) -> Band:
    if percentile < 35:
        return "low"
    if percentile <= 65:
        return "mid"
    return "high"


def _band_label(percentile: float) -> str:
    return {"low": "bajo", "mid": "medio", "high": "alto"}[_band_for(percentile)]


def interpret_dimension(
    dimension_key: str, percentile: float, path: Path | None = None
) -> dict:
    data = _load(str(path or DEFAULTS_PATH))["dimensions"].get(dimension_key)
    if not data:
        return {
            "name": dimension_key,
            "band": _band_label(percentile),
            "behavioral": "",
            "text": "",
        }
    return {
        "name": data["name"],
        "band": _band_label(percentile),
        "behavioral": data["behavioral"],
        "text": data[_band_for(percentile)],
    }


def interpret_facet(
    facet_key: str, percentile: float, path: Path | None = None
) -> dict:
    data = _load(str(path or DEFAULTS_PATH))["facets"].get(facet_key)
    if not data:
        return {
            "name": facet_key,
            "band": _band_label(percentile),
            "behavioral": "",
            "text": "",
        }
    return {
        "name": facet_key.replace("_", " ").capitalize(),
        "band": _band_label(percentile),
        "behavioral": data["behavioral"],
        "text": data[_band_for(percentile)],
    }


def interpret_composite(
    index_key: str, percentile: float, path: Path | None = None
) -> dict:
    data = _load(str(path or DEFAULTS_PATH))["composite_indices"].get(index_key)
    if not data:
        return {
            "name": index_key,
            "band": _band_label(percentile),
            "behavioral": "",
            "text": "",
        }
    return {
        "name": data["name"],
        "band": _band_label(percentile),
        "behavioral": data["behavioral"],
        "text": data[_band_for(percentile)],
    }
