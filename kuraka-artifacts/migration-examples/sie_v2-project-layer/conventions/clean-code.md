# Clean Code (OBLIGATORIO)

---

## 1. Nombres Descriptivos

Los nombres deben explicar QUE hace la variable/funcion sin necesidad de leer el codigo.

```python
# ❌ MAL - Nombres cripticos
def proc(d, t):
    r = []
    for x in d:
        if x.s == t:
            r.append(x)
    return r

# ✅ BIEN - Se entiende al leerlo
def filter_tickets_by_status(tickets: list[Ticket], status: TicketStatus) -> list[Ticket]:
    return [ticket for ticket in tickets if ticket.status == status]
```

Reglas de nombres:
- Minimo 3 caracteres (excepto `i`, `j` en bucles)
- El nombre describe el CONTENIDO, no el TIPO (`ticket_payload` no `obj`, `postal_parts` no `x`)
- Funciones: verbo + sustantivo (`get_tickets`, `validate_email`, `send_notification`)
- Booleanos: prefijo `is_`, `has_`, `can_` (`is_active`, `has_attachments`, `can_reassign`)

---

## 2. Funciones Pequenas y Enfocadas

- **Maximo 50 lineas** por funcion (ideal 20-30)
- Una funcion hace **UNA cosa**
- Si necesitas comentarios para separar secciones, esas secciones deben ser funciones separadas
- **Siempre extrae a funciones** — bloques de logica deben ser funciones con nombre descriptivo. Pero **evalua si moverla a otro archivo**: si una funcion helper solo la usa una unica funcion en ese mismo archivo y no se reutiliza en ningun otro sitio, puede quedarse en el mismo archivo como funcion interna (`_prefijo`). No la muevas a un archivo separado solo por moverla — hazlo cuando haya reutilizacion real o el archivo crezca demasiado.

```python
# ❌ MAL - Funcion gigante que hace 5 cosas
def process_ticket(data):
    # Validar datos (20 lineas)
    if not data.get('title'):
        raise ...
    if not data.get('category'):
        raise ...
    # ... mas validaciones

    # Crear ticket (15 lineas)
    ticket = Ticket(...)
    db.add(ticket)
    # ...

    # Asignar usuario (25 lineas)
    users = get_available_users(...)
    best_user = find_best_match(...)
    # ...

    # Enviar notificacion (20 lineas)
    email = build_email(...)
    send_email(...)
    # ...

    return ticket  # 80+ lineas total

# ✅ BIEN - Orquestador corto que delega
def process_ticket(data: TicketCreate) -> Ticket:
    validated = _validate_ticket_data(data)
    ticket = ticket_repository.create(validated)
    _assign_to_user(ticket)
    notification_service.notify_new_ticket(ticket)
    metrics_service.increment_created(ticket.category)
    return ticket
```

### Antes de crear un helper, revisa `utils/`

**SIEMPRE** revisa la carpeta `utils/` antes de crear una funcion helper nueva. Puede que ya exista una funcion generica que haga lo mismo o algo muy similar.

Modulos clave en `utils/`:
- `converters.py` — conversiones de tipos, limpieza de strings, telefono, NIF, zip codes
- `date_utils.py` — normalizacion de fechas (ISO 8601, DD/MM/YYYY, RFC 2822)
- `email_parser.py` — parsing de emails IMAP

Si la funcion que necesitas **no existe pero es reutilizable** por otros servicios, creala en `utils/` directamente en vez de como helper privado (`_funcion`) dentro de tu modulo.

Si la funcion es **especifica** y no tiene sentido reutilizarla, entonces si puede quedarse como helper interno.

---

## 3. Early Return (Retorno Temprano)

Evita piramides de `if` anidados. Valida y retorna temprano.

```python
# ❌ MAL - Piramide de doom
def get_ticket_response(ticket_id, user):
    if user:
        if user.is_active:
            ticket = ticket_repository.find_by_id(ticket_id)
            if ticket:
                if ticket.module_id in user.modules:
                    return ticket
                else:
                    raise ErrAuthorization("Sin acceso al modulo")
            else:
                raise ErrNotFound("Ticket no encontrado")
        else:
            raise ErrAuthorization("Usuario inactivo")
    else:
        raise ErrAuthentication("No autenticado")

# ✅ BIEN - Flujo lineal, facil de leer
def get_ticket_response(ticket_id: int, user: User) -> Ticket:
    if not user:
        raise ErrAuthentication("No autenticado")
    if not user.is_active:
        raise ErrAuthorization("Usuario inactivo")

    ticket = ticket_repository.find_by_id(ticket_id)
    if not ticket:
        raise ErrNotFound("Ticket no encontrado")
    if ticket.module_id not in user.modules:
        raise ErrAuthorization("Sin acceso al modulo")

    return ticket
```

---

## 4. Enums en vez de Strings Magicos

NUNCA uses strings literales para estados, tipos o categorias. Usa Enums.

```python
# ❌ MAL - Strings magicos por todo el codigo
ticket.status = "en_proceso"
if ticket.priority == "alta":
    notify_urgently()

# ✅ BIEN - Enums tipados
class TicketStatus(str, Enum):
    UNASSIGNED = "sin_asignar"
    ASSIGNED = "asignado"
    IN_PROGRESS = "en_proceso"
    RESOLVED = "resuelto"
    OBSERVED = "observado"
    NOT_APPLICABLE = "no_procede"
    REOPENED = "reapertura"
    REASSIGNED = "reasignado"

class TicketPriority(str, Enum):
    LOW = "baja"
    MEDIUM = "media"
    HIGH = "alta"
    CRITICAL = "critica"

ticket.status = TicketStatus.IN_PROGRESS
if ticket.priority == TicketPriority.HIGH:
    notify_urgently()
```

---

## 5. No Comentarios Obvios

Comenta solo el **POR QUE**, nunca el **QUE**. El codigo debe explicarse solo.

```python
# ❌ MAL - Comentarios que repiten lo que se ve
i = 0  # Inicializar contador
tickets = []  # Lista vacia de tickets
ticket.status = "resolved"  # Cambiar status a resolved
# Recorrer todos los tickets
for ticket in tickets:
    pass

# ✅ BIEN - Comenta solo decisiones no obvias
# Timeout de 30s porque Asitur responde lento en horario pico (9-11h)
ASITUR_TIMEOUT = 30

# Reintento 3 veces porque la API de Generali tiene rate limiting agresivo
MAX_RETRIES = 3
```

---

## 6. Sin Codigo Muerto

- **NUNCA** dejes codigo comentado - Git es el historial
- **NUNCA** dejes funciones que no se usan
- **NUNCA** dejes imports sin usar
- Si algo se borra, se borra. No se comenta "por si acaso".
