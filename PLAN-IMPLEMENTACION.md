# 🧠 Plan de Implementación — Test de Personalidad OCEAN-P
## Versión 1.0 | Basado en PRD v1.0

---

> **IMPORTANTE:** Este plan cubre **Fase 1 (MVP)** y **Fase 2 (Exportación)** del PRD. El modelo de datos se diseña completo desde el día 1 para no requerir migraciones estructurales en Fase 3.

---

## 📐 Stack Tecnológico Confirmado

| Capa | Tecnología | Justificación |
|---|---|---|
| **Backend** | Python 3.12 + FastAPI | Async, tipado, OpenAPI automático; reutiliza `scoring_engine.py` |
| **Frontend** | Jinja2 + HTMX + Alpine.js + Tailwind CSS (CDN) | Sin Node.js, sin build step, sin segundo lenguaje |
| **ORM / DB** | SQLModel + PostgreSQL | SQLModel = tipado Python nativo compatible con FastAPI |
| **PDF** | WeasyPrint | 100% Python, reutiliza plantilla Jinja2 del informe |
| **Email** | Resend SDK (Python) | Plan gratuito suficiente para MVP, entregabilidad premium |
| **Hosting** | Railway | Deploy automático desde repo, PostgreSQL incluido |
| **Almacenamiento PDFs** | Railway Volume + URLs firmadas (token UUID v4) | Cumple RF-4.5 (no URL predecible) |
| **Animations (Frontend)** | Anime.js (CDN) | Micro-interacciones premium: stagger, spring, timeline |
| **Fonts** | Google Fonts — "Outfit" + "Inter" | Tipografía moderna, legibilidad psicométrica |

---

## 🎨 Sistema de Diseño (Design System OCEAN-P)

> Aplicando skills: **design-spells**, **animejs-animation**, **ui-ux-designer**

### Paleta de colores (tokens CSS)
```css
/* Identidad visual: científico pero cálido, premium oscuro */
--color-bg:            #0D0F1A;   /* Fondo principal — azul noche profundo */
--color-surface:       #161929;   /* Cards y paneles */
--color-surface-raised:#1E2235;   /* Hover de cards */
--color-border:        rgba(255,255,255,0.08);
--color-accent-ocean:  #5B8DEF;   /* Openness — azul índigo */
--color-accent-cons:   #4ECDC4;   /* Conscientiousness — teal */
--color-accent-extra:  #FFD93D;   /* Extraversion — ámbar cálido */
--color-accent-agree:  #6BCB77;   /* Agreeableness — verde esmeralda */
--color-accent-neuro:  #FF6B6B;   /* Neuroticism — coral */
--color-text-primary:  #F0F2FF;
--color-text-secondary:#8892B0;
--color-glow:          rgba(91,141,239,0.15);
```

### Design Spells aplicados
1. **Barra de progreso magnética** — avanza con animación spring, no transición lineal genérica
2. **Opciones Likert con efecto ripple** — al seleccionar, el botón emite una onda de color desde el punto de clic
3. **Loader de cálculo de perfil** — SVG morphing animado con Anime.js (5 anillos OCEAN rotantes)
4. **Gráfico de dimensiones** — barras que se "llenan" con stagger escalonado al entrar en viewport
5. **Hover magnético en CTA** — el botón "Comenzar test" sigue sutilmente el cursor (±8px)
6. **Checkmark animado** — al confirmar envío de email, SVG de check se dibuja con stroke-dashoffset
7. **Reveal de texto staggered** — headline de landing se revela letra por letra con Anime.js

### Tipografía
```
Headings: "Outfit" 700/800 — impacto psicológico, identidad de marca
Body:      "Inter" 400/500 — máxima legibilidad en ítems del test
Mono:      "JetBrains Mono" — puntuaciones y percentiles (credibilidad)
```

---

## 🗂️ Estructura del Proyecto

```
ocean-p/
├── app/
│   ├── main.py                    # FastAPI entry point + routers
│   ├── config.py                  # Settings (env vars, DB URL, Resend API key)
│   ├── database.py                # SQLModel engine + session factory
│   │
│   ├── models/                    # SQLModel table definitions
│   │   ├── __init__.py
│   │   ├── session.py             # TestSession, User
│   │   ├── response.py            # ItemResponse
│   │   ├── score.py               # Score (facet/dimension/index/validity)
│   │   ├── report.py              # Report
│   │   ├── delivery.py            # EmailDelivery
│   │   └── norm_table.py          # NormTable (versionada)
│   │
│   ├── routers/
│   │   ├── quiz.py                # GET /quiz, POST /quiz/response, POST /quiz/submit
│   │   ├── report.py              # GET /report/{session_id}
│   │   ├── pdf.py                 # POST /report/{session_id}/pdf
│   │   └── email.py               # POST /report/{session_id}/email
│   │
│   ├── services/
│   │   ├── scoring_engine.py      # Motor: facetas, dimensiones, índices, validez
│   │   ├── pdf_service.py         # WeasyPrint PDF generation
│   │   ├── email_service.py       # Resend SDK integration
│   │   └── norm_service.py        # Conversión raw → percentil (tabla normativa)
│   │
│   ├── data/
│   │   ├── items.json             # 65 ítems + metadatos (faceta, dirección R/N)
│   │   ├── interpretations.json   # Textos narrativos por dimensión/faceta/percentil
│   │   └── norms_v1.json          # Tabla normativa inicial (fórmula lineal)
│   │
│   └── templates/                 # Jinja2 templates
│       ├── base.html              # Layout base con Design System
│       ├── landing.html           # Pantalla 1: Landing
│       ├── instructions.html      # Pantalla 2: Instrucciones + privacidad
│       ├── quiz.html              # Pantalla 3: Cuestionario HTMX
│       ├── calculating.html       # Pantalla 4: Loader "Calculando perfil..."
│       ├── report.html            # Pantalla 5: Informe interactivo
│       └── report_pdf.html        # Template específico para PDF (A4, sin JS)
│
├── tests/
│   ├── test_scoring.py            # Unit tests del motor de scoring
│   ├── test_validity.py           # Unit tests de escalas de validez
│   └── test_norm.py               # Unit tests conversión percentil
│
├── migrations/                    # Alembic migrations
├── .env.example
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## 📋 Fases de Implementación

---

### 🔴 FASE 1 — MVP (Semanas 1–3)

---

#### Semana 1 — Fundación: Proyecto + DB + Cuestionario

**Objetivo:** Un usuario puede abrir la app, responder los 65 ítems y que las respuestas queden guardadas en PostgreSQL.

##### Tareas Backend

- [ ] **T1.1** Inicializar proyecto FastAPI con estructura de directorios
- [ ] **T1.2** Configurar SQLModel + Alembic; crear TODAS las tablas del modelo de datos (incluyendo las de Fase 2 y 3 para no romper migraciones futuras)
- [ ] **T1.3** Crear `items.json` con los 65 ítems: `{id, text, facet, dimension, reverse_scored: bool, block}`
- [ ] **T1.4** Endpoint `POST /sessions` — crea nueva `test_session` con UUID v4
- [ ] **T1.5** Endpoint `POST /sessions/{session_id}/responses` — guarda respuesta individual con `response_time_ms`
- [ ] **T1.6** Endpoint `GET /sessions/{session_id}/state` — retorna respuestas guardadas (restaurar progreso desde localStorage)

##### Tareas Frontend

- [ ] **T1.7** Crear `base.html` con Design System completo:
  - CSS custom properties (tokens de color, spacing, tipografía)
  - Google Fonts: Outfit + Inter vía `<link>`
  - Anime.js vía CDN
  - Alpine.js vía CDN
  - HTMX vía CDN
  - Tailwind CSS vía Play CDN

- [ ] **T1.8** `landing.html` — **Design Spell: "Hover magnético"**
  - Fondo: gradiente radial animado (azul noche → añil profundo)
  - Headline: texto con reveal letra por letra (Anime.js stagger)
  - CTA "Comenzar test": hover magnético (texto sigue cursor ±8px)
  - Subheadline con descripción y número de preguntas

- [ ] **T1.9** `instructions.html`
  - Cards de información (tiempo estimado, propósito, privacidad)
  - Aviso de retención: "Los resultados se conservan 90 días sin cuenta asociada"
  - Enlace a política de privacidad

- [ ] **T1.10** `quiz.html` — **Design Spells: "Ripple en Likert" + "Barra magnética"**
  - HTMX: `hx-post` por ítem, avanza sin reload completo
  - Alpine.js: estado local del ítem actual, navegación atrás
  - localStorage: backup del `session_id` y respuestas
  - Barra de progreso con animación spring (Anime.js)
  - Escala Likert: 5 botones con etiquetas en extremos; selección → efecto ripple
  - Botón "Anterior" visible después del ítem 1
  - Indicador: "15 de 65"

**Criterio de aceptación S1:** Las 65 respuestas aparecen en PostgreSQL. El progreso sobrevive un refresh (localStorage + restauración desde `/state`).

---

#### Semana 2 — Motor de Scoring

**Objetivo:** El backend calcula correctamente facetas, dimensiones, índices y escalas de validez.

##### Tareas Backend

- [ ] **T2.1** Implementar `scoring_engine.py`:
  - `invert_items(responses)` — invierte ítems marcados `reverse_scored=True`
  - `calculate_facets(responses)` → dict de 15 facetas (promedio 1-5)
  - `calculate_dimensions(facets)` → dict de 5 dimensiones (promedio de facetas)
  - `calculate_professional_indices(facets, dimensions)` → 4 índices compuestos
  - `calculate_validity_scales(responses, timing)` → 3 escalas + alertas

- [ ] **T2.2** Implementar `norm_service.py`:
  - `raw_to_percentile(scope_key, raw_score, version="v1")` → consulta `norm_tables` activa
  - Tabla normativa inicial: fórmula lineal simplificada, etiquetada como "versión inicial"

- [ ] **T2.3** Endpoint `POST /sessions/{session_id}/calculate`:
  1. Valida que existan las 65 respuestas
  2. Ejecuta scoring_engine
  3. Persiste en tabla `scores`
  4. Genera `reports` con `archetype_label`
  5. Actualiza `status = "completed"` o `"invalid"` (si ≥2 alertas de validez)
  6. Retorna `{report_id, status, archetype_label}`

- [ ] **T2.4** Lógica de `archetype_label` basada en combinación de dimensiones dominantes

##### Tareas de Testing

- [ ] **T2.5** `tests/test_scoring.py` — 5 casos de prueba calculados manualmente:
  - Caso "todas máximas": todos ítems = 5
  - Caso "todas mínimas": todos ítems = 1
  - Caso "invertido": verifica inversión de ítems R
  - Caso "validez baja": respuestas erráticas activan ≥2 alertas
  - Caso "validez alta": respuestas coherentes no activan alertas

- [ ] **T2.6** `tests/test_norm.py` — percentiles en rango 1-99 para todos los scope_keys

**Criterio de aceptación S2:** `pytest tests/` al 100%. Motor validado con 3+ casos calculados a mano.

---

#### Semana 3 — Informe en Pantalla

**Objetivo:** El usuario ve su informe completo con visualizaciones animadas.

##### Tareas Backend

- [ ] **T3.1** Endpoint `GET /report/{session_id}` — renderiza `report.html` con:
  - `archetype_label`, fecha, resumen narrativo por dimensión
  - 5 puntuaciones de dimensión (con percentil)
  - 15 puntuaciones de faceta (con descripción conductual)
  - 4 índices profesionales
  - Estado de validez (aviso si `status = "invalid"`)

- [ ] **T3.2** Crear `interpretations.json`:
  - Texto descriptivo para percentil bajo (<35), medio (35-65) y alto (>65)
  - Descripción conductual concreta para cada faceta

##### Tareas Frontend

- [ ] **T3.3** `calculating.html` — **Design Spell: "Loader de personalidad"**
  - SVG animado con Anime.js: 5 anillos concéntricos que rotan a velocidades distintas
  - Texto que cambia cada 1.5s: "Analizando apertura…", "Calculando responsabilidad…", etc.
  - Auto-redirect a `/report/{session_id}` después de completar

- [ ] **T3.4** `report.html` — **Design Spells: "Gráfico animado" + "Scroll reveal escalonado"**
  - Header: arquetipo con reveal de texto staggered (Anime.js)
  - Sección dimensiones: 5 barras de percentil animadas al entrar en viewport (IntersectionObserver + Anime.js), color único por dimensión
  - Sección facetas: cards que aparecen con stagger al hacer scroll (translateY + opacity)
  - Sección índices: 4 tarjetas con icono, nombre y puntuación; hover con glow
  - Aviso de validez: banner prominente con "Resultado no concluyente" y botón "Repetir test"
  - CTA exportación: botones "Descargar PDF" y campo de email (funcionales en Fase 2)

**Criterio de aceptación S3:** Flujo completo funciona. Informe coincide matemáticamente con las fórmulas del motor de scoring.

---

### 🟡 FASE 2 — Exportación (Semanas 4–5)

---

#### Semana 4 — Generación de PDF

**Objetivo:** El botón "Descargar PDF" genera un PDF en < 5 segundos.

##### Tareas Backend

- [ ] **T4.1** Crear `report_pdf.html` — versión A4 del informe para WeasyPrint:
  - Sin JavaScript (WeasyPrint no ejecuta JS)
  - CSS específico para impresión: page-break, márgenes A4
  - Gráfico de dimensiones como SVG estático
  - Incluye: nombre del test, fecha, resumen, gráfico, facetas, índices, aviso de validez

- [ ] **T4.2** `pdf_service.py`:
  - `generate_pdf(session_id, report_data)` → WeasyPrint → bytes
  - Guardar PDF con nombre `{uuid_token_nuevo}.pdf` (UUID v4, distinto al session_id)
  - Actualizar `pdf_url` en tabla `reports`

- [ ] **T4.3** Endpoint `POST /report/{session_id}/pdf`:
  - Si `pdf_url` ya existe → retorna URL existente (caché)
  - Si no → ejecuta como `BackgroundTasks` de FastAPI
  - Retorna `{url, expires_at}`

- [ ] **T4.4** Endpoint `GET /files/{token}`:
  - Verifica token existe y no expiró
  - Retorna archivo con `Content-Disposition: attachment`
  - Nunca expone session_id ni IDs incrementales

**Criterio de aceptación S4:** PDF generado en <5s, A4 correcto, URL no predecible, caché funciona.

---

#### Semana 5 — Envío por Correo

**Objetivo:** El usuario puede recibir el informe en su email con consentimiento explícito.

##### Tareas Backend

- [ ] **T5.1** `email_service.py`:
  - `send_report_email(to_email, pdf_url, expires_at)` usando Resend SDK
  - Template HTML del email: enlace de descarga con expiración de 7 días (no adjunto)

- [ ] **T5.2** Endpoint `POST /report/{session_id}/email`:
  - Validar formato de email (Pydantic EmailStr)
  - Verificar `consent: true` en el payload (validado en backend, no solo frontend)
  - Llamar a `email_service.send_report_email()`
  - Registrar en `email_deliveries`: `{session_id, email_hash SHA-256, sent_at, status}`
  - Retornar `{success: bool, message: str}`

##### Tareas Frontend

- [ ] **T5.3** Actualizar `report.html` — sección de email funcional:
  - Validación en tiempo real con Alpine.js
  - Checkbox de consentimiento NO premarcado, texto legal claro
  - Botón "Enviarme una copia" habilitado solo cuando email válido + checkbox marcado
  - HTMX: envío sin reload, confirmación/error en contexto
  - **Design Spell: "Estado de éxito animado"** — checkmark SVG se dibuja con stroke-dashoffset (Anime.js)

**Criterio de aceptación S5:** Correo solo se envía con consentimiento. Llega a inbox (no spam). Hash del email guardado, no texto plano.

---

### 🟢 FASE 3 (Post-MVP) — Referencia Futura

> No implementar ahora. El modelo de datos ya lo soporta desde Fase 1.

- Tests complementarios (7 listados en documento de diseño)
- Microrretos diarios + seguimiento de progreso
- Certificación / insignias
- Panel de administración con analítica agregada (anónima)
- Sistema de autenticación (cuentas opcionales)

---

### Semana 6 — QA, Piloto y Despliegue

- [ ] **T6.1** Pruebas end-to-end: Chrome, Firefox, Safari Mobile
- [ ] **T6.2** Prueba de rendimiento: informe ≤3s, PDF ≤5s
- [ ] **T6.3** Piloto interno: 20-30 personas, validar resultados manualmente
- [ ] **T6.4** Ajuste de tabla normativa con datos reales del piloto
- [ ] **T6.5** Configurar dominio + HTTPS + SPF/DKIM para Resend
- [ ] **T6.6** Despliegue en Railway: env vars, PostgreSQL, volumen para PDFs
- [ ] **T6.7** Monitoreo básico: Railway logs + alertas si `email_deliveries.status = "failed"`

---

## 🔒 Checklist de Seguridad y Privacidad (sección 8 PRD)

- [ ] HTTPS obligatorio (Railway lo provee automáticamente)
- [ ] Nunca usar IDs incrementales en URLs públicas (siempre UUID v4)
- [ ] Email almacenado solo como hash SHA-256 en `email_deliveries`
- [ ] Checkbox de consentimiento no premarcado (validado en backend también)
- [ ] Política de retención: 90 días → anonimización automática
- [ ] Política de privacidad visible en `instructions.html` antes de empezar
- [ ] PDFs servidos con token único, no URL predecible
- [ ] Variables de entorno: API keys nunca en el código fuente

---

## ⚡ Design Spells — Código de Implementación

### 1. Hover Magnético en CTA (landing.html)
```javascript
// Alpine.js + Anime.js — botón sigue el cursor ±8px
document.querySelector('#cta-button').addEventListener('mousemove', (e) => {
  const rect = e.target.getBoundingClientRect();
  const x = e.clientX - rect.left - rect.width / 2;
  const y = e.clientY - rect.top - rect.height / 2;
  anime({
    targets: '#cta-button',
    translateX: x * 0.15,
    translateY: y * 0.15,
    duration: 300,
    easing: 'easeOutElastic(1, .6)'
  });
});
document.querySelector('#cta-button').addEventListener('mouseleave', () => {
  anime({ targets: '#cta-button', translateX: 0, translateY: 0, duration: 400, easing: 'spring(1, 80, 10, 0)' });
});
```

### 2. Ripple en Escala Likert (quiz.html)
```javascript
document.querySelectorAll('.likert-option').forEach(btn => {
  btn.addEventListener('click', function(e) {
    const ripple = document.createElement('span');
    ripple.className = 'ripple-effect';
    this.appendChild(ripple);
    anime({
      targets: ripple,
      scale: [0, 4],
      opacity: [0.6, 0],
      duration: 600,
      easing: 'easeOutExpo',
      complete: () => ripple.remove()
    });
  });
});
```

### 3. Gráfico de Dimensiones Animado (report.html)
```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      anime({
        targets: entry.target.querySelectorAll('.dimension-bar-fill'),
        width: (el) => el.dataset.percentile + '%',
        duration: 1200,
        delay: anime.stagger(150),
        easing: 'spring(1, 80, 10, 0)'
      });
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.3 });
document.querySelectorAll('.dimensions-chart').forEach(el => observer.observe(el));
```

### 4. Loader SVG Animado (calculating.html)
```javascript
// 5 anillos = 5 dimensiones OCEAN
const tl = anime.timeline({ loop: true });
['#ring-O','#ring-C','#ring-E','#ring-A','#ring-N'].forEach((ring, i) => {
  tl.add({
    targets: ring,
    rotate: i % 2 === 0 ? 360 : -360,
    duration: 2000 + i * 400,
    easing: 'linear'
  }, 0);
});
```

### 5. Checkmark de Éxito (report.html — confirmación email)
```javascript
anime({
  targets: '#success-checkmark path',
  strokeDashoffset: [anime.setDashoffset, 0],
  easing: 'easeInOutSine',
  duration: 700,
  delay: 200
});
```

---

## 📊 Métricas de Éxito a Monitorear

| Métrica | Cómo medir | Meta |
|---|---|---|
| Tasa de finalización | `completed_at IS NOT NULL / started_at IS NOT NULL` | ≥ 70% |
| Tests "no concluyente" | `status = 'invalid' / total` | ≤ 15% |
| % que exportan | `pdf_url IS NOT NULL OR email status='sent'` / completados | ≥ 50% |
| Tiempo de informe | `completed_at - last_response_time` | ≤ 3s |
| Tiempo de PDF | Logging con `time.perf_counter()` en `pdf_service.py` | ≤ 5s |
| Entregabilidad email | `email_deliveries.status = 'sent' / total` | ≥ 98% |
| Abandono por ítem | `COUNT(responses) GROUP BY item_id WHERE session in_progress` | Identificar ítem crítico |

---

## 📁 Estructura de Datos Clave

### `items.json` — estructura de ítem
```json
{
  "id": 1,
  "text": "Me considero una persona curiosa intelectualmente.",
  "facet": "apertura_ideas",
  "dimension": "openness",
  "reverse_scored": false,
  "block": 1
}
```

### `norms_v1.json` — tabla normativa inicial
```json
{
  "version": "v1",
  "description": "Tabla normativa inicial — fórmula lineal simplificada. Recalibrar con datos reales tras 200+ respuestas.",
  "dimensions": {
    "openness":          {"mean": 3.5, "sd": 0.7},
    "conscientiousness": {"mean": 3.4, "sd": 0.6},
    "extraversion":      {"mean": 3.2, "sd": 0.8},
    "agreeableness":     {"mean": 3.6, "sd": 0.6},
    "neuroticism":       {"mean": 2.8, "sd": 0.9}
  }
}
```

---

## ✅ Definition of Done — Checklist Final

### MVP (Fase 1)
- [ ] Usuario completa test de inicio a fin sin perder progreso ante refresh
- [ ] Informe en pantalla coincide matemáticamente con clave de corrección del documento de diseño
- [ ] Test con ≥2 alertas de validez muestra aviso "no concluyente" y botón "Repetir test"
- [ ] `pytest tests/` pasa al 100%
- [ ] Tabla normativa actualizable sin tocar código del motor de scoring

### Fase 2 (Exportación)
- [ ] PDF generado correctamente en < 5 segundos
- [ ] Envío por correo solo ocurre tras consentimiento explícito
- [ ] Confirmación de éxito/fallo visible al usuario
- [ ] Ningún PDF ni informe accesible mediante URL adivinable
- [ ] Email almacenado como hash SHA-256, no en texto plano

### Calidad Frontend
- [ ] Responsive: funciona en móvil (375px) y escritorio (1280px+)
- [ ] Animaciones a 60fps, sin layout shifts (Lighthouse CLS < 0.1)
- [ ] Contraste WCAG AA en todos los textos
- [ ] Test completable 100% con teclado

---

## 🚀 Próximos Pasos Inmediatos

1. Crear repositorio `ocean-p` en GitHub (privado hasta lanzamiento)
2. Inicializar proyecto FastAPI con la estructura de directorios definida
3. Crear base de datos PostgreSQL en Railway y conectar con SQLModel
4. Construir `items.json` con los 65 ítems del documento de diseño OCEAN-P
5. Implementar el cuestionario (RF-1) como primera feature visible al usuario
6. Validar el motor de scoring (RF-2) con 3-5 casos de prueba manuales antes de avanzar

---

*Generado: 2026-06-30 | Basado en PRD-test-personalidad-OCEAN-P.md v1.0*
*Skills aplicadas: ui-ux-designer, design-spells, animejs-animation*
