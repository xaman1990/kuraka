# Project Structure and Monorepo Rules

---

## 1. Estructura del Proyecto y Separacion de Responsabilidades

| Carpeta | Responsabilidad |
|---------|-----------------|
| `api/endpoints/` | Definiciones de endpoints (rutas FastAPI) |
| `api/schemas/` | Modelos Pydantic (request/response) |
| `api/models/` | Modelos SQLAlchemy (tablas BD) |
| `api/services/` | Logica de negocio |
| `api/services/providers/` | Integraciones con aseguradoras (1 carpeta por provider) |
| `api/crud_config/` | Configuracion CRUD generico por entidad |
| `repositories/` | Acceso a datos (queries) |
| `utils/` | Utilidades comunes (guai_client, imap_helper, date_utils, etc.) |
| `core/` | Infraestructura base (NO TOCAR) |
| `tests/` | Tests pytest |

### Senales de mala ubicacion:
- Schemas Pydantic fuera de `schemas/`
- Logica de negocio en archivos de endpoint
- Queries SQL directas en services (deben estar en repositories)
- Funciones auxiliares dentro de services (deben estar en utils o helpers)

---

## 2. Estructura Completa del Monorepo

```
sie_v2/ (rama SIE-fastapi-DEV)
├── backend/
│   ├── main.py                      # Entry point unico FastAPI
│   ├── core/                        # SOLO ENRIQUE - NO TOCAR
│   │   ├── database.py              # 1 sola conexion PostgreSQL
│   │   ├── exceptions.py            # 1 sola jerarquia de errores
│   │   ├── exception_handlers.py    # Middleware global JSON
│   │   ├── jwt_utils.py             # 1 solo sistema auth JWT
│   │   ├── auth_dependencies.py     # get_current_user() + allow_roles()
│   │   ├── dev_tools.py             # is_dev(), is_prod(), is_testing()
│   │   ├── redis_client.py          # Conexion Redis
│   │   ├── rate_limiter.py          # slowapi
│   │   └── middleware/
│   │       └── jwt_middleware_auth.py
│   ├── api/                         # Toda la API vive aqui
│   │   ├── endpoints/
│   │   │   ├── auth.py
│   │   │   ├── system.py
│   │   │   ├── generic_crud.py
│   │   │   ├── tools/               # Carlos - baremos, duplicidad, proyecta
│   │   │   ├── ticketera/           # Raul - sistema de tickets
│   │   │   └── retell/
│   │   ├── models/                  # Modelos SQLAlchemy (tablas BD)
│   │   ├── schemas/                 # Modelos Pydantic (request/response)
│   │   ├── services/                # Logica de negocio
│   │   │   └── providers/           # 1 carpeta por aseguradora
│   │   │       ├── base.py
│   │   │       ├── factory.py
│   │   │       ├── asitur/
│   │   │       ├── generali/
│   │   │       ├── ima/
│   │   │       ├── multiasistencia/
│   │   │       ├── mutua_madrilena/
│   │   │       ├── caser/
│   │   │       ├── santander/
│   │   │       ├── pelayo/
│   │   │       ├── lagunaro/
│   │   │       ├── linea_directa/
│   │   │       ├── kutxa/
│   │   │       └── proyecta/
│   │   └── crud_config/             # Configuracion CRUD generico por entidad
│   ├── repositories/                # Acceso a datos (queries SQL via SQLAlchemy)
│   ├── utils/                       # Utilidades comunes (MG9)
│   │   ├── guai_client.py
│   │   ├── imap_helper.py
│   │   ├── date_utils.py
│   │   ├── phone_utils.py
│   │   └── zip_code_utils.py
│   ├── tests/
│   │   ├── conftest.py              # 1 solo conftest
│   │   ├── unit/
│   │   │   ├── providers/
│   │   │   ├── services/
│   │   │   └── utils/
│   │   └── integration/
│   ├── alembic/                     # 1 solo Alembic para todas las migraciones
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── requirements.txt
└── frontend/                        # Vue 3 + TypeScript (Daira)
    ├── src/
    │   ├── views/                   # Paginas (por modulo)
    │   │   ├── auth/
    │   │   ├── sie/
    │   │   ├── ticketera/
    │   │   ├── tools/
    │   │   └── admin/
    │   ├── components/              # Componentes reutilizables
    │   │   ├── layout/              # Sidebar, Header, MainLayout
    │   │   ├── common/              # Botones, Modals, Tables
    │   │   └── forms/               # Form inputs reutilizables
    │   ├── composables/             # Logica reutilizable
    │   │   ├── useAuth.ts
    │   │   ├── usePermissions.ts
    │   │   └── useWebSocket.ts
    │   ├── stores/                  # Pinia stores
    │   │   ├── authStore.ts
    │   │   └── notificationStore.ts
    │   ├── router/                  # Vue Router con guards
    │   ├── services/                # API client + llamadas
    │   │   └── apiClient.ts
    │   ├── types/                   # TypeScript types/interfaces
    │   └── assets/                  # Imagenes, fuentes
    ├── Dockerfile
    ├── nginx.conf
    └── package.json
```

---

## 3. Reglas del Monorepo

1. **NUNCA toques `core/`** - Si necesitas algo de core, habla con Enrique. El core lo mantiene solo el.
2. **Trabaja SOLO en tu area** - Raul en `api/endpoints/ticketera/`, Carlos en `api/endpoints/tools/`, Daira en `frontend/`
3. **Usa `utils/`** para utilidades comunes entre dominios (guai_client, imap_helper, date_utils, etc.)
4. **Un solo Alembic** - No crees configuraciones de migracion paralelas
5. **Un solo `conftest.py`** en `tests/` - No dupliques fixtures de test
6. **Rama**: `SIE-fastapi-DEV` - Siempre trabaja desde ahi
7. **Una sola PostgreSQL** - La de SIE. Ticketera migra de MySQL, Tools migra de SQLite. Todo va a la misma BD.
8. **NO crear carpetas paralelas** - Todo el codigo backend vive en `api/`, `repositories/`, `utils/`. Providers viven en `api/services/providers/`. No crear `modules/` ni estructuras alternativas.

---

## 4. VIOLACION DETECTADA: Estructuras Paralelas (Caso Real)

### El error: `modules/tools/`

Se creo una estructura paralela fuera de la arquitectura centralizada:

```
# ❌ INCORRECTO - Arquitectura paralela que rompe la estructura
modules/
    tools/
        endpoints/       # Duplica api/endpoints/
        models/          # Duplica api/models/
        schemas/         # Duplica api/schemas/
        services/        # Duplica api/services/
```

Esto es **INCORRECTO** porque:
- Crea un punto de entrada paralelo para endpoints
- Los modelos quedan fuera del sistema centralizado de migraciones
- Los schemas no se pueden compartir con otros modulos
- Los services quedan aislados, impidiendo reutilizacion

### La correccion:

```
# ✅ CORRECTO - Todo pasa por la arquitectura centralizada
api/
    endpoints/
        tools/           # Solo endpoints aqui
    models/              # Modelos compartidos (todos los modulos)
    schemas/             # Schemas compartidos (todos los modulos)
    services/            # Services compartidos (todos los modulos)
repositories/            # Repositories compartidos
```

### Regla estricta:

**NUNCA** crear carpetas tipo `modules/`, `features/`, `domains/` con su propia estructura `api/` interna. Todo pasa por la arquitectura centralizada definida en la seccion 1.

Si necesitas agrupar funcionalidad por dominio, hazlo **dentro** de las carpetas existentes:
- `api/endpoints/tools/baremos.py` - endpoints de baremos
- `api/services/baremos_service.py` - logica de baremos
- `api/schemas/baremos.py` - schemas de baremos
- `repositories/baremos_repository.py` - queries de baremos
