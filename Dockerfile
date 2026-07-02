# ─────────────────────────────────────────────────────────────
# Dockerfile — OCEAN-P para Railway
# Imagen: python:3.12-slim (debian-based, ~150MB base)
# ─────────────────────────────────────────────────────────────

FROM python:3.12-slim

# Evitar bytecode .pyc y buffering de stdout/stderr (importante para logs)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencias del sistema (mínimas — sin WeasyPrint todavía, no hacen falta)
# Si en el futuro añades WeasyPrint o psycopg2 compilado, agrega:
#   libpq-dev gcc libpango-1.0-0 libpangoft2-1.0-0
# Pero como ya usamos psycopg2-binary (binario pre-compilado), no hace falta.
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl && \
    rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (mejor caché de capas Docker)
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer el puerto (Railway lo inyecta via $PORT)
EXPOSE 8000

# Healthcheck (Railway lo usa para saber si el servicio está vivo)
# Usamos shell form para que ${PORT:-8000} se expanda correctamente
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD sh -c 'curl -f "http://127.0.0.1:${PORT:-8000}/health" || exit 1'

# Start command: usa shell form (sh -c) para expandir ${PORT:-8000}.
# Esto es crítico: CMD en exec form NO expande variables de entorno.
# Railway inyecta $PORT automáticamente; fallback a 8000 para dev local.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
