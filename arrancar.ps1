# ─────────────────────────────────────────────────────────────────
# arrancar.ps1 — script de inicio rápido para PowerShell
# ─────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  OCEAN-P — Test de Personalidad (entorno local)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 1) Verificar Python
try {
    $pythonVersion = python --version
    Write-Host "[OK] Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python no esta instalado o no esta en PATH." -ForegroundColor Red
    Write-Host "        Descargalo desde https://www.python.org/downloads/" -ForegroundColor Red
    pause
    exit 1
}

# 2) Crear venv si no existe
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "[1/4] Creando entorno virtual..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] No se pudo crear el entorno virtual." -ForegroundColor Red
        pause
        exit 1
    }
} else {
    Write-Host "[1/4] Entorno virtual ya existe." -ForegroundColor Green
}

# 3) Activar venv
& .\.venv\Scripts\Activate.ps1 | Out-Null

# 4) Instalar/actualizar dependencias
Write-Host "[2/4] Verificando dependencias..." -ForegroundColor Yellow
pip install -q -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] No se pudieron instalar las dependencias." -ForegroundColor Red
    pause
    exit 1
}
Write-Host "       Dependencias OK." -ForegroundColor Green

# 5) Aplicar migraciones si la BD no existe
if (-not (Test-Path "ocean_p.db")) {
    Write-Host "[3/4] Creando base de datos local..." -ForegroundColor Yellow
    alembic upgrade head | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] No se pudieron aplicar las migraciones." -ForegroundColor Red
        pause
        exit 1
    }
    Write-Host "       Base de datos creada." -ForegroundColor Green
} else {
    Write-Host "[3/4] Base de datos local ya existe." -ForegroundColor Green
}

# 6) Arrancar servidor
Write-Host "[4/4] Arrancando servidor..." -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Servidor en: " -NoNewline -ForegroundColor Cyan
Write-Host "http://127.0.0.1:8000/quiz" -ForegroundColor White
Write-Host "  Para detener: Ctrl+C" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

uvicorn app.main:app --reload

pause
