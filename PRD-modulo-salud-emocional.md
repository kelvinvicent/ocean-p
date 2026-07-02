# PRD — Módulo de Salud Emocional (Depresión y Ansiedad)
## Product Requirements Document v1.0
### Extensión del proyecto de Test de Personalidad OCEAN-P

---

## 1. Resumen del producto

**Qué es:** un módulo nuevo dentro de la plataforma existente, que ofrece un cribado de apoyo amplio de síntomas depresivos, ansiosos, somáticos, cognitivos, conductuales y de autoestima, organizado en 6 bloques temáticos + 2 módulos complementarios (sueño y contexto de vida). Cada bloque usa el instrumento validado más adecuado a lo que mide, o —cuando no existe un instrumento clínico corto y de uso libre para ese contenido— un checklist explícitamente etiquetado como **no clínico**.

**Qué NO es (esto debe quedar explícito en todo el producto):** no es un instrumento de diagnóstico, no reemplaza una evaluación clínica, y no debe presentarse en ningún punto del flujo como si lo fuera. Tampoco es una acumulación de preguntas redactadas de múltiples formas sobre un mismo síntoma — cada bloque aporta información distinta, no repetida con otro tono.

**Cómo se integra al proyecto existente:** vive dentro de la misma aplicación FastAPI del test OCEAN-P, como un segundo tipo de `assessment`, reutilizando la misma infraestructura (base de datos, generación de PDF, envío de correo) definida en el PRD anterior.

**Total de preguntas: 78** (77 en usuarios hombres, ya que 1 ítem del PHQ-15 aplica solo a mujeres). Tiempo estimado: 15-18 minutos.

**Los 8 módulos y su fundamento:**

| # | Bloque temático (tu diseño original) | Instrumento usado | Ítems | ¿Validado clínicamente? |
|---|---|---|---|---|
| 1 | Síntomas emocionales centrales | PHQ-9 + WHO-5 | 9 + 5 = 14 | Sí, ambos |
| 2 | Síntomas físicos y somáticos | PHQ-15 | 15 (14 en hombres) | Sí |
| 3 | Funciones cognitivas y mentales | Checklist de niebla mental (diseño propio) | 8 | No — etiquetado como tal |
| 4 | Comportamiento y apatía | Checklist conductual (diseño propio) | 8 | No — etiquetado como tal |
| 5 | Ansiedad comórbida e irritabilidad | GAD-7 + checklist de irritabilidad | 7 + 4 = 11 | GAD-7 sí, checklist no |
| 6 | Autoestima, culpa y pensamientos oscuros | Escala de Autoestima de Rosenberg | 10 | Sí |
| 7 | Calidad de sueño *(módulo complementario ya existente)* | Escala breve no clínica | 4 | No — etiquetado como tal |
| 8 | Contexto de vida *(módulo complementario ya existente)* | Checklist cualitativo, sin puntaje | 7 | No aplica (no se puntúa) |

**Nota importante sobre el Bloque 6:** los "pensamientos oscuros" (ideación de autolesión) **no se miden con ítems nuevos**. Esa señal ya está cubierta, de forma validada, por el ítem 9 del PHQ-9 (Bloque 1) — duplicarla con preguntas propias diluiría la fiabilidad de la alerta de crisis en vez de reforzarla (ver Requisito de Seguridad RS-1).

---

## 2. Por qué este PRD tiene una sección de "Requisitos de Seguridad" que el anterior no tenía

En el test de personalidad, el peor escenario de un error de diseño es un informe poco preciso. Aquí, el peor escenario es **no detectar una señal de riesgo real en una persona que la está expresando**. Por eso, antes de los requisitos funcionales normales, este PRD define **requisitos de seguridad con prioridad absoluta** — ningún requisito funcional (RF) puede implementarse de forma que contradiga un requisito de seguridad (RS).

---

## 3. Objetivos y métricas de éxito

| Objetivo | Métrica | Meta inicial |
|---|---|---|
| El cribado es completado | Tasa de finalización | ≥ 55% (baja frente a la versión anterior porque el test ahora es notablemente más largo —78 ítems— y el tema es sensible) |
| El usuario no abandona por fatiga a mitad del test | % de abandono concentrado en un bloque específico | Monitorear por bloque; si un bloque concentra >40% del abandono, revisar su longitud o redacción |
| Las alertas de crisis se muestran sin demora | Tiempo entre respuesta al ítem 9 y despliegue de recursos | Inmediato (sin esperar a terminar el test) |
| El usuario entiende que no es un diagnóstico | % que reconoce el disclaimer (medido con checkbox de confirmación) | 100% (es obligatorio, no opcional) |
| El usuario con severidad alta recibe recomendación de ayuda profesional | % de casos "moderadamente severa" o "severa" con mensaje de derivación mostrado | 100% |
| Entrega de correo/PDF | Igual que en el PRD de personalidad | ≥ 98% entregado |

---

## 4. Requisitos de Seguridad (RS) — máxima prioridad, se implementan primero

### RS-1: Detección de riesgo aislada del puntaje total
- El ítem 9 del PHQ-9 (ideación de autolesión) se evalúa de forma **independiente** a la suma total, en el mismo momento en que el usuario lo responde — no se espera a que termine el test completo.
- Cualquier valor > 0 en ese ítem activa `crisis_alert = True`, sin importar el resto de respuestas (ya validado en `emotional_health_engine.py`, Caso C).

### RS-2: Interrupción de flujo ante alerta de crisis
- Si `crisis_alert = True`, la aplicación debe mostrar una pantalla de recursos de ayuda **inmediatamente después de responder ese ítem**, no al final del test.
- Esta pantalla no debe poder cerrarse sin que el usuario haya visto al menos una opción de contacto (línea de crisis, chat, o similar).
- El usuario puede continuar el test después de ver esta pantalla — la alerta no bloquea el uso, pero sí se antepone.

### RS-3: Recursos de crisis configurables, no hardcodeados
- Los contactos de ayuda (líneas telefónicas, chats, webs oficiales) deben vivir en una tabla de configuración editable (`crisis_resources`), **no escritos directamente en el código o en las plantillas**.
- Razón: estos datos cambian con el tiempo y deben poder actualizarse sin un nuevo despliegue de código.
- Antes de producción: se debe cargar esta tabla con los recursos oficiales verificados del país/países donde se lanzará el producto (esto queda pendiente como tarea explícita — ver sección 10).

### RS-4: Disclaimer obligatorio, no evitable
- Debe mostrarse: (a) antes de iniciar el módulo, y (b) en el informe de resultados, siempre, sin excepción.
- Texto mínimo: *"Este resultado es una herramienta de cribado de apoyo y no constituye un diagnóstico clínico. Si tienes dudas sobre tu bienestar emocional, te recomendamos hablar con un profesional de salud mental."*
- El usuario debe marcar una casilla de "he leído y entendido" antes de comenzar (no premarcada).

### RS-5: Recomendación de ayuda profesional en severidad alta
- Si PHQ-9 ≥ 15 ("moderadamente severa" o "severa") o GAD-7 ≥ 15 ("severa"), el informe debe incluir una recomendación explícita de buscar apoyo profesional — separada visualmente del resto del informe, no como una línea más entre otras.

### RS-6: Lenguaje no diagnóstico en toda la interfaz
- Ninguna pantalla debe usar frases como "tienes depresión" o "estás diagnosticado con...". El lenguaje correcto es: "tus respuestas sugieren síntomas compatibles con..." — esta es una diferencia deliberada de redacción, no un detalle menor.

### RS-7: Revisión profesional antes de producción
- Antes de publicar este módulo a usuarios reales, se recomienda que el contenido (ítems, textos de resultado, recursos de crisis) sea revisado por un profesional de salud mental o psicólogo clínico, y que se verifique si existen requisitos regulatorios locales aplicables a herramientas de cribado de salud digital en el país de lanzamiento (esto varía por jurisdicción y debe confirmarse antes del lanzamiento, no asumirse).

---

## 5. Requisitos funcionales (RF)

### RF-1: Cuestionario
- RF-1.1: Mostrar los 78 ítems en 8 bloques (PHQ-9, WHO-5, PHQ-15, Checklist cognitivo, Checklist conductual, GAD-7, Checklist de irritabilidad, Rosenberg, Sueño, Contexto), cada uno con su propia instrucción de encabezado — incluyendo la ventana de tiempo correcta (la mayoría son "últimas 2 semanas", pero **PHQ-15 usa "últimas 4 semanas"**, y esto debe quedar explícito en pantalla para no confundir al usuario).
- RF-1.2: **Cada bloque declara su propia escala de respuesta — no existe una escala única reutilizable para todo el test.** El componente de UI del cuestionario debe recibir la escala como parámetro, no asumirla:
  - PHQ-9, GAD-7, Sueño, Checklist de irritabilidad → 0-3 (4 opciones, frecuencia en 2 semanas)
  - WHO-5 → 0-5 (6 opciones, frecuencia en 2 semanas)
  - PHQ-15 → 0-2 (3 opciones, "molestia" en 4 semanas)
  - Rosenberg → 0-3 (4 opciones, grado de acuerdo — no es frecuencia, es acuerdo)
  - Checklist cognitivo y conductual → opción múltiple simple, sin puntuación
  - Contexto → opción múltiple simple, sin puntuación
- RF-1.3: El ítem 9 del PHQ-9 debe evaluarse en el momento (ver RS-1), no solo al final.
- RF-1.4: Guardar progreso en cliente igual que en el test de personalidad (RF-1.4 del PRD anterior) — más importante aún con 78 ítems, ya que el riesgo de pérdida de progreso por un refresco accidental es mayor.
- RF-1.5: Mostrar una barra de progreso por bloque (ej. "Bloque 3 de 8"), no solo un porcentaje global — ayuda a que el usuario perciba avance tangible en un test largo.

### RF-2: Motor de scoring
- RF-2.1: Extender `emotional_health_engine.py` (no reescribirlo) agregando 3 funciones nuevas siguiendo el mismo patrón ya validado de `score_phq9()` y `score_gad7()`: `score_who5()`, `score_phq15()`, `score_rosenberg()`.
- RF-2.2: Los 8 módulos se calculan y presentan **siempre por separado**, nunca combinados en un solo puntaje (ver lección metodológica de la sesión de diseño — esto sigue siendo la regla central del proyecto).
- RF-2.3: Las bandas de severidad usan los puntos de corte oficiales de cada instrumento, sin modificación: PHQ-9, GAD-7, PHQ-15 y WHO-5 tienen puntos de corte publicados; Rosenberg usa el rango normal (15-25) documentado en la literatura.
- RF-2.4: Los checklists no clínicos (cognitivo, conductual, irritabilidad) **no generan un "puntaje"** — se procesan como lista de ítems marcados, para mostrarse en el informe como observaciones descriptivas, nunca como un número con apariencia de precisión clínica que no tienen.
- RF-2.5: Cada función de scoring debe incluir sus propios casos de prueba manuales (mismo patrón que `emotional_health_engine.py`), antes de conectarse al resto del sistema.

### RF-3: Informe en pantalla
- RF-3.1: Mostrar primero cualquier alerta de seguridad (RS-2, RS-5) si aplica, antes que el resto del contenido.
- RF-3.2: Mostrar resultado de PHQ-9 con severidad y descripción conductual.
- RF-3.3: Mostrar resultado de WHO-5 (bienestar), interpretado en conjunto con el PHQ-9 — ej. "tu bienestar general está reducido, lo cual es consistente con tu resultado de síntomas depresivos".
- RF-3.4: Mostrar resultado de PHQ-15 (síntomas somáticos) con severidad.
- RF-3.5: Mostrar los checklists cognitivo y conductual como listas descriptivas, **sin puntaje numérico** (ver RF-2.4) — ej. "Marcaste 5 de 8 señales de dificultad de concentración/memoria en las últimas semanas".
- RF-3.6: Mostrar resultado de GAD-7 con severidad, junto con el checklist de irritabilidad como observación complementaria (sin puntaje).
- RF-3.7: Mostrar resultado de Rosenberg (autoestima) con su interpretación (rango normal / bajo).
- RF-3.8: Mostrar resultado de sueño, etiquetado explícitamente como "estimación no clínica".
- RF-3.9: Mostrar resumen cualitativo del módulo de contexto (sin puntaje, como narrativa).
- RF-3.10: Incluir siempre el disclaimer (RS-4).
- RF-3.11: Cada resultado con instrumento validado debe indicar visualmente que lo es (ej. una pequeña etiqueta "Instrumento clínico validado"), y cada checklist no clínico debe indicar lo contrario (ej. "Observación descriptiva, no es una escala clínica") — esta distinción visual es un requisito, no un detalle estético, para que el usuario no interprete todo el informe con el mismo nivel de certeza.

### RF-4: Generación de PDF
- Igual que RF-4 del PRD de personalidad (WeasyPrint, misma plantilla, URL no predecible).
- RF-4.1 adicional: el PDF debe incluir el disclaimer y, si aplica, la recomendación de ayuda profesional — nunca se omiten en la versión descargable.

### RF-5: Envío por correo
- Igual que RF-5 del PRD de personalidad (consentimiento explícito, enlace con expiración).
- RF-5.1 adicional: si `crisis_alert = True`, el correo también debe incluir los recursos de ayuda, no solo el informe.

---

## 6. Modelo de datos (extiende el modelo del PRD de personalidad, no lo reemplaza)

```
emotional_assessments
├─ id
├─ session_id (FK → test_sessions, reutiliza la tabla existente)
├─ started_at
├─ completed_at
├─ disclaimer_accepted (boolean) — RS-4

emotional_responses
├─ id
├─ assessment_id (FK → emotional_assessments)
├─ module (phq9 | who5 | phq15 | cognitive_checklist | behavioral_checklist | gad7 | irritability_checklist | rosenberg | sleep | context)
├─ item_id
├─ raw_value
├─ is_scored (boolean) — false para los checklists no clínicos y el módulo de contexto (RF-2.4)

emotional_scores
├─ id
├─ assessment_id (FK → emotional_assessments)
├─ module (phq9 | who5 | phq15 | gad7 | rosenberg | sleep)   -- los checklists no clínicos no generan fila aquí
├─ response_scale (ej: "0-3_4opciones" | "0-5_6opciones" | "0-2_3opciones") — documenta qué escala se usó, ya que varía por módulo (RF-1.2)
├─ total_score
├─ severity_band
├─ is_clinically_validated (boolean) — true para PHQ-9/GAD-7/PHQ-15/WHO-5/Rosenberg, false para Sueño
├─ crisis_alert (boolean) — RS-1, solo aplica a phq9
├─ professional_help_recommended (boolean) — RS-5

emotional_checklist_selections  (nueva — para los 3 checklists no clínicos, que no se puntúan pero sí se listan)
├─ id
├─ assessment_id (FK → emotional_assessments)
├─ module (cognitive_checklist | behavioral_checklist | irritability_checklist)
├─ item_id
├─ selected (boolean)

crisis_resources  (RS-3 — tabla de configuración, editable sin desplegar código)
├─ id
├─ country_code
├─ resource_name
├─ contact_info (teléfono, chat, url)
├─ active (boolean)
├─ updated_at
```

---

## 7. Arquitectura técnica

**Se reutiliza exactamente el mismo stack definido en el PRD de personalidad — no se introduce ninguna herramienta nueva:**

| Capa | Herramienta | Nota de integración |
|---|---|---|
| Backend | Python + FastAPI | Nuevas rutas dentro del mismo proyecto (`/emotional-health/...`) |
| Frontend | Jinja2 + HTMX + Alpine.js + Tailwind | Nuevas plantillas, mismo patrón que el cuestionario de personalidad |
| Datos | SQLModel + PostgreSQL | Tablas nuevas (sección 6), mismo motor de base de datos |
| PDF | WeasyPrint | Misma librería, nueva plantilla |
| Correo | Resend / SendGrid | Mismo proveedor, nueva plantilla de email con sección de recursos si aplica |
| Motor de scoring | `emotional_health_engine.py` | Ya construido y probado — se importa directo, sin reescribir lógica |

---

## 8. Flujo de usuario

```
1. Landing del módulo → explicación breve + disclaimer (RS-4) → checkbox obligatorio
2. Bloque 1 — PHQ-9 + WHO-5 (14 ítems)
   └─ Si ítem 9 (PHQ-9) > 0 al responderlo → pantalla de recursos de crisis (RS-2) → usuario puede continuar
3. Bloque 2 — PHQ-15 (15 ítems, ventana de 4 semanas)
4. Bloque 3 — Checklist cognitivo (8 ítems, sin puntaje)
5. Bloque 4 — Checklist conductual (8 ítems, sin puntaje)
6. Bloque 5 — GAD-7 + checklist de irritabilidad (11 ítems)
7. Bloque 6 — Rosenberg (10 ítems)
8. Bloque 7 — Sueño (4 ítems, ya existente)
9. Bloque 8 — Contexto (7 ítems, opción múltiple, ya existente)
10. Pantalla de carga → cálculo con emotional_health_engine.py (extendido)
11. Informe:
    ├─ [Si aplica] Alerta de ayuda profesional (RS-5)
    ├─ Resultado PHQ-9 + interpretación conjunta con WHO-5
    ├─ Resultado PHQ-15 (somático)
    ├─ Checklist cognitivo (descriptivo, sin puntaje)
    ├─ Checklist conductual (descriptivo, sin puntaje)
    ├─ Resultado GAD-7 + checklist de irritabilidad (descriptivo)
    ├─ Resultado Rosenberg (autoestima)
    ├─ Resultado Sueño (no clínico)
    ├─ Resumen de contexto
    ├─ Disclaimer (siempre visible)
    ├─ Botón "Descargar PDF"
    └─ Campo de email + botón "Enviarme una copia"
```

---

## 9. Criterios de aceptación (Definition of Done)

- [ ] El ítem 9 del PHQ-9 activa la alerta de crisis de forma aislada, verificado con el Caso C del motor de scoring.
- [ ] La pantalla de recursos de crisis aparece antes de completar el resto del test, no solo al final.
- [ ] El disclaimer se muestra en 2 puntos obligatorios (inicio y resultado) y no puede omitirse.
- [ ] Ningún texto de la interfaz usa lenguaje diagnóstico ("tienes depresión").
- [ ] Los 8 módulos se presentan y calculan por separado, nunca combinados en un solo puntaje.
- [ ] Cada checklist no clínico (cognitivo, conductual, irritabilidad) se muestra sin puntaje numérico, solo como lista descriptiva.
- [ ] Cada resultado indica visualmente si proviene de un instrumento validado o de una observación no clínica (RF-3.11).
- [ ] La tabla `crisis_resources` está cargada con al menos 1 recurso verificado antes de producción (bloqueante — ver sección 10).
- [ ] Un profesional de salud mental revisó el contenido antes del lanzamiento a usuarios reales (bloqueante — RS-7).

---

## 10. Pendientes bloqueantes antes de producción (no técnicos, pero obligatorios)

Estos puntos **no se resuelven con código** — son decisiones de contenido/legales que debes cerrar tú antes de lanzar:

1. **Cargar `crisis_resources` con líneas de ayuda verificadas** del país donde vas a lanzar (busca la fuente oficial actual, no uses un dato que puedas tener desactualizado).
2. **Revisión de contenido por un profesional de salud mental**, aunque sea una revisión breve de los textos de resultado y las bandas de severidad.
3. **Verificar si tu país exige algún tipo de registro o cumplimiento normativo** para herramientas de cribado de salud digital (esto varía mucho por jurisdicción — en algunos países una app de este tipo puede considerarse producto sanitario según cómo se comunique, en otros no aplica ninguna regulación especial).
4. **Política de privacidad específica para datos de salud mental** — estos datos suelen clasificarse como "categoría especial" en regulaciones de protección de datos (más sensibles que el email de un test de personalidad), y eso puede exigir consentimiento y medidas de seguridad adicionales.
5. **Verificar los términos de uso vigentes de WHO-5, PHQ-15 y la Escala de Rosenberg** antes de un uso comercial. Los tres son de uso libre para fines clínicos/de investigación según su documentación histórica, pero los términos exactos (sobre todo para uso comercial a escala) deben confirmarse en la fuente oficial vigente antes del lanzamiento — no asumir que "de uso libre" equivale a "sin ninguna condición".

---

## 11. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Un usuario en crisis no ve los recursos a tiempo | RS-2: mostrar la alerta al momento de responder el ítem 9, no al final |
| El producto se percibe (o se usa) como diagnóstico médico | RS-4 + RS-6: disclaimer obligatorio + lenguaje no diagnóstico en todo el copy |
| Recursos de crisis desactualizados | RS-3: tabla configurable, revisión periódica programada (ej. cada 6 meses) |
| Exposición de datos sensibles de salud mental | Modelo de datos separado de identidad cuando sea posible; política de retención más estricta que en el test de personalidad |
| Incumplimiento normativo no detectado a tiempo | Pendiente bloqueante #3 (sección 10) antes de cualquier lanzamiento público |

---

## 12. Próximos pasos inmediatos

1. Extender `emotional_health_engine.py` con `score_who5()`, `score_phq15()` y `score_rosenberg()`, cada una con sus propios casos de prueba manuales (mismo patrón ya usado y validado).
2. Crear las tablas nuevas/actualizadas del modelo de datos (sección 6) sobre la base de datos ya existente del proyecto.
3. Implementar las rutas del cuestionario (RF-1) reutilizando el patrón de HTMX ya usado en el test de personalidad, con especial atención a que cada bloque declare su propia escala de respuesta (RF-1.2).
4. Conectar el motor extendido al endpoint de scoring.
5. Implementar la pantalla de alerta de crisis (RS-2) como la primera pieza de interfaz nueva — sigue siendo el requisito de mayor prioridad de todo el módulo, sin importar que el test ahora sea más largo.
6. Cerrar los 5 pendientes bloqueantes de la sección 10 (incluyendo el nuevo punto sobre licencias de los instrumentos) antes de considerar el módulo listo para producción.
