
# Security Audit — Auditoría de Seguridad de Código

Detecta vulnerabilidades antes de que lleguen a producción. En sistemas que manejan datos de expedientes, pólizas y facturas, la seguridad no es opcional.

---

## OWASP Top 10 — Checklist de revisión

### A01 — Control de acceso roto
```python
# ❌ Vulnerable — cualquier usuario autenticado accede a cualquier expediente
@app.get("/expedientes/{id}")
def get_expediente(id: str, user=Depends(get_current_user)):
    return db.query(Expediente).filter(Expediente.id == id).first()

# ✅ Seguro — verificar que el expediente pertenece al usuario/delegación
@app.get("/expedientes/{id}")
def get_expediente(id: str, user=Depends(get_current_user)):
    expediente = db.query(Expediente).filter(
        Expediente.id == id,
        Expediente.delegacion_id == user.delegacion_id  # Row-level security
    ).first()
    if not expediente:
        raise HTTPException(status_code=404)  # No revelar 403 por enumeración
    return expediente
```

**Verificar:**
- [ ] Cada endpoint verifica que el recurso pertenece al usuario que lo solicita
- [ ] Los roles se verifican en el servidor, no en el cliente
- [ ] No hay endpoints administrativos sin autenticación
- [ ] Las rutas de archivos no permiten path traversal (`../../../etc/passwd`)

---

### A02 — Fallos criptográficos
**Verificar:**
- [ ] Contraseñas hasheadas con bcrypt/argon2, nunca MD5/SHA1
- [ ] Datos sensibles cifrados en reposo (DNI, IBAN, datos médicos)
- [ ] HTTPS obligatorio en producción (no HTTP)
- [ ] Tokens JWT con expiración razonable (<24h para acceso, <30d para refresh)
- [ ] Secretos en variables de entorno, nunca en código fuente

```python
# ❌ Vulnerable
password_hash = hashlib.md5(password.encode()).hexdigest()
SECRET_KEY = "mi-secreto-hardcodeado-123"

# ✅ Seguro
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
SECRET_KEY = os.environ["JWT_SECRET_KEY"]  # Mínimo 32 chars aleatorios
```

---

### A03 — Inyección (SQL, NoSQL, OS, LDAP)
```python
# ❌ CRÍTICO — inyección SQL directa
query = f"SELECT * FROM expedientes WHERE compania = '{compania_input}'"
db.execute(query)

# ✅ Seguro — queries parametrizadas siempre
db.query(Expediente).filter(Expediente.compania == compania_input).all()
# O con SQL raw:
db.execute(text("SELECT * FROM expedientes WHERE compania = :c"), {"c": compania_input})
```

**También verificar:**
- [ ] Comandos de sistema operativo no construidos con input del usuario
- [ ] Deserialización de objetos solo de fuentes de confianza
- [ ] LDAP queries parametrizadas si se usa directorio corporativo

---

### A04 — Diseño inseguro
**Verificar:**
- [ ] Rate limiting en endpoints de autenticación (máx. 5 intentos/minuto)
- [ ] Validación de negocio en el servidor, no solo en el cliente
- [ ] Los flujos de recuperación de contraseña no revelan si el email existe
- [ ] Los IDs no son secuenciales (usar UUID para evitar enumeración)

---

### A05 — Configuración de seguridad incorrecta
```python
# ❌ Expone stack traces en producción
app = FastAPI(debug=True)

# ✅ Solo debug en desarrollo
app = FastAPI(debug=os.getenv("ENV") == "development")
```

**Verificar:**
- [ ] Headers de seguridad HTTP configurados (CORS restringido, no `*`)
- [ ] Cabeceras `X-Content-Type-Options`, `X-Frame-Options`, `HSTS`
- [ ] Páginas de error no revelan tecnología ni stack traces
- [ ] Directorios de administración no accesibles públicamente
- [ ] Variables de entorno de producción distintas a las de desarrollo

---

### A07 — Fallos de autenticación
**Verificar:**
- [ ] Tokens invalidados al hacer logout (blacklist o rotación)
- [ ] Refresh tokens de un solo uso
- [ ] MFA disponible para usuarios con acceso a datos sensibles
- [ ] Sesiones expiran por inactividad
- [ ] Logs de intentos fallidos de autenticación

---

### A09 — Fallos en registro y monitorización
```python
# ❌ Loguear datos sensibles
logger.info(f"Login: user={user.email}, password={password}")

# ✅ Solo loguear lo necesario, nunca credenciales
logger.info(f"Login exitoso: user_id={user.id}, ip={request.client.host}")
logger.warning(f"Login fallido: email_hash={hash(email)}, ip={request.client.host}")
```

**Verificar:**
- [ ] Logs de acceso a datos sensibles (expedientes, facturas)
- [ ] Alertas en patrones anómalos (muchos accesos en poco tiempo)
- [ ] Los logs NO contienen contraseñas, tokens, DNI ni IBAN

---

## GDPR — Datos personales en el código

Para sistemas que manejan datos de asegurados/siniestros:

**Inventario de datos personales:**
```markdown
| Dato | Tabla/Campo | Clasificación | Cifrado | Retención | Base legal |
|------|-------------|---------------|---------|-----------|------------|
| DNI titular | personas.dni | Identificativo | ✅ AES-256 | 5 años | Contrato |
| IBAN | facturacion.iban | Financiero | ✅ AES-256 | 7 años (fiscal) | Contrato |
| Email | usuarios.email | Contacto | No | Vida cuenta | Contrato |
| IP acceso | logs.ip | Técnico | No | 90 días | Interés legítimo |
```

**Verificar en el código:**
- [ ] Los datos personales no aparecen en logs
- [ ] Hay mecanismo de borrado/anonimización (derecho al olvido)
- [ ] Los datos no viajan a servicios de terceros sin consentimiento
- [ ] Los exports/backups también están cifrados

---

## Secretos expuestos — Búsqueda rápida

```bash
# Buscar secretos hardcodeados en el codebase
grep -rn "password\s*=" --include="*.py" --include="*.js" --include="*.ts" .
grep -rn "api_key\s*=" --include="*.py" --include="*.js" .
grep -rn "secret\s*=" --include="*.py" --include="*.js" .
grep -rn "BEGIN RSA PRIVATE KEY" .

# Verificar que .env no está en git
cat .gitignore | grep ".env"
git log --all --full-history -- "**/.env"
```

---

## Formato de informe de auditoría

```markdown
## Auditoría de Seguridad — [módulo/PR] — [fecha]

**Riesgo global:** 🔴 Alto / 🟠 Medio / 🟢 Bajo

### Vulnerabilidades encontradas

| # | Severidad | Categoría | Descripción | Línea | Solución |
|---|-----------|-----------|-------------|-------|---------|
| 1 | 🔴 CRÍTICA | Inyección SQL | Query construida con concatenación | L42 | Usar ORM o query parametrizada |
| 2 | 🟠 ALTA | Control acceso | Sin verificación de ownership | L78 | Añadir filtro por delegacion_id |

### Cumplimiento GDPR
- [ ] Datos personales identificados y mapeados
- [ ] Mecanismo de borrado implementado
- [ ] Logs sin datos sensibles

### Recomendaciones prioritarias
1. [Acción inmediata antes de producción]
2. [Acción en próximo sprint]
```
