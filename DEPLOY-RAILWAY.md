# 🚂 Desplegar OCEAN-P en Railway

Guía paso a paso para llevar el proyecto a producción. Railway detecta el `Dockerfile` automáticamente y despliega en cada push a la rama principal.

---

## 1. Requisitos

- Cuenta en [Railway](https://railway.app) (GitHub login es lo más rápido)
- El proyecto en un repositorio de GitHub
- (Opcional) cuenta en [Neon](https://neon.tech) si querés una BD PostgreSQL administrada

---

## 2. Archivos que Railway necesita

| Archivo | Para qué |
|---|---|
| `Dockerfile` | Construye la imagen del contenedor |
| `railway.toml` | Configuración de deploy (release command, healthcheck, restart policy) |
| `.dockerignore` | Excluye `.venv`, `.db`, `.env` de la imagen |
| `requirements.txt` | Dependencias Python |
| `alembic.ini` + `migrations/` | Migraciones (se aplican automáticamente en cada deploy) |

Todos estos archivos **ya están en el proyecto**. No tenés que crear nada nuevo.

---

## 3. Setup paso a paso

### 3.1 — Subir el código a GitHub

Si todavía no lo hiciste:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/tu-usuario/ocean-p.git
git push -u origin main
```

### 3.2 — Crear proyecto en Railway

1. Ir a https://railway.app/new
2. Click en **"Deploy from GitHub repo"**
3. Seleccionar el repositorio `ocean-p`
4. Railway detecta el Dockerfile y empieza a construir

### 3.3 — Configurar la base de datos

Tenés dos opciones:

**Opción A: Usar el PostgreSQL de Railway (más simple)**
1. En tu proyecto de Railway, click **"+ New"** → **"Database"** → **"PostgreSQL"
2. Railway crea la BD y la inyecta como variable `DATABASE_URL` automáticamente
3. No tenés que hacer nada más

**Opción B: Usar Neon (BD administrada, free tier generoso)**
1. Crear proyecto en https://console.neon.tech
2. Copiar el connection string (formato `postgresql://user:pass@ep-xxx.aws.neon.tech/neondb?sslmode=require`)
3. En Railway → tu servicio → **"Variables"** → agregar:
   ```
   DATABASE_URL = postgresql://user:pass@ep-xxx.aws.neon.tech/neondb?sslmode=require
   ```

### 3.4 — Configurar SECRET_KEY (importante)

En Railway → tu servicio → **"Variables"** → agregar:
```
SECRET_KEY = una-cadena-aleatoria-larga-de-al-menos-32-caracteres
jjI5zgb-oFZkaCp3vkW0phjfRR1whGYe7iy6bcyML6I

Podés generar una con: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

### 3.5 — Verificar el deploy

1. Railway construye la imagen y la despliega
2. El **release command** (`alembic upgrade head`) se ejecuta automáticamente antes de arrancar el servidor
3. Si las migraciones fallan, Railway hace rollback automático
4. El **healthcheck** (`/health`) confirma que el servicio está vivo
5. Una vez verde, click en el dominio generado por Railway: `tu-app.up.railway.app`

### 3.6 — Configurar dominio custom (opcional)

1. En Railway → tu servicio → **"Settings"** → **"Domains"**
2. Click **"Custom Domain"** → escribir `tudominio.com`
3. Configurar el CNAME en tu proveedor DNS

---

## 4. Cómo funciona el deploy

```
git push origin main
         ↓
   Railway detecta el push
         ↓
   Construye la imagen (Dockerfile)
         ↓
   Ejecuta releaseCommand: alembic upgrade head
         ↓
   Si las migraciones fallan → ROLLBACK automático
         ↓
   Ejecuta startCommand: uvicorn app.main:app --port $PORT
         ↓
   Healthcheck GET /health cada 30s
         ↓
   App accesible en https://tu-app.up.railway.app
```

---

## 5. Variables de entorno

| Variable | Requerida | Default | Descripción |
|---|---|---|---|
| `DATABASE_URL` | Sí | `sqlite:///./ocean_p.db` | URL de conexión a la BD |
| `SECRET_KEY` | Sí | (placeholder) | Clave para tokens — **usar valor aleatorio en producción** |
| `PORT` | Auto | `8000` | Railway lo inyecta automáticamente |
| `RESEND_API_KEY` | No | (vacío) | Solo para envío de emails (Fase 2, no implementado aún) |

---

## 6. Verificación post-deploy

Una vez desplegado, verificá:

```bash
# Health check
curl https://tu-app.up.railway.app/health

# Landing
curl -I https://tu-app.up.railway.app/quiz

# Crear sesión
curl -X POST https://tu-app.up.railway.app/sessions
```

Si todo responde 200, el deploy está OK.

---

## 7. Troubleshooting

### El deploy falla con "alembic upgrade head" no encontrado

Verificar que `alembic.ini` y la carpeta `migrations/` están commiteados en el repo.

### El healthcheck falla repetidamente

Abrí la consola de Railway → "Logs". Buscar:
- Errores de import (módulo faltante)
- Errores de conexión a BD (DATABASE_URL mal configurado)
- Puerto incorrecto (asegurate de usar `${PORT:-8000}`)

### Las migraciones se ejecutan pero la app no arranca

Revisar los logs. Probablemente sea un error de runtime (variable de entorno faltante).

### Quiero forzar re-ejecución de migraciones

En Railway → tu servicio → **"Settings"** → **"Restart"**. Esto NO vuelve a correr migraciones. Para forzar:
1. Push un commit vacío (`git commit --allow-empty -m "trigger deploy"`)
2. O conectar a la BD manualmente y verificar el estado con `alembic current`

---

## 8. Costos estimados

| Recurso | Plan | Costo |
|---|---|---|
| Railway Hobby | $5/mes de crédito incluido | $0-5/mes según uso |
| Neon Free | 0.5GB BD, 191 horas compute | $0 (suficiente para MVP) |
| Dominio custom | Opcional | $10-15/año |

**Total para MVP: $0-5/mes** (con Neon free).

---

## 9. Actualizaciones futuras

Cada vez que hagas `git push` a la rama principal, Railway:
1. Construye la nueva imagen
2. Aplica las nuevas migraciones (si las hay)
3. Reinicia el servicio
4. Verifica el healthcheck
5. Si algo falla → rollback automático a la versión anterior

Para trabajar con preview deployments: conectá una rama de feature y Railway crea un deployment separado por rama.

---

## 10. Próximos pasos (después del MVP)

- **Monitoreo**: integrar Sentry para tracking de errores
- **Logs centralizados**: LogDNA o Better Stack
- **Backups automáticos de Neon**: configurar snapshot diario
- **CDN para assets estáticos**: Cloudflare frente a Railway
- **CI/CD**: GitHub Actions para correr tests antes del deploy

---

*Para más info, ver `GUIA-LOCAL.md` (uso en desarrollo) y `README.md` (overview del proyecto).*
