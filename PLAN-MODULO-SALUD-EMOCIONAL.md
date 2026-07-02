# 🧠 Plan de Implementación — Módulo de Salud Emocional
## Versión 1.0 | Basado en PRD v1.0 + `emotional_health_engine.py` ya validado

> **Contexto:** Este módulo se integra al proyecto OCEAN-P existente. El motor de scoring (`emotional_health_engine.py`) ya está completo y con 9 casos de prueba pasando (A–I). El plan arranca desde ahí, sin reescribir lo que ya funciona.

---

## 📋 Estado actual del motor (lo que ya existe y NO se toca)

| Función | Estado | Casos de prueba |
|---|---|---|
| `score_phq9()` | ✅ Completo | Casos A, B, C |
| `score_gad7()` | ✅ Completo | Casos A, B |
| `score_sleep()` | ✅ Completo | Incluido en A–C |
| `score_who5()` | ✅ Completo | Casos D, E |
| `score_phq15()` | ✅ Completo | Caso F |
| `score_rosenberg()` | ✅ Completo | Casos G, H |
| `score_assessment()` | ✅ Completo | Caso I |
| Checklists (cognitivo, conductual, irritabilidad) | ⚠️ Banco de ítems pendiente | — |
| Contexto de vida | ✅ `CONTEXT_ITEMS` definido | — |

> **El PRD (RF-2.1) pedía extender el motor — ya está hecho.** El trabajo pendiente es conectarlo al sistema.

---

## 🗺️ Arquitectura de archivos nuevos (sobre la estructura existente)

```
Test personalidad/
├── emotional_health_engine.py       ✅ YA EXISTE — no se modifica
├── app/
│   ├── models/
│   │   └── __init__.py              → agregar modelos de salud emocional
│   ├── routers/
│   │   ├── quiz.py                  (existente — OCEAN-P)
│   │   ├── report.py                (existente — OCEAN-P)
│   │   └── emotional_health.py      🆕 NUEVO — todas las rutas del módulo
│   ├── services/
│   │   ├── scoring_engine.py        (existente — OCEAN-P)
│   │   └── emotional_scoring_service.py  🆕 NUEVO — adaptador entre el engine y FastAPI
│   └── templates/
│       ├── base.html                (existente — base compartida)
│       ├── eh_landing.html          🆕 NUEVO — landing + disclaimer
│       ├── eh_quiz.html             🆕 NUEVO — cuestionario (8 bloques)
│       ├── eh_crisis.html           🆕 NUEVO — pantalla de alerta de crisis (RS-2)
│       ├── eh_calculating.html      🆕 NUEVO — pantalla de carga (reutiliza patrón)
│       ├── eh_report.html           🆕 NUEVO — informe en pantalla
│       └── eh_report_pdf.html       🆕 NUEVO — plantilla PDF (WeasyPrint)
└── migrations/
    └── versions/
        └── 00X_emotional_health_tables.py  🆕 NUEVO — Alembic migration
```

---

## 🔴 FASE 0 — Requisitos de Seguridad primero (RS-1 a RS-7)
**Duración estimada: 1 día | Prioridad: ABSOLUTA — nada más puede empezar sin esto**

> **Regla del PRD:** ningún requisito funcional puede implementarse de forma que contradiga un requisito de seguridad.

### Tarea 0.1 — Definir los ítems de los checklists no clínicos

El motor ya tiene los ítems de PHQ-9, GAD-7, WHO-5, PHQ-15, Rosenberg, Sueño y Contexto.
**Falta:** el banco de ítems para los 3 checklists sin puntaje.

Agregar en `emotional_health_engine.py` (sección 1, junto a los demás):

```python
COGNITIVE_CHECKLIST_ITEMS: dict[int, str] = {
    1: "He tenido dificultad para concentrarme en tareas simples",
    2: "Olvido cosas que normalmente recordaría con facilidad",
    3: "Siento que mi pensamiento es más lento de lo usual",
    4: "Me cuesta trabajo tomar decisiones aunque sean pequeñas",
    5: "Tengo dificultad para retener información nueva",
    6: "Me pierdo en mitad de conversaciones o lecturas",
    7: "Siento una sensación de 'niebla' o confusión mental",
    8: "Me cuesta iniciar tareas aunque sepa que debo hacerlas",
}

BEHAVIORAL_CHECKLIST_ITEMS: dict[int, str] = {
    1: "He reducido actividades que antes disfrutaba",
    2: "Me he aislado de amigos o familia",
    3: "He descuidado tareas del hogar, trabajo o estudio",
    4: "He perdido la motivación para salir de casa",
    5: "Como de forma diferente a lo habitual (mucho más o mucho menos)",
    6: "Me cuesta mantener una rutina diaria",
    7: "He pospuesto cosas importantes sin poder retomarlo",
    8: "Paso más tiempo de lo usual en cama o sin actividad",
}

IRRITABILITY_CHECKLIST_ITEMS: dict[int, str] = {
    1: "Me he irritado o molestado con facilidad, más de lo normal",
    2: "He tenido reacciones exageradas ante situaciones pequeñas",
    3: "Me siento con poca tolerancia hacia los demás",
    4: "He tenido conflictos o fricciones que no son habituales en mí",
}
```

### Tarea 0.2 — Crear la tabla `crisis_resources` en el modelo de datos

Esta tabla debe existir antes de cualquier UI de crisis (RS-3). Se define en el modelo de datos pero se **puebla manualmente** con los recursos oficiales verificados (pendiente bloqueante de la sección 10 del PRD — no técnico).

### Tarea 0.3 — Verificar manualmente el Caso C del motor

Antes de conectar cualquier interfaz, ejecutar:
```bash
python emotional_health_engine.py
```
Confirmar que el Caso C pasa: `crisis_alert=True` cuando ítem 9 > 0 aunque el total sea mínimo.

> ⚠️ **RS-1 bloqueante:** si el Caso C falla, no se puede continuar. La alerta de crisis es el requisito de mayor prioridad del módulo.

---

## 🗄️ FASE 1 — Modelo de datos (Alembic migration)
**Duración estimada: 1 día | Dependencia: Fase 0 completa**

### Tarea 1.1 — Crear modelos SQLModel en `app/models/__init__.py`

Agregar al final del archivo, sin modificar los modelos existentes de OCEAN-P:

```python
# ─────────────────────────────────────────────────────────────
# MÓDULO DE SALUD EMOCIONAL — modelos nuevos
# ─────────────────────────────────────────────────────────────

class EmotionalAssessment(SQLModel, table=True):
    __tablename__ = "emotional_assessments"
    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="test_sessions.id")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    disclaimer_accepted: bool = False           # RS-4

class EmotionalResponse(SQLModel, table=True):
    __tablename__ = "emotional_responses"
    id: int | None = Field(default=None, primary_key=True)
    assessment_id: int = Field(foreign_key="emotional_assessments.id")
    module: str  # phq9 | who5 | phq15 | cognitive_checklist | behavioral_checklist
                 # gad7 | irritability_checklist | rosenberg | sleep | context
    item_id: int
    raw_value: int
    is_scored: bool = True  # False para checklists no clínicos y contexto

class EmotionalScore(SQLModel, table=True):
    __tablename__ = "emotional_scores"
    id: int | None = Field(default=None, primary_key=True)
    assessment_id: int = Field(foreign_key="emotional_assessments.id")
    module: str          # phq9 | who5 | phq15 | gad7 | rosenberg | sleep
    response_scale: str  # "0-3_4opciones" | "0-5_6opciones" | "0-2_3opciones"
    total_score: float
    severity_band: str
    is_clinically_validated: bool = True
    crisis_alert: bool = False               # RS-1, solo aplica a phq9
    professional_help_recommended: bool = False  # RS-5

class EmotionalChecklistSelection(SQLModel, table=True):
    __tablename__ = "emotional_checklist_selections"
    id: int | None = Field(default=None, primary_key=True)
    assessment_id: int = Field(foreign_key="emotional_assessments.id")
    module: str  # cognitive_checklist | behavioral_checklist | irritability_checklist
    item_id: int
    selected: bool

class CrisisResource(SQLModel, table=True):
    __tablename__ = "crisis_resources"
    id: int | None = Field(default=None, primary_key=True)
    country_code: str           # "VE" | "ES" | "MX" | etc.
    resource_name: str
    contact_info: str           # teléfono, url, o descripción de chat
    active: bool = True
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### Tarea 1.2 — Generar y aplicar la migración Alembic

```bash
alembic revision --autogenerate -m "emotional_health_tables"
alembic upgrade head
```

**Verificar:** las 5 tablas nuevas existen sin romper las tablas OCEAN-P existentes.

---

## ⚙️ FASE 2 — Servicio adaptador
**Duración estimada: 0.5 día | Dependencia: Fase 1 completa**

### Tarea 2.1 — Crear `app/services/emotional_scoring_service.py`

Este archivo es el **puente** entre el motor puro (`emotional_health_engine.py`) y FastAPI.
No contiene lógica de scoring — solo traduce los datos de la BD al formato que el motor espera, llama al motor, y persiste los resultados.

```python
# app/services/emotional_scoring_service.py

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from emotional_health_engine import score_assessment, AssessmentResult
from sqlmodel import Session

def compute_and_save_scores(
    assessment_id: int,
    responses: dict,
    is_female: bool,
    db: Session
) -> AssessmentResult:
    """
    1. Agrupa las respuestas por módulo desde emotional_responses
    2. Llama a score_assessment() del motor
    3. Persiste en emotional_scores y emotional_checklist_selections
    4. Retorna AssessmentResult completo para el informe
    """
    ...
```

**Reglas de implementación:**
- Nunca mezclar scores de módulos distintos en este servicio
- Si `crisis_alert=True`, persistirlo inmediatamente (no esperar al final del flujo)
- Los checklists no clínicos van a `emotional_checklist_selections`, nunca a `emotional_scores`

---

## 🌐 FASE 3 — Rutas FastAPI (router)
**Duración estimada: 1.5 días | Dependencia: Fase 2 completa**

### Tarea 3.1 — Crear `app/routers/emotional_health.py`

Prefijo de todas las rutas: `/emotional-health/`

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/emotional-health/` | Landing + disclaimer |
| `POST` | `/emotional-health/start` | Crear `EmotionalAssessment`, marcar `disclaimer_accepted=True` |
| `GET` | `/emotional-health/quiz/{assessment_id}` | Cuestionario (bloque actual por query param) |
| `POST` | `/emotional-health/answer` | HTMX — guardar respuesta(s) de un bloque |
| `GET` | `/emotional-health/crisis` | Pantalla de recursos de crisis (RS-2) |
| `GET` | `/emotional-health/calculating/{assessment_id}` | Pantalla de carga |
| `POST` | `/emotional-health/score/{assessment_id}` | Invocar `emotional_scoring_service` |
| `GET` | `/emotional-health/report/{assessment_id}` | Informe en pantalla |
| `GET` | `/emotional-health/pdf/{token}` | Descargar PDF (WeasyPrint) |
| `POST` | `/emotional-health/send-email` | Enviar PDF por correo |

### Tarea 3.2 — Registrar el router en `app/main.py`

```python
from app.routers import emotional_health
app.include_router(emotional_health.router, prefix="", tags=["Salud Emocional"])
```

### Tarea 3.3 — Lógica crítica de seguridad en el endpoint de respuesta

El endpoint `POST /answer` debe, antes de retornar, evaluar el ítem 9 del PHQ-9:

```python
# Pseudocódigo — en el endpoint de respuesta a Bloque 1 (PHQ-9)
if module == "phq9" and item_id == 9 and raw_value > 0:
    # RS-1: marcar crisis_alert inmediatamente
    assessment.crisis_alert = True
    db.commit()
    # RS-2: redirigir a pantalla de crisis ANTES de continuar
    return RedirectResponse("/emotional-health/crisis?next=bloque2", status_code=303)
```

> ⚠️ **Esta lógica de redirección al ítem 9 es el requisito de mayor prioridad de todo el módulo.** Debe implementarse y probarse antes que cualquier otro endpoint.

---

## 🎨 FASE 4 — Plantillas HTML (Frontend)
**Duración estimada: 2 días | Dependencia: Fase 3 completa**

Reutilizar el sistema de diseño ya establecido en OCEAN-P (mismos tokens CSS, misma tipografía Outfit/Inter, mismo patrón HTMX). Las plantillas nuevas extienden `base.html`.

### Tarea 4.1 — `eh_landing.html` (Landing + Disclaimer)

Elementos obligatorios (RS-4):
- Explicación del módulo (qué es y qué NO es — lenguaje no diagnóstico RS-6)
- Bloque de disclaimer con fondo diferenciado
- **Checkbox de "he leído y entendido"** — no premarcado, obligatorio para habilitar el botón "Comenzar"
- Tiempo estimado: 15-18 minutos, número de bloques: 8

```html
<!-- Checkbox obligatorio — no puede omitirse ni premarcarse -->
<label class="disclaimer-check">
  <input type="checkbox" id="disclaimer-accepted" x-model="disclaimerChecked" />
  He leído y entendido que este resultado es una herramienta de cribado de apoyo,
  no un diagnóstico clínico.
</label>
<button :disabled="!disclaimerChecked" @click="startAssessment()">
  Comenzar cribado
</button>
```

### Tarea 4.2 — `eh_quiz.html` (Cuestionario — 8 bloques)

**Regla de diseño crítica (RF-1.2):** cada bloque declara su propia escala. El componente de escala recibe los labels como parámetro, no los asume.

**Escalas por bloque (deben implementarse como variables, no hardcodeadas):**

| Bloque | Instrumento | Escala | Ventana temporal |
|---|---|---|---|
| 1a | PHQ-9 | 0=Ningún día · 1=Varios días · 2=Más de la mitad · 3=Casi todos | 2 semanas |
| 1b | WHO-5 | 0=Nunca · 1=Alguna vez · 2=Menos de la mitad · 3=Más de la mitad · 4=Casi siempre · 5=Siempre | 2 semanas |
| 2 | PHQ-15 | 0=Nada molesto · 1=Un poco molesto · 2=Mucho molesto | **4 semanas** ⚠️ |
| 3 | Checklist cognitivo | Sí / No (checkboxes, sin puntaje) | — |
| 4 | Checklist conductual | Sí / No (checkboxes, sin puntaje) | — |
| 5a | GAD-7 | 0=Ningún día · 1=Varios días · 2=Más de la mitad · 3=Casi todos | 2 semanas |
| 5b | Irritabilidad | Sí / No (checkboxes, sin puntaje) | — |
| 6 | Rosenberg | 0=Muy en desacuerdo · 1=En desacuerdo · 2=De acuerdo · 3=Muy de acuerdo | — |
| 7 | Sueño | 0=Ningún día · 1=Varios días · 2=Más de la mitad · 3=Casi todos | 2 semanas |
| 8 | Contexto | Opción múltiple (sin puntaje) | — |

> ⚠️ **El PHQ-15 usa ventana de 4 semanas, no 2.** Este texto debe aparecer explícitamente en pantalla para el bloque 2. Es un error de diseño frecuente ignorarlo.

Otros elementos obligatorios en el quiz:
- Header de cada bloque con nombre, número de ítems y ventana de tiempo
- Etiqueta de validación: `"Instrumento clínico validado"` / `"Observación descriptiva"` (RF-3.11)
- Barra de progreso por bloque: `"Bloque 3 de 8"` (RF-1.5)
- Guardado de progreso en `localStorage` (RF-1.4) — igual que OCEAN-P

### Tarea 4.3 — `eh_crisis.html` (Pantalla de Alerta de Crisis)

Esta es la plantilla de mayor prioridad de todo el módulo (RS-2).

Elementos obligatorios:
- No puede cerrarse sin que el usuario vea al menos una opción de contacto
- Cargar recursos desde la BD (`crisis_resources`) — **nunca hardcodeados** (RS-3)
- Tono: cálido, no alarmista. Ejemplo: *"Gracias por compartir esto. Hay personas disponibles para escucharte ahora mismo."*
- Botón "Continuar con el cribado" — el usuario puede seguir (RS-2: la alerta no bloquea, pero se antepone)
- Si no hay recursos en la BD para el país del usuario: mostrar mensaje genérico de búsqueda de ayuda profesional (nunca una pantalla vacía)

### Tarea 4.4 — `eh_report.html` (Informe en pantalla)

**Orden obligatorio de secciones (RF-3.1):**

1. **[Condicional] Alerta de ayuda profesional** — si PHQ-9 ≥ 15 o GAD-7 ≥ 15 (RS-5). Separada visualmente, no como texto inline.
2. PHQ-9 + interpretación conjunta con WHO-5 (RF-3.3)
3. PHQ-15 — síntomas somáticos con banda de severidad
4. Checklist cognitivo — lista descriptiva, **sin número** (RF-3.5)
5. Checklist conductual — lista descriptiva, sin número
6. GAD-7 + checklist de irritabilidad como observación complementaria
7. Rosenberg — autoestima con interpretación
8. Sueño — etiquetado como "estimación no clínica"
9. Contexto — resumen cualitativo sin puntaje
10. **Disclaimer siempre visible** (RS-4) — bloque destacado, no un footer pequeño
11. Botón "Descargar PDF" + campo de email

**Etiquetas de validación obligatorias (RF-3.11):**
```html
<!-- Para instrumentos validados -->
<span class="badge-validated">✓ Instrumento clínico validado</span>

<!-- Para checklists propios -->
<span class="badge-descriptive">○ Observación descriptiva — no es una escala clínica</span>
```

### Tarea 4.5 — `eh_report_pdf.html` (Plantilla PDF WeasyPrint)

Igual que `report.html` del OCEAN-P pero adaptado al contenido emocional.

Obligatorio en el PDF (RF-4.1):
- Disclaimer siempre presente
- Si `professional_help_recommended=True`: sección de recomendación explícita
- Si `crisis_alert=True`: incluir recursos de crisis en el PDF (RF-5.1)

---

## 📧 FASE 5 — Email con recursos de crisis
**Duración estimada: 0.5 día | Dependencia: Fase 4 completa**

### Tarea 5.1 — Modificar el servicio de email existente

En el servicio de envío de email (Resend/SendGrid), agregar lógica condicional:

```python
# En el servicio de envío de email
if assessment_result.crisis_alert:
    # RF-5.1: incluir bloque de recursos de crisis en el email
    crisis_resources = get_active_resources(country_code, db)
    email_body = render_email_with_crisis(assessment_result, crisis_resources)
else:
    email_body = render_email_standard(assessment_result)
```

---

## ✅ FASE 6 — Tests y Criterios de Aceptación
**Duración estimada: 1 día | Dependencia: Fases 1-5 completas**

### Tarea 6.1 — Tests de seguridad (prioridad máxima)

Crear `tests/test_emotional_security.py`:

```python
def test_crisis_alert_activates_immediately():
    """RS-1: el ítem 9 > 0 activa crisis_alert aunque el total sea mínimo."""
    # Replica el Caso C del motor

def test_crisis_screen_shown_before_test_completion():
    """RS-2: la redirección ocurre al responder el ítem 9, no al final."""

def test_disclaimer_required_before_start():
    """RS-4: POST /start sin disclaimer_accepted=True devuelve error 422."""

def test_professional_help_shown_in_severe_cases():
    """RS-5: PHQ-9 >= 15 → professional_help_recommended=True en el informe."""

def test_no_diagnostic_language_in_templates():
    """RS-6: buscar 'tienes depresión', 'diagnóstico', 'estás diagnosticado' en templates."""
```

### Tarea 6.2 — Tests de scoring

Crear `tests/test_emotional_scoring.py`:

```python
def test_checklists_not_in_emotional_scores():
    """RF-2.4: los checklists no generan filas en emotional_scores."""

def test_modules_never_combined():
    """RF-2.2: emotional_scores tiene una fila por módulo, nunca un total global."""

def test_phq15_excludes_item_15_for_males():
    """RF-1: ítem 15 no aparece ni se suma para is_female=False."""
```

### Tarea 6.3 — Checklist manual de Definition of Done

Antes de considerar el módulo listo para producción, verificar **cada punto**:

- [ ] Caso C del motor pasa: `crisis_alert=True` con ítem 9 > 0 y total mínimo
- [ ] Pantalla de crisis aparece **antes** de completar el resto del test
- [ ] Disclaimer en 2 puntos obligatorios (inicio + resultado) — ninguno evitable
- [ ] Ningún texto de la interfaz usa lenguaje diagnóstico ("tienes depresión", "estás diagnosticado")
- [ ] Los 8 módulos se presentan y calculan por separado, nunca combinados
- [ ] Checklists sin puntaje numérico — solo lista descriptiva
- [ ] Cada resultado indica visualmente si proviene de instrumento validado o no (RF-3.11)
- [ ] `crisis_resources` tiene al menos 1 recurso verificado (bloqueante — sección 10 del PRD)
- [ ] Revisión por profesional de salud mental antes de producción (bloqueante — RS-7)

---

## 📅 Cronograma resumido

| Fase | Descripción | Días est. | Dependencia |
|---|---|---|---|
| **Fase 0** | Seguridad primero (ítems checklists + verificar Caso C) | 1 día | — |
| **Fase 1** | Modelo de datos + migración Alembic (5 tablas nuevas) | 1 día | Fase 0 |
| **Fase 2** | Servicio adaptador `emotional_scoring_service.py` | 0.5 días | Fase 1 |
| **Fase 3** | Rutas FastAPI + lógica crítica RS-2 (ítem 9) | 1.5 días | Fase 2 |
| **Fase 4** | 5 plantillas HTML (landing, quiz, crisis, report, PDF) | 2 días | Fase 3 |
| **Fase 5** | Email condicional con recursos de crisis | 0.5 días | Fase 4 |
| **Fase 6** | Tests + DoD checklist | 1 día | Fase 5 |
| **Total** | | **~7.5 días** | |

> **Pendientes bloqueantes no técnicos (no se resuelven con código — sección 10 del PRD):**
> 1. Cargar `crisis_resources` con líneas de ayuda verificadas del país de lanzamiento
> 2. Revisión del contenido por profesional de salud mental (RS-7)
> 3. Verificación de cumplimiento normativo local para herramientas de cribado digital
> 4. Política de privacidad específica para datos de salud mental
> 5. Confirmación de licencias de uso de PHQ-15, WHO-5 y Rosenberg para uso comercial

---

## ⚠️ Reglas de implementación permanentes

Estas reglas aplican a **todo el código del módulo**, sin excepción:

1. **Nunca mezclar puntajes** — `AssessmentResult` tiene 6 campos separados. Nunca se suman en un total global.
2. **Crisis primero** — cualquier endpoint que procese respuestas del PHQ-9 debe verificar el ítem 9 antes de hacer cualquier otra cosa.
3. **Checklists = listas, no números** — `cognitive_checklist`, `behavioral_checklist` e `irritability_checklist` nunca generan un `total_score`. Van a `emotional_checklist_selections`, no a `emotional_scores`.
4. **Recursos desde BD** — los contactos de crisis se leen de `crisis_resources`, nunca del código o templates (RS-3).
5. **Lenguaje no diagnóstico** — revisar cada string antes de commit. "Tus respuestas sugieren..." ≠ "Tienes...".
6. **El motor no se modifica** — `emotional_health_engine.py` ya está completo y probado. Se importa, no se edita (excepción: agregar los 3 bancos de ítems de checklists, Tarea 0.1).
