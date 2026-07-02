@echo off
REM ─────────────────────────────────────────────────────────────────
REM arrancar.bat — script de inicio rápido para Windows
REM ─────────────────────────────────────────────────────────────────

echo.
echo ============================================================
echo   OCEAN-P — Test de Personalidad (entorno local)
echo ============================================================
echo.

REM 1) Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    echo         Descargalo desde https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 2) Crear venv si no existe
if not exist ".venv\Scripts\python.exe" (
    echo [1/4] Creando entorno virtual...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
) else (
    echo [1/4] Entorno virtual ya existe.
)

REM 3) Activar venv
call .venv\Scripts\activate.bat

REM 4) Instalar/actualizar dependencias
echo [2/4] Verificando dependencias...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [ERROR] No se pudieron instalar las dependencias.
    pause
    exit /b 1
)

REM 5) Aplicar migraciones si la BD no existe
if not exist "ocean_p.db" (
    echo [3/4] Creando base de datos local...
    alembic upgrade head
    if errorlevel 1 (
        echo [ERROR] No se pudieron aplicar las migraciones.
        pause
        exit /b 1
    )
) else (
    echo [3/4] Base de datos local ya existe.
)

REM 6) Arrancar servidor
echo [4/4] Arrancando servidor...
echo.
echo ============================================================
echo   Servidor en: http://127.0.0.1:8000/quiz
echo   Para detener: Ctrl+C
echo ============================================================
echo.

uvicorn app.main:app --reload

pause
