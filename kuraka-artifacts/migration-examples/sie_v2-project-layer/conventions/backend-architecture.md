# Backend Architecture - FastAPI + PostgreSQL

---

## 1. Arquitectura por Capas (ESTRICTA)

```
Endpoint (Controller) --> Service --> Repository --> Database (SQLAlchemy)
```

| Capa | Responsabilidad | Puede Llamar | NO Puede Llamar |
|------|-----------------|--------------|-----------------|
| **Endpoint** | Manejo HTTP, validacion request/response, routing | Service | Repository, Database |
| **Service** | Logica de negocio, orquestacion, reglas de validacion | Repository, otros Services | Database directamente |
| **Repository** | Acceso a datos, queries, operaciones CRUD | Database (SQLAlchemy) | Endpoint, Service |

### Ejemplo correcto completo:
```python
# ✅ endpoints/tickets.py - SOLO maneja HTTP
@router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: int):
    return await ticket_service.get_by_id(ticket_id)

# ✅ services/ticket_service.py - Logica de negocio
async def get_by_id(ticket_id: int) -> Ticket:
    ticket = await ticket_repository.find_by_id(ticket_id)
    if not ticket:
        raise ErrNotFound("Ticket no encontrado")
    return ticket

# ✅ repositories/ticket_repository.py - SOLO acceso a datos
async def find_by_id(ticket_id: int) -> Ticket | None:
    return db.query(Ticket).filter(Ticket.id == ticket_id).first()
```

### Ejemplo PROHIBIDO:
```python
# ❌ PROHIBIDO - Endpoint accediendo a DB directamente (salta capas)
@router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    return db.query(Ticket).filter(Ticket.id == ticket_id).first()

# ❌ PROHIBIDO - Service haciendo queries directas
class TicketService:
    def get_by_id(self, ticket_id: int, db: Session):
        return db.query(Ticket).filter(Ticket.id == ticket_id).first()
```

---

## 2. Manejo de Errores

- **NUNCA** uses bloques try/except en endpoints o rutas
- El middleware de errores maneja automaticamente todas las excepciones
- Solo usa try/except en casos MUY especificos de logica interna (y documenta por que)
- Deja que las excepciones propaguen al middleware

### Ejemplo incorrecto:
```python
@app.get("/expedientes")
async def get_expedientes():
    try:  # ❌ NO HAGAS ESTO JAMAS
        return await expediente_service.get_all()
    except Exception as e:
        return {"error": str(e)}
```

### Ejemplo correcto:
```python
@app.get("/expedientes")
async def get_expedientes():
    return await expediente_service.get_all()  # ✅ El middleware maneja errores
```

### Excepciones de Dominio

Usa las excepciones definidas en `core/exceptions.py`:
```python
from core.exceptions import ErrNotFound, ErrValidation, ErrProviderError

# En servicios o repositorios (NUNCA en endpoints):
raise ErrNotFound("Expediente no encontrado")
raise ErrValidation("Rango de fechas invalido", details={"start": start, "end": end})
raise ErrProviderError("Asitur", "Error al autenticar", details={"status": 401})
```

---

## 3. Reglas NUNCA/SIEMPRE del Backend

### NUNCA:
- **NUNCA** try/except en endpoints ni services (excepto integraciones externas justificadas)
- **NUNCA** db.query() en services - usa repositories
- **NUNCA** logica de negocio en repositories (solo queries)
- **NUNCA** logica de negocio en endpoints (solo delegar a services)
- **NUNCA** valores hardcodeados - usa enums, .env o configuracion en BD
- **NUNCA** toques `core/` - si necesitas algo de core, habla con Enrique
- **NUNCA** imports dentro de funciones
- **NUNCA** codigo comentado - Git es el historial
- **NUNCA** `console.log` o `print()` - usa `logger`
- **NUNCA** credenciales en codigo fuente

### SIEMPRE:
- **SIEMPRE** Endpoint -> Service -> Repository -> DB (sin saltar capas)
- **SIEMPRE** imports al inicio del archivo (stdlib -> terceros -> locales)
- **SIEMPRE** nombres en ingles, snake_case para funciones/variables
- **SIEMPRE** funciones internas con prefijo `_`
- **SIEMPRE** queries parametrizadas
- **SIEMPRE** Enums para estados, tipos y categorias
- **SIEMPRE** schemas Pydantic para request/response
- **SIEMPRE** lee las reglas antes de escribir codigo
- **SIEMPRE** ejecutar `make test` desde `sie_v2/` ANTES de hacer commit — no hagas push esperando que el CI valide, cada fallo gasta tokens de GitHub Actions
- **SIEMPRE** corregir cualquier error de lint o test ANTES de hacer commit — nunca commit con errores conocidos
