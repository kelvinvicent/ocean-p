# 🐙 Subir a GitHub — Guía de autenticación

Si te aparece un error de autenticación al hacer `git push`, esta es la solución.

---

## El error más común

```
remote: Support for password authentication was removed on August 13, 2021.
fatal: Authentication failed for 'https://github.com/kelvinvicent/ocean-p.git'
```

**Causa:** GitHub ya no acepta contraseñas. Necesitás un **Personal Access Token (PAT)**.

---

## Solución paso a paso

### 1. Crear un Personal Access Token (PAT)

1. Ir a https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Configurar:
   - **Note:** `OCEAN-P deploy` (lo que sea descriptivo)
   - **Expiration:** 90 days (o lo que prefieras)
   - **Scopes:** marcar solo **`repo`** (acceso al repo)
4. Click **"Generate token"**
5. **COPIAR EL TOKEN** — GitHub no lo vuelve a mostrar

### 2. Usar el token al hacer push

**Opción A — Una vez (te lo pide en el push):**

```bash
git push -u origin main
# Cuando pida usuario: tu-usuario-de-github
# Cuando pida contraseña: PEGAR EL TOKEN (no tu contraseña)
```

**Opción B — Guardarlo en Windows Credential Manager (recomendado):**

1. Windows busca credenciales en `manager` (ya configurado en tu sistema)
2. La primera vez que hagas push, ingresás usuario + token
3. Windows los guarda y no te vuelve a pedir

**Opción C — Usar SSH (más seguro, requiere setup):**

```bash
# Generar clave SSH (una sola vez)
ssh-keygen -t ed25519 -C "tu@email.com"
# Copiar la clave pública
cat ~/.ssh/id_ed25519.pub
# Pegarla en https://github.com/settings/keys
# Cambiar el remote a SSH
git remote set-url origin git@github.com:kelvinvicent/ocean-p.git
git push -u origin main
```

---

## Verificar que funcionó

Después del push exitoso, ir a https://github.com/kelvinvicent/ocean-p y deberías ver todos los archivos.

---

## Si el push falla por archivos grandes

Si te aparece algo como:
```
remote: error: File .venv/... is 102 MB; this exceeds GitHub's file size limit
```

Es porque el `.venv/` o algún archivo grande se está subiendo. Verificar:

1. **El .gitignore existe en la raíz** (ya está, lo creamos antes)
2. **Limpiar el cache de git:**
   ```bash
   git rm -r --cached .venv
   git rm -r --cached ocean_p.db
   git commit -m "Remove ignored files from tracking"
   git push
   ```

---

## Si el push es rechazado (non-fast-forward)

Si el repo en GitHub ya tiene commits (ej: un README inicial):

```bash
git pull --rebase origin main
git push
```

---

## Resumen — el flujo más común

```bash
# Primera vez (te pide usuario + token)
git push -u origin main

# Siguientes veces
git push
```
