# 🧠 OCEAN-P — Test de Personalidad Profesional

Aplicación web para realizar un test de personalidad basado en el modelo **OCEAN** (Big Five), con módulo de **competencias profesionales** integrado. Genera un informe accionable con 5 dimensiones, 15 facetas, 4 índices profesionales y 3 escalas de validez.

## Estado del proyecto

- ✅ **Fase 1 (MVP) — COMPLETA:** cuestionario + motor de scoring + informe en pantalla
- ⏳ **Fase 2 — Pendiente:** exportación a PDF + envío por email
- ⏳ **Fase 3 — Pendiente:** tests complementarios, microrretos, insignias

## Quick start

### Windows — un solo clic

```bash
arrancar.bat
```

Eso es todo. El script crea el venv, instala dependencias, aplica migraciones y arranca el servidor. Abrí `http://127.0.0.1:8000/quiz` en tu navegador.

### Windows (PowerShell)

```powershell
.\arrancar.ps1
```

### Manual (cualquier OS)

```bash
python -m venv .venv
source .venv/bin/activate          # o .venv\Scripts\activate en Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## Documentación

- **[GUIA-LOCAL.md](./GUIA-LOCAL.md)** — guía completa de uso local (instalación, recorrido del flujo, tests, troubleshooting)
- **[PLAN-IMPLEMENTACION.md](./PLAN-IMPLEMENTACION.md)** — plan de implementación por fases
- **[PRD-test-personalidad-OCEAN-P.md](./PRD-test-personalidad-OCEAN-P.md)** — requisitos del producto
- **[test-personalidad-OCEAN-P.md](./test-personalidad-OCEAN-P.md)** — diseño psicométrico completo

## Tests

```bash
pytest -v
```

**88 tests pasando** que cubren: motor de scoring, percentiles normativos, endpoints REST, vistas HTML y servicio de interpretaciones.

## Stack

- **Backend:** Python 3.12 + FastAPI + SQLModel
- **BD:** SQLite (dev) / PostgreSQL/Neon (prod) — sin cambios de código
- **Frontend:** Jinja2 + HTMX + Alpine.js + Tailwind (Play CDN) + Anime.js
- **Tests:** pytest
- **Migraciones:** Alembic

## Estructura

```
app/
├── main.py                  # Entry point FastAPI
├── config.py                # Settings (.env)
├── database.py              # Engine SQLModel
├── models/                  # 7 modelos (User, TestSession, ItemResponse, Score, Report, EmailDelivery, NormTable)
├── routers/
│   ├── quiz.py              # Endpoints REST del cuestionario
│   ├── views.py             # Renderiza templates
│   └── report.py            # Informe + calculating
├── services/                # scoring_engine, scoring_service, norm_service, archetype_service, interpretation_service
├── data/                    # items.json, norms_v1.json, interpretations.json
├── templates/               # Jinja2 (landing, instructions, quiz, calculating, report, base)
└── static/                  # CSS + JS

tests/                       # 88 tests pytest
migrations/                  # Alembic
```

## Licencia

Privado.
