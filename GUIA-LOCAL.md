# 🚀 Guía de Uso Local — OCEAN-P

Esta guía explica cómo levantar el proyecto en tu máquina, recorrer el flujo completo del test, y validar que todo funciona antes de desplegar.

---

## 1. Requisitos previos

- **Python 3.10+** (probado con 3.12)
- **Git** (opcional, solo para clonar)
- Un navegador moderno (Chrome, Firefox, Edge, Safari)
- Conexión a internet (las CDNs de Tailwind, HTMX, Alpine.js y Anime.js se cargan en el navegador)

> **No necesitas** Node.js, npm, PostgreSQL local ni Docker para desarrollo.

---

## 2. Instalación (5 minutos)

### 2.1 Clonar o descargar el proyecto

```bash
cd "C:\Users\User\Desktop\Test personalidad"
```

### 2.2 Crear y activar el entorno virtual

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2.3 Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2.4 Verificar la instalación

```bash
python -c "import fastapi, sqlmodel, jinja2, alembic, pytest, resend, psycopg2; print('OK')"
```

Si imprime `OK`, todo está instalado.

---

## 3. Base de datos local

El proyecto usa **SQLite por defecto** (cero config). Si vas a usar PostgreSQL/Neon, edita `.env` (ver sección 10).

### 3.1 Aplicar las migraciones

```bash
alembic upgrade head
```

Deberías ver:
```
INFO  [alembic.runtime.migration] Running upgrade  -> fab70df98a04, initial schema
```

Esto crea el archivo `ocean_p.db` con las 7 tablas.

### 3.2 Verificar tablas creadas

```bash
python -c "import sqlite3; con=sqlite3.connect('ocean_p.db'); [print(n[0]) for n in con.execute(\"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name\")]; con.close()"
```

Deberías ver:
```
alembic_version
email_deliveries
norm_tables
reports
responses
scores
test_sessions
users
```

---

## 4. Arrancar el servidor

```bash
uvicorn app.main:app --reload
```

Salida esperada:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Application startup complete.
```

> **Importante:** NO abras el navegador todavía. Primero completa la sección 5.

---

## 5. Recorrido del flujo completo

Abre en el navegador: **http://127.0.0.1:8000/quiz**

### Paso 1 — Landing
- Ves la pantalla principal con headline, descripción y el botón **"Comenzar test"**.
- **Verifica:** mueve el mouse sobre el botón — debe seguiste sutilmente el cursor (hover magnético).
- Las letras del título aparecen con animación staggered.

### Paso 2 — Crear sesión
- Haz clic en **"Comenzar test"**.
- Serás redirigido a `/quiz/{session_id}/instructions` (la pantalla de instrucciones).

### Paso 3 — Pantalla de instrucciones
- Lee las cards informativas (tiempo, dimensiones, privacidad).
- Haz clic en **"Empezar el test"**.

### Paso 4 — Cuestionario
- Aparecerá el ítem 1 con la escala Likert 1-5.
- **Verifica:** al hacer clic en una opción, verás un **efecto ripple** (onda circular desde el punto de clic).
- La **barra de progreso** se llena con animación spring.
- **Indicador:** "1 de 65".

### Paso 4.5 — Probar la persistencia
- Responde 5-10 ítems, luego **cierra la pestaña** (no la app).
- Vuelve a abrir `http://127.0.0.1:8000/quiz/{tu_session_id}`.
- **Verifica:** tus respuestas anteriores siguen ahí, y el contador muestra "X de 65" correctamente.

### Paso 4.6 — Micro-motivación al ítem 33
- Responde hasta llegar al ítem 33 (contador "33 de 65").
- **Verifica:** aparece un banner animado: **"¡Ya vas por la mitad! Tu perfil está tomando forma..."** con botón "Continuar".
- Solo aparece **una vez** por sesión (no se reabre tras refresh).

### Paso 5 — Pantalla de cálculo
- Al responder el ítem 65, serás redirigido a `/calculating/{session_id}`.
- **Verifica:** SVG con 5 anillos OCEAN rotando, texto que cambia cada 1.5s.
- Después de ~1.2s, redirige automáticamente al informe.

### Paso 6 — Informe
- Llegas a `/report/{session_id}`.
- **Verifica:**
  - Header con tu **arquetipo dimensional** (reveal letter-by-letter).
  - **Disclaimer** de tabla normativa inicial (gris, debajo del header).
  - **Banner rojo** si tu test tuvo 2+ alertas de validez, con botón "Repetir el test".
  - **Top 2 fortalezas** y **2 áreas de desarrollo** (cards).
  - **Gráfico de 5 dimensiones** con barras animadas (percentil 0-100).
  - **15 cards de facetas** con badge coloreado (verde/amarillo/rojo según percentil).
  - **4 tarjetas de índices profesionales** (Liderazgo, Equipo, Riesgo, Ejecución).
  - CTAs de PDF/email deshabilitados (serán la Fase 2).

---

## 6. Probar el caso de "validez baja"

Para ver el banner de "Resultado no concluyente":

1. Abre DevTools (F12) → Application → Local Storage.
2. Elimina la clave `ocean-p:session:{session_id}`.
3. Recarga la página.
4. Responde los primeros 32 ítems con **3** (neutral).
5. Para los ítems 61, 62, 63 responde **5** (esto dispara las alertas de deseabilidad social y atención).
6. El resto con **3**.

Al finalizar deberías ver el banner rojo de "Resultado no concluyente".

---

## 7. Ejecutar los tests

```bash
pytest -v
```

Salida esperada:
```
============================== 88 passed, 2 warnings in 7.5s ==============================
```

Para ver el detalle de los tests:
```bash
pytest -v --tb=short
```

Para correr solo un archivo de tests:
```bash
pytest tests/test_scoring.py -v
pytest tests/test_report.py -v
pytest tests/test_api_sessions.py -v
```

### Cobertura de tests

| Archivo | Cubre |
|---|---|
| `test_scoring.py` | Motor de scoring puro + orquestador con BD (14 tests) |
| `test_norm.py` | Conversión raw → percentil (28 tests) |
| `test_api_sessions.py` | Endpoints REST `/sessions/*` (12 tests) |
| `test_views.py` | Templates HTML (10 tests) |
| `test_report.py` | Informe y servicio de interpretaciones (15 tests) |
| `conftest.py` | Fixtures compartidas (BD en memoria) |

---

## 8. Estructura del proyecto

```
Test personalidad/
├── app/
│   ├── main.py                # Entry point FastAPI + routers
│   ├── config.py              # Settings (.env)
│   ├── database.py            # Engine SQLModel + sesión
│   ├── models/                # Modelos de BD (User, TestSession, etc.)
│   ├── routers/
│   │   ├── quiz.py            # Endpoints REST del cuestionario
│   │   ├── views.py           # Renderiza templates (landing, quiz, etc.)
│   │   └── report.py          # Endpoints del informe
│   ├── services/
│   │   ├── scoring_engine.py  # Motor puro (sin I/O)
│   │   ├── scoring_service.py # Orquestador: BD → motor → persistencia
│   │   ├── norm_service.py    # Raw → percentil
│   │   ├── archetype_service.py
│   │   └── interpretation_service.py
│   ├── data/
│   │   ├── items.json         # 65 ítems del test
│   │   ├── norms_v1.json      # Tabla normativa inicial
│   │   └── interpretations.json
│   ├── templates/             # Jinja2 (HTML)
│   └── static/                # CSS + JS
├── tests/                     # 88 tests pytest
├── migrations/                # Alembic
├── .env                       # Configuración local
├── alembic.ini
├── requirements.txt
└── PLAN-IMPLEMENTACION.md    # Plan completo del proyecto
```

---

## 9. Comandos útiles

| Comando | Para qué sirve |
|---|---|
| `uvicorn app.main:app --reload` | Arrancar el servidor con hot-reload |
| `alembic upgrade head` | Aplicar migraciones pendientes |
| `alembic revision --autogenerate -m "msg"` | Crear nueva migración tras cambios en modelos |
| `alembic downgrade -1` | Revertir la última migración |
| `pytest -v` | Correr todos los tests |
| `pytest -k test_nombre` | Correr un test específico |
| `rm ocean_p.db && alembic upgrade head` | Resetear la BD local |
| `python -c "from app.main import app; print(app.routes)"` | Ver todas las rutas registradas |

---

## 10. Cambiar a PostgreSQL (Neon) — opcional

Por defecto el proyecto usa SQLite. Para conectarte a Neon (u otro PostgreSQL):

### 10.1 Crear proyecto en Neon
1. Ve a https://console.neon.tech
2. Crea un proyecto (región cerca de tus usuarios).
3. Copia el **Connection string** (formato: `postgresql://user:pass@ep-xxx.aws.neon.tech/neondb?sslmode=require`)

### 10.2 Configurar .env
Edita `.env`:
```
DATABASE_URL=postgresql://user:pass@ep-xxx.aws.neon.tech/neondb?sslmode=require
```

### 10.3 Aplicar migraciones
```bash
alembic upgrade head
```

### 10.4 Arrancar normal
```bash
uvicorn app.main:app --reload
```

El motor de la app detecta automáticamente SQLite vs PostgreSQL y configura el pool de conexiones apropiado (con `pool_pre_ping` y `pool_recycle=300` para Neon serverless).

---

## 11. Resetear todo

Si quieres empezar de cero:

```bash
# 1. Borrar la BD local
rm ocean_p.db

# 2. Re-aplicar migraciones
alembic upgrade head

# 3. Arrancar de nuevo
uvicorn app.main:app --reload
```

---

## 12. Solución de problemas

### "ModuleNotFoundError: No module named 'app'"
- Asegúrate de estar en la raíz del proyecto y de tener el venv activado.

### "sqlite3.OperationalError: table X already exists"
- Borra la BD: `rm ocean_p.db` y re-aplica migraciones.

### El navegador muestra la página en blanco
- Abre DevTools (F12) → Console. Probablemente una CDN falló (revisa tu internet).
- Las CDNs cargadas: `cdn.tailwindcss.com`, `unpkg.com/htmx`, `cdn.jsdelivr.net/npm/alpinejs`, `cdn.jsdelivr.net/npm/animejs`, `fonts.googleapis.com`.

### Las animaciones no se ven
- Recarga la página con Ctrl+Shift+R (forzar recarga sin caché).

### "Address already in use" al arrancar uvicorn
- Otro proceso está usando el puerto 8000. Mata el proceso o usa otro puerto:
  ```bash
  uvicorn app.main:app --reload --port 8001
  ```

### El test falla con "JSONDecodeError"
- Probablemente quedó una sesión vieja. Cierra el navegador, limpia Local Storage, y vuelve a empezar.

---

## 13. Próximos pasos (Fase 2)

La **Fase 1 (MVP) está completa**. Lo que sigue:

- **Fase 2 — Exportación:** generación de PDF (WeasyPrint) y envío por email (Resend).
- **Fase 3 — Producto completo:** tests complementarios, microrretos, insignias.

Para ver el plan completo: [PLAN-IMPLEMENTACION.md](./PLAN-IMPLEMENTACION.md).

---

*¿Encontraste un bug o tienes una sugerencia? Anótalo y abrimos issue.*
