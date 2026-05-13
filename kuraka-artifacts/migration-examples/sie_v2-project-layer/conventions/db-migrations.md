
# DB Migrations — Migraciones de Base de Datos Seguras

Las migraciones mal hechas causan los incidentes más graves: pérdida de datos, downtime, deploys que no se pueden revertir. Cada migración es una operación en producción.

---

## Principios fundamentales

1. **Cada migración es irreversible en producción** — aunque tengas `downgrade()`, los datos pueden haberse modificado
2. **Una migración = un cambio lógico** — no acumules 10 cambios en una sola migración
3. **Migraciones hacia adelante, no hacia atrás** — diseña para avanzar, no para deshacer
4. **Prueba el rollback en staging** — antes de tocar producción
5. **Sin datos hardcodeados en migraciones** — usa seeds separados

---

## Naming convention

```
YYYYMMDD_HHMMSS_descripcion_accion.py
YYYYMMDD_NNN_descripcion_accion.sql

# Ejemplos:
20260215_143022_expedientes_add_column_delegacion_id.py
20260215_144500_industriales_create_index_gremio.py
20260216_001_facturas_rename_table_to_facturas_compania.sql
```

**Verbos estándar:**
- `create_table_` — nueva tabla
- `add_column_` — nueva columna
- `drop_column_` — eliminar columna
- `rename_column_` — renombrar columna
- `create_index_` — nuevo índice
- `alter_column_` — modificar tipo o constraint
- `add_fk_` — nueva foreign key

---

## Plantilla de migración (Alembic / Python)

```python
"""Descripción clara de qué hace esta migración y por qué.

Contexto: [ticket o ADR relacionado]
Fecha: 2026-02-15
Autor: [nombre]

Impacto estimado:
- Tablas afectadas: expedientes
- Filas afectadas: ~50.000
- Tiempo estimado: < 1 segundo (ADD COLUMN con DEFAULT)
- ¿Requiere downtime?: No
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime

# Revision identifiers
revision = '20260215_143022'
down_revision = '20260210_091500'
branch_labels = None
depends_on = None


def upgrade():
    # Añadir columna nullable primero (sin downtime)
    op.add_column('expedientes',
        sa.Column('delegacion_id', sa.String(10), nullable=True)
    )
    
    # Poblar datos existentes (si hay lógica de migración de datos)
    op.execute("""
        UPDATE expedientes
        SET delegacion_id = 'ALC'
        WHERE delegacion_id IS NULL
        AND provincia = 'Alicante'
    """)
    
    # Añadir NOT NULL constraint solo después de poblar datos
    op.alter_column('expedientes', 'delegacion_id', nullable=False)
    
    # Crear índice si la columna se usará en filtros
    op.create_index('ix_expedientes_delegacion_id', 'expedientes', ['delegacion_id'])


def downgrade():
    # IMPORTANTE: downgrade solo borra la columna, los datos se pierden
    # Verificar en staging antes de ejecutar en producción
    op.drop_index('ix_expedientes_delegacion_id', table_name='expedientes')
    op.drop_column('expedientes', 'delegacion_id')
```

---

## Migraciones sin downtime (Zero-downtime)

### Añadir columna
```sql
-- ✅ Seguro — nullable primero, NOT NULL después
ALTER TABLE expedientes ADD COLUMN delegacion_id VARCHAR(10);
-- [deploy nueva versión de app que escribe el valor]
UPDATE expedientes SET delegacion_id = 'ALC' WHERE delegacion_id IS NULL;
ALTER TABLE expedientes ALTER COLUMN delegacion_id SET NOT NULL;
```

### Renombrar columna (estrategia expand-contract)
```
-- NUNCA: ALTER TABLE expedientes RENAME COLUMN estado TO estado_expediente;
-- (rompe la app si hay código en producción leyendo 'estado')

-- Proceso en 3 deploys:
-- Deploy 1: Añadir columna nueva, app escribe en ambas
ALTER TABLE expedientes ADD COLUMN estado_expediente VARCHAR(50);

-- Deploy 2: Migrar datos, app lee de la nueva columna
UPDATE expedientes SET estado_expediente = estado;

-- Deploy 3: Eliminar columna antigua, app ya no la usa
ALTER TABLE expedientes DROP COLUMN estado;
```

### Crear índice en tabla grande
```sql
-- ❌ Bloquea la tabla durante minutos/horas
CREATE INDEX ix_expedientes_fecha ON expedientes(fecha_apertura);

-- ✅ Sin bloqueo (PostgreSQL)
CREATE INDEX CONCURRENTLY ix_expedientes_fecha ON expedientes(fecha_apertura);
```

### Eliminar columna (con código legacy)
```
-- Fase 1: Deprecar en código (la app deja de leer/escribir la columna)
-- Fase 2: Verificar que nadie usa la columna (logs, monitoring, 2 semanas)
-- Fase 3: DROP COLUMN
```

---

## Tipos de cambio y su riesgo

| Cambio | Riesgo | Requiere downtime | Estrategia |
|--------|--------|-------------------|------------|
| ADD COLUMN nullable | 🟢 Bajo | No | Directo |
| ADD COLUMN NOT NULL con DEFAULT | 🟡 Medio | No en PG 11+ | Añadir DEFAULT primero |
| ADD COLUMN NOT NULL sin DEFAULT | 🔴 Alto | Sí | Expand-contract |
| DROP COLUMN | 🔴 Alto | No | Solo si app ya no la usa |
| RENAME COLUMN | 🔴 Alto | Sí si no se usa expand-contract | Expand-contract |
| CREATE INDEX | 🟡 Medio | No con CONCURRENTLY | CONCURRENTLY siempre |
| ADD FOREIGN KEY | 🟡 Medio | No con NOT VALID | Validar después |
| ALTER COLUMN TYPE | 🔴 Alto | Generalmente sí | Expand-contract |

---

## Checklist antes de ejecutar en producción

```
Preparación:
[ ] La migración tiene descripción, autor y ticket de referencia
[ ] Se ha probado en desarrollo y staging
[ ] Se ha probado el downgrade en staging
[ ] Se conoce el tiempo estimado de ejecución
[ ] Se tiene backup reciente de la BD

Seguridad de datos:
[ ] La migración no borra datos sin backup previo
[ ] Si hay transformación de datos, se ha verificado la lógica con muestra real
[ ] Las columnas eliminadas llevan al menos 2 semanas sin uso en app

Ejecución:
[ ] Comunicado al equipo antes de ejecutar
[ ] Monitoring activo durante la ejecución
[ ] Plan de rollback documentado y probado
```

---

## Documentación del esquema

Mantén `docs/schema.md` actualizado tras cada migración:

```markdown
## Tabla: expedientes

| Columna | Tipo | Nullable | Default | Descripción |
|---------|------|----------|---------|-------------|
| id | UUID | No | gen_random_uuid() | Identificador único |
| estado | VARCHAR(50) | No | 'abierto' | Estado del expediente (abierto/gestion/cerrado) |
| delegacion_id | VARCHAR(10) | No | — | Código delegación (ALC/VLC/CAS) |
| compania_codigo | VARCHAR(20) | No | — | Código compañía aseguradora |
| fecha_apertura | TIMESTAMP | No | NOW() | Fecha/hora de apertura |
| industrial_id | UUID | Sí | NULL | Industrial asignado (NULL si pendiente) |

**Índices:**
- `ix_expedientes_delegacion_id` — filtros por delegación
- `ix_expedientes_compania_fecha` — reporting por compañía y período

**Relaciones:**
- `delegacion_id` → `delegaciones.codigo`
- `industrial_id` → `industriales.id`
```
