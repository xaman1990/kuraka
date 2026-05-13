# Organizacion de Archivos y Patron Orquestador

---

## 1. Limite de Lineas por Archivo (ESTRICTO)

| Umbral | Accion |
|--------|--------|
| 0 - 500 lineas | Normal, archivo saludable |
| 500 - 700 lineas | **ATENCION**: Evalua si ya hay que dividir |
| 700+ lineas | **OBLIGATORIO**: Refactoriza AHORA. Divide en subarchivos |
| 1000 lineas | **PROHIBIDO**: Ningun archivo debe llegar NUNCA a 1000 lineas |

### Funciones: Maximo 50 lineas (ideal 20-30)

Si una funcion supera 50 lineas, extrae helpers con prefijo `_`.

---

## 2. Vision de Developer: Prevenir ANTES de que crezca

No esperes a que un archivo llegue a 700 lineas. Debes **ANTICIPAR** el crecimiento:

- Si un service tiene 5 metodos y vas a agregar 5 mas --> divide ANTES
- Si un endpoint file tiene 8 rutas y vas a agregar 4 mas --> divide ANTES
- Si un modelo tiene muchas relaciones y metodos helper --> separa los helpers
- Si un schema file tiene 10+ schemas --> agrupa por dominio en carpeta

**Preguntate SIEMPRE antes de escribir codigo nuevo**:
1. Si agrego esto, el archivo superara 500 lineas?
2. Este archivo ya tiene mas de una responsabilidad?
3. Puedo agrupar estas funciones en un submodulo con nombre propio?

Si la respuesta a CUALQUIERA es SI --> **refactoriza primero, implementa despues**.

---

## 3. Patron Orquestador (Como Dividir Archivos Grandes)

Cuando un archivo crece, NO lo dejes crecer. Usa el **patron orquestador**: el archivo principal se convierte en un punto de entrada que importa y coordina funciones de subarchivos especializados.

### 3.1. Cuando Aplicar

- Un service tiene mas de 5-6 metodos publicos
- Un store/service maneja mas de 2 dominios de logica
- Un archivo de endpoints tiene mas de 6-8 rutas
- Funciones helper se acumulan al final del archivo
- El archivo ya supera 400 lineas y va a seguir creciendo

### 3.2. Patron 1: Carpeta con __init__.py como Fachada

El archivo original se convierte en carpeta. El `__init__.py` actua como fachada publica que re-exporta las funciones. **Quien importa el modulo no sabe que esta dividido internamente.**

```
# ANTES (archivo unico que crece sin control):
services/
    ticket_service.py          # 800 lineas - DEMASIADO

# DESPUES (carpeta orquestadora):
services/
    ticket/
        __init__.py            # Fachada: re-exporta funciones publicas (~50 lineas)
        crud.py                # create, update, delete, get_by_id (~150 lineas)
        assignment.py          # auto_assign, reassign, get_assignable_users (~120 lineas)
        state_machine.py       # transition_status, validate_transition (~100 lineas)
        search.py              # search_tickets, filter, paginate (~130 lineas)
        notifications.py       # notify_created, notify_assigned, notify_resolved (~100 lineas)
```

El `__init__.py` como fachada:
```python
# services/ticket/__init__.py
"""Servicio de tickets - punto de entrada publico.
Quien importa este modulo no necesita saber la estructura interna."""

from .crud import create_ticket, update_ticket, delete_ticket, get_by_id
from .assignment import auto_assign, reassign_ticket, get_assignable_users
from .state_machine import transition_status, validate_transition
from .search import search_tickets, get_paginated
from .notifications import notify_ticket_event

# Uso externo (igual que antes de dividir):
# from services.ticket import create_ticket, auto_assign
```

### 3.3. Patron 2: Carpeta helpers/ para Funciones Auxiliares

Cuando un archivo tiene muchas funciones helper internas (con `_prefijo`), extraelas a una carpeta `helpers/`.

```
# ANTES:
stores/
    ticket_store.py            # 600 lineas, 15 helpers al final

# DESPUES:
stores/
    ticket_store.py            # 200 lineas - solo logica principal
    helpers/
        __init__.py            # Re-exporta helpers
        ticket_mappers.py      # map_ticket_to_dto, map_dto_to_ticket
        ticket_parsers.py      # parse_filters, parse_dates, parse_sort
        ticket_validators.py   # validate_transition, validate_assignment
```

Uso desde el archivo principal:
```python
# stores/ticket_store.py
from .helpers.ticket_mappers import map_ticket_to_dto, map_dto_to_ticket
from .helpers.ticket_parsers import parse_filters, parse_date_range
from .helpers.ticket_validators import validate_transition

def get_filtered_tickets(filters: dict) -> list[TicketDTO]:
    parsed = parse_filters(filters)
    tickets = ticket_repository.find_by_filters(parsed)
    return [map_ticket_to_dto(t) for t in tickets]
```

### 3.4. Patron 3: Routers Anidados por Dominio (Endpoints)

Para endpoints, agrupa rutas por dominio en archivos separados y registralos desde un router padre.

```
# ANTES:
endpoints/
    ticketera.py               # 40 rutas, 900 lineas - PROHIBIDO

# DESPUES:
endpoints/
    ticketera/
        __init__.py            # Router principal, incluye sub-routers
        tickets.py             # CRUD tickets (8 rutas)
        comments.py            # CRUD comentarios (5 rutas)
        files.py               # Upload/download archivos (4 rutas)
        admin.py               # Admin categorias, urgencias, modulos (12 rutas)
        notifications.py       # Notificaciones (4 rutas)
        search.py              # Busqueda y filtros avanzados (3 rutas)
```

El `__init__.py` registra sub-routers:
```python
# endpoints/ticketera/__init__.py
from fastapi import APIRouter
from .tickets import router as tickets_router
from .comments import router as comments_router
from .files import router as files_router
from .admin import router as admin_router
from .notifications import router as notifications_router

router = APIRouter(prefix="/ticketera", tags=["Ticketera"])
router.include_router(tickets_router)
router.include_router(comments_router)
router.include_router(files_router)
router.include_router(admin_router)
router.include_router(notifications_router)
```

### 3.5. Patron 4: Calculations/Logic Split

Cuando un service tiene calculos complejos, separa cada tipo de calculo.

```
# ANTES:
services/baremos_service.py    # 700 lineas con calculos mezclados

# DESPUES:
services/
    baremos/
        __init__.py            # Fachada
        pipeline.py            # Orquestador principal del flujo
        extraction.py          # Logica de extraccion de datos de ficheros
        comparison.py          # Comparaciones CIA vs GUAI
        matrix.py              # Calculos de matriz de equivalencias
        output.py              # Generacion de ficheros de salida
```

---

## 4. Regla de Oro del Orquestador

El archivo orquestador (`__init__.py`, `pipeline.py`, archivo principal) debe:

1. **Ser corto** (maximo 100-150 lineas)
2. **No contener logica** - solo coordinar llamadas a submodulos
3. **Importar y delegar** - cada paso es una llamada
4. **Leerse como un indice** - al leerlo entiendes todo el flujo sin ver detalles

```python
# ✅ BIEN - Se lee como un indice de capitulos
def process_baremos_job(job_id: str) -> JobResult:
    job = job_repository.get_by_id(job_id)
    companies = extraction.scan_uploaded_files(job.upload_path)

    results = []
    for company in companies:
        extractor = get_extractor(company.name)
        raw_data = extractor.extract(company.file_path)
        normalized = extractor.normalize(raw_data)
        compared = comparison.compare_with_guai(normalized, company.guai_data)
        report = output.generate_report(compared)
        results.append(report)

    return JobResult(job_id=job_id, results=results)
```
