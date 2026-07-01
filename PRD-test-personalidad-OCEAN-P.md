# PRD — Test de Personalidad OCEAN-P
## Product Requirements Document v1.0

---

## 1. Resumen del producto

**Qué es:** una aplicación web donde el usuario realiza un test de personalidad de 65 ítems, recibe un informe interactivo en pantalla, puede descargarlo en **PDF** y/o recibirlo por **correo electrónico**.

**Para quién:** personas que buscan autoconocimiento aplicado a su desarrollo profesional (público general, sin necesidad de formación en psicología).

**Por qué ahora (problema que resuelve):** la mayoría de tests gratuitos online dan un resultado genérico, sin profundidad ni conexión a un plan de acción. Este producto entrega un informe accionable y lo deja en manos del usuario (PDF descargable, copia en su correo) sin obligarlo a crear cuenta para obtener valor.

---

## 2. Objetivos y métricas de éxito

| Objetivo | Métrica | Meta inicial (MVP) |
|---|---|---|
| El usuario completa el test | Tasa de finalización (inicia → termina) | ≥ 70% |
| El informe es confiable | % de tests marcados "no concluyente" por escalas de validez | ≤ 15% |
| El usuario se lleva el resultado | % que descarga PDF o pide envío por correo | ≥ 50% |
| Rendimiento técnico | Tiempo de generación de informe tras el último ítem | ≤ 3 segundos |
| Rendimiento del PDF | Tiempo de generación del PDF | ≤ 5 segundos |
| Entrega de correo | % de correos entregados exitosamente | ≥ 98% |

---

## 3. Alcance por fases

### Fase 1 — MVP (núcleo funcional)
- Cuestionario interactivo de 65 ítems (frontend)
- Motor de scoring (backend): facetas, dimensiones, índices, validez
- Informe de resultados en pantalla (HTML)
- Almacenamiento de resultados en base de datos
- **Fuera de alcance en MVP:** cuenta de usuario obligatoria, tests complementarios, microrretos, certificación

### Fase 2 — Exportación
- Generación de **PDF** del informe (descarga directa)
- Envío del informe por **correo electrónico** (con consentimiento explícito)
- Captura de email opcional (no bloquea el acceso al resultado en pantalla)

### Fase 3 — Producto completo (post-MVP)
- Tests complementarios (los 7 listados en el documento de diseño)
- Microrretos diarios + seguimiento de progreso
- Certificación / insignias
- Panel de administración con analítica agregada (anónima)

> **Regla de diseño:** las fases 2 y 3 deben construirse de modo que **no requieran rediseñar el modelo de datos de la fase 1**. Esto se logra diseñando el modelo de datos completo desde ahora (sección 6), aunque se implemente por partes.

---

## 4. Usuarios y flujo principal

**Personas:**
- *Usuario final:* quiere autoconocimiento aplicado, no tiene conocimientos de psicometría, accede desde móvil o escritorio.
- *Tú (builder):* necesitas un sistema que puedas mantener y extender solo, sin equipo de soporte.

**Flujo de usuario (happy path):**

```
1. Landing → "Comenzar test"
2. Pantalla de instrucciones (tiempo estimado, propósito, privacidad)
3. Cuestionario (65 ítems, barra de progreso, 1 ítem o bloque por pantalla)
4. Pantalla de carga ("Calculando tu perfil…")
5. Informe de resultados en pantalla
   ├─ Botón "Descargar PDF"
   └─ Campo de email + botón "Enviarme una copia"
6. (Opcional) Pantalla de confirmación de envío de correo
```

**Flujo de error / validez baja:**
```
3. Cuestionario completado con ≥2 alertas de validez activadas
4. Informe muestra aviso: "Resultado no concluyente" + botón "Repetir test"
```

---

## 5. Requisitos funcionales

### RF-1: Cuestionario
- RF-1.1: Mostrar los 65 ítems en escala Likert 1-5, con etiquetas visibles en los extremos.
- RF-1.2: Permitir navegación hacia atrás para corregir respuestas antes de enviar.
- RF-1.3: No permitir avanzar sin responder el ítem actual (o bloque actual).
- RF-1.4: Guardar el progreso en el cliente (localStorage o estado de sesión) para que un refresco accidental no borre las respuestas.
- RF-1.5: Registrar el tiempo total de respuesta y el tiempo por ítem (input para futura detección de respuestas apresuradas).

### RF-2: Motor de scoring
- RF-2.1: Invertir automáticamente los ítems marcados (R) antes de calcular.
- RF-2.2: Calcular las 15 puntuaciones de faceta (promedio 1-5).
- RF-2.3: Calcular las 5 puntuaciones de dimensión (promedio de facetas).
- RF-2.4: Calcular los 4 índices profesionales compuestos.
- RF-2.5: Calcular las 3 escalas de validez y aplicar las reglas de alerta definidas en el documento de diseño (sección 4.4).
- RF-2.6: Convertir puntuaciones brutas a percentil usando la tabla normativa vigente (versionada, ver RF-2.7).
- RF-2.7: La tabla normativa debe ser un recurso versionado y reemplazable (no hardcodeada en la lógica de negocio), para poder actualizarla cuando haya datos reales de usuarios.

### RF-3: Informe en pantalla
- RF-3.1: Mostrar resumen del perfil + arquetipo dimensional.
- RF-3.2: Mostrar gráfico de las 5 dimensiones (percentil).
- RF-3.3: Mostrar detalle de las 15 facetas con descripción conductual.
- RF-3.4: Mostrar los 4 índices profesionales.
- RF-3.5: Si hay alertas de validez, mostrar aviso claro y no presentar el informe como concluyente.

### RF-4: Generación de PDF
- RF-4.1: Botón "Descargar PDF" genera un documento con el mismo contenido del informe en pantalla, en formato imprimible (A4).
- RF-4.2: El PDF debe generarse en el servidor (no con captura de pantalla del navegador), para garantizar formato consistente.
- RF-4.3: El PDF debe incluir: nombre del test, fecha, resumen, gráfico de dimensiones, detalle de facetas, índices profesionales, y aviso de validez si aplica.
- RF-4.4: Tiempo máximo de generación: 5 segundos (ver sección 2).
- RF-4.5: El PDF no debe quedar accesible públicamente por URL predecible (usar token único no incremental).

### RF-5: Envío por correo electrónico
- RF-5.1: Campo de email con validación de formato antes de habilitar el botón de envío.
- RF-5.2: Checkbox de consentimiento explícito, no premarcado: *"Acepto recibir este informe en mi correo"* (ver sección 8, privacidad).
- RF-5.3: El correo debe incluir el PDF adjunto o un enlace de descarga seguro con expiración (recomendado: enlace con expiración de 7 días, más liviano que adjuntar PDF pesado).
- RF-5.4: Confirmar visualmente al usuario que el correo fue enviado (o mostrar error claro si falló).
- RF-5.5: Registrar el evento de envío (sin almacenar el contenido del correo, solo metadato: a qué hora, a qué test_session, éxito/fallo).

---

## 6. Modelo de datos (diseño desde el día 1, aunque se implemente por fases)

```
users (opcional en MVP — puede no requerir login)
├─ id
├─ email (nullable, solo si el usuario lo entrega)
├─ created_at

test_sessions
├─ id
├─ user_id (nullable)
├─ started_at
├─ completed_at
├─ status (in_progress | completed | invalid)
├─ avg_response_time_ms

responses
├─ id
├─ session_id (FK → test_sessions)
├─ item_id (1-65)
├─ raw_value (1-5)
├─ response_time_ms

scores
├─ id
├─ session_id (FK → test_sessions)
├─ scope_type (facet | dimension | composite_index | validity)
├─ scope_key (ej: "asertividad", "responsabilidad", "liderazgo_potencial")
├─ raw_score
├─ percentile

reports
├─ id
├─ session_id (FK → test_sessions)
├─ archetype_label
├─ generated_at
├─ pdf_url (nullable hasta que se genera)

email_deliveries
├─ id
├─ session_id (FK → test_sessions)
├─ email_hash (no almacenar el email en texto plano sin necesidad — ver sección 8)
├─ sent_at
├─ status (sent | failed)

norm_tables (tabla normativa versionada — RF-2.7)
├─ id
├─ version
├─ scope_key
├─ raw_to_percentile_mapping (JSON)
├─ active (boolean)
```

---

## 7. Arquitectura técnica recomendada

> **Decisión de stack: 100% Python en el backend, y en el frontend una combinación que evita depender de un segundo lenguaje/framework (JavaScript avanzado, Node.js) para que una sola persona con dominio de Python pueda construir y mantener todo el producto.**

| Capa | Recomendación | Por qué |
|---|---|---|
| Backend | **Python + FastAPI** | Framework async, tipado, con documentación de API automática (OpenAPI/Swagger). Reutiliza directamente el `scoring_engine.py` ya construido, sin traducir la lógica de negocio a otro lenguaje |
| Frontend | **Jinja2 (plantillas server-side) + HTMX + Alpine.js + Tailwind CSS (vía CDN, sin build step)** | Permite construir el cuestionario y el informe con HTML + Python. HTMX maneja la interactividad (avanzar de ítem sin recargar la página completa) y Alpine.js cubre comportamientos pequeños en el cliente (validaciones, progreso). No requiere Node.js, npm, webpack ni un framework JS separado (React/Vue) |
| ORM / capa de datos | **SQLModel** (creado por el mismo autor de FastAPI) o SQLAlchemy | Mapea el modelo de datos de la sección 6 directamente a clases Python con validación de tipos integrada |
| Base de datos | PostgreSQL | Relacional, encaja con el modelo de la sección 6; se puede alojar en Railway, Render o Supabase |
| Generación de PDF | **WeasyPrint** | Librería 100% Python que convierte HTML/CSS directamente a PDF. Reutiliza la misma plantilla Jinja2 del informe en pantalla → sin depender de Node/Puppeteer ni de un segundo entorno de ejecución |
| Envío de correo | Resend o SendGrid (ambos con SDK oficial en Python) | Se llaman directamente desde Python, buena entregabilidad, plan gratuito suficiente para validar el producto |
| Hosting | Railway o Render | Despliegan aplicaciones Python (FastAPI) directamente desde el repositorio, sin necesidad de configurar servidores manualmente ni de un runtime distinto |
| Almacenamiento temporal de PDFs | Volumen del propio proveedor (Railway/Render) o S3, con URLs firmadas y expiración | Cumple RF-4.5 y RF-5.3 sin construir tu propio sistema de archivos seguro |

**Resumen de la decisión:** con esta combinación, el único código que no es Python es HTML + un poco de Tailwind/Alpine en los templates — no hay un segundo lenguaje de programación que aprender ni un proyecto separado (frontend/backend) que sincronizar. Todo vive en un solo repositorio FastAPI.

---

## 8. Privacidad y seguridad de datos (crítico — datos psicológicos son datos sensibles)

- **Consentimiento explícito** antes de capturar el email (RF-5.2) — nunca premarcado.
- **Minimización de datos**: no almacenar el email en texto plano si no es estrictamente necesario; considerar almacenar un hash para verificación de envíos duplicados, y el email real solo en el proveedor de correo transaccional (que ya cumple sus propios estándares de seguridad), no duplicado en tu base de datos si puedes evitarlo.
- **Retención**: define una política clara, ej. "los resultados se conservan 90 días si no hay cuenta asociada, luego se anonimizan". Comunícalo en la pantalla de instrucciones.
- **Sin venta ni uso secundario de los datos** sin consentimiento adicional explícito — esto debe figurar en una política de privacidad simple, visible antes de empezar el test.
- **URLs no predecibles** para PDFs e informes (RF-4.5) — usar UUID v4, nunca IDs incrementales.
- **Cifrado en tránsito** (HTTPS obligatorio) y **en reposo** si tu proveedor de base de datos lo permite (Supabase/Neon lo incluyen por defecto).

---

## 9. Plan de implementación sugerido (para un builder solo)

| Semana | Entregable |
|---|---|
| 1 | Proyecto FastAPI + modelo de datos (SQLModel) + cuestionario funcional (rutas Jinja2 + HTMX) guardando respuestas en BD |
| 2 | Motor de scoring completo (facetas, dimensiones, índices, validez) + tests unitarios de las fórmulas |
| 3 | Informe en pantalla (plantilla Jinja2) consumiendo los datos calculados por el endpoint FastAPI |
| 4 | Generación de PDF con **WeasyPrint** a partir de la misma plantilla Jinja2 del informe |
| 5 | Envío de correo (SDK de Resend/SendGrid) + consentimiento + registro de envíos |
| 6 | Pruebas end-to-end, ajuste de tabla normativa con respuestas reales de prueba (mínimo 20-30 personas piloto), despliegue en Railway/Render |

---

## 10. Criterios de aceptación (Definition of Done del MVP + Fase 2)

- [ ] Un usuario puede completar el test de inicio a fin sin perder progreso ante un refresco de página.
- [ ] El informe en pantalla coincide matemáticamente con la clave de corrección del documento de diseño.
- [ ] Un test con 2+ alertas de validez muestra el aviso de "no concluyente" y no presenta percentiles como definitivos.
- [ ] El botón "Descargar PDF" genera un archivo correctamente formateado en menos de 5 segundos.
- [ ] El envío por correo solo ocurre tras consentimiento explícito y confirma éxito/fallo al usuario.
- [ ] Ningún PDF ni informe es accesible mediante URL adivinable.
- [ ] La tabla normativa puede actualizarse sin tocar el código del motor de scoring.

---

## 11. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Percentiles poco precisos por falta de muestra normativa real | Lanzar con la fórmula lineal simplificada, etiquetada como "versión inicial", y recalibrar tras 200-300 respuestas reales |
| Baja entregabilidad de correos (van a spam) | Usar proveedor transaccional reputado (Resend/SendGrid) con dominio verificado (SPF/DKIM) desde el día 1 |
| Usuarios abandonan el test a mitad de camino | Medir en qué ítem ocurre el abandono (analítica simple) y considerar dividir en bloques con guardado de progreso visible |
| Generación de PDF lenta bajo carga | Generar el PDF de forma asíncrona (background task de FastAPI, o Celery/RQ si el tráfico crece) en vez de bloquear la respuesta HTTP |

---

## 12. Próximos pasos inmediatos

1. Crear el repositorio y el modelo de datos de la sección 6 en Postgres.
2. Implementar el cuestionario (RF-1) conectado a `responses`.
3. Implementar el motor de scoring (RF-2) como módulo independiente y testeable, usando como entrada la clave de corrección del documento de diseño previo.
4. Validar manualmente el motor de scoring con 3-5 casos de prueba calculados a mano antes de seguir a PDF/correo.
