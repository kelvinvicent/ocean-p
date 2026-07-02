@echo off
REM ─────────────────────────────────────────────────────────────────
REM reset.bat — borra la BD local y la recrea desde migraciones
REM ─────────────────────────────────────────────────────────────────

echo.
echo ============================================================
echo   OCEAN-P — Reset de base de datos local
echo ============================================================
echo.

if exist "ocean_p.db" (
    echo [1/2] Borrando ocean_p.db...
    del ocean_p.db
) else (
    echo [1/2] No existe ocean_p.db, nada que borrar.
)

echo [2/2] Aplicando migraciones...
call .venv\Scripts\activate.bat
alembic upgrade head

echo.
echo [OK] Base de datos reseteada.
echo.
pause
