# Backend Conventions (Python)

---

## 1. Convenciones de Nombres

- **Funciones y variables**: `snake_case` (`get_tickets`, `ticket_count`)
- **Clases**: `PascalCase` (`TicketService`, `BaseExtractor`)
- **Constantes**: `UPPER_SNAKE_CASE` (`MAX_RETRIES`, `DEFAULT_PAGE_SIZE`)
- **Archivos**: `snake_case.py` (`ticket_service.py`, `email_utils.py`)
- **Funciones internas**: `_prefijo` (`_validate_data`, `_build_response`)
- **Todos los nombres en INGLES** (documentacion puede ir en espanol)
- Minimo 3 caracteres (excepto `i`, `j` en bucles)
- **Parametros opcionales**: SIEMPRE usar `Tipo | None`, NUNCA `Optional[Tipo]`

```python
# ❌ MAL - Optional importado de typing
from typing import Optional

def get_users(role: Optional[str] = None) -> list[User]:
    ...

# ✅ BIEN - Union con None directa
def get_users(role: str | None = None) -> list[User]:
    ...
```

---

## 2. Valores Hardcodeados (EVITAR)

**EVITA** valores hardcodeados. Antes de hardcodear, preguntate:
- Puede cambiar por reglas de negocio? --> config o BD
- Administradores necesitarian modificarlo? --> BD
- Varia por cliente, region o configuracion? --> BD o .env
- Si la respuesta a CUALQUIERA es SI --> NO lo hardcodees

```python
# ❌ MAL
def fetch_expedientes():
    if days > 30:  # ¿De donde sale este 30?
        return []
    return await api.get(timeout=60)  # ¿Configurable?

# ✅ BIEN
from core.config import settings

def fetch_expedientes():
    if days > settings.MAX_FETCH_DAYS:  # Desde .env
        return []
    return await api.get(timeout=30)  # HARDCODED: timeout HTTP estandar
```

Si DEBES hardcodear un valor, anade un comentario breve explicando por que.

---

## 3. Variables de Entorno

Todas las configuraciones sensibles o variables deben estar en `.env`:

```env
# Database
POSTGRES_USER=sie
POSTGRES_PASSWORD=secure_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=sie_db

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480

# Entorno
ENVIRONMENT=development  # development, staging, production

# CORS
CORS_ORIGINS=http://localhost:3001,http://localhost:3000

# Diaple/Guai
DIAPLE_API_URL=https://api.diaple.com
DIAPLE_API_TOKEN=xxx

# Redis
REDIS_URL=redis://localhost:6379/0
```

---

## 4. Toma de Decisiones

- **SIEMPRE** pregunta al usuario antes de hacer cambios cuando haya cualquier duda sobre la intencion, alcance o enfoque
- Nunca asumas lo que el usuario quiere - si la solicitud es ambigua o puede interpretarse de mas de una manera, pregunta primero
- Esto aplica a todo tipo de cambios: codigo, prompts, configuracion, decisiones de arquitectura, etc.
