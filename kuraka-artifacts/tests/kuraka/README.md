# Kuraka Evaluation Harness

> Tests que validan el sistema de agentes del Kuraka **sin invocarlos
> realmente**. Comprueban estructura, contratos y frontmatter — no corren
> agentes contra una API (eso sería caro y no determinista).

## Propósito

Detectar drift en el sistema Kuraka antes de que llegue a producción:

- Frontmatter de agentes válido (name, description, model entre opus/sonnet/haiku)
- Todos los agentes referenciados en `kuraka.md` existen como archivo
- Todas las skills referenciadas existen
- `output-schemas.md` tiene entrada para cada agente
- Cada agente menciona su propio skill correctamente
- No quedan referencias huérfanas al nombre viejo (`workflow`)
- Fixtures sintéticas de REQ/Story/TestPlan satisfacen el schema

## Estructura

```
tests/kuraka/
├── README.md                     ← este archivo
├── conftest.py                   ← fixtures (paths al repo, fixtures sintéticas)
├── fixtures/
│   ├── sample_req.md             ← REQ sintético para tests estructurales
│   └── sample_story.md           ← Story sintética
└── test_structure.py             ← tests de estructura (estáticos)
```

## Qué NO testea (por diseño)

- **Calidad de output de un agente en ejecución**: requiere invocación real, es
  costoso, no determinista, y el modelo cambia. Para eso usa retros del ciclo.
- **Comportamiento dinámico del orquestador**: difícil de simular sin Claude
  Code runtime. Cubrir vía retros manuales.
- **Performance real de tokens**: medible vía telemetría post-ejecución
  (`aggregate-telemetry.py`), no aquí.

## Ejecutar

```bash
cd sie_v2
python3 -m pytest tests/kuraka/ -v
```

## Extender

Cada nuevo chequeo estructural va como un test nuevo en `test_structure.py`
o en un fichero nuevo si es un dominio distinto (p.ej. `test_fixtures.py`
para validar que las fixtures sintéticas cumplen el schema).

Reglas:
- Tests deterministas, sin red, sin LLM
- Nombres `test_should_{check}_{when}`
- AAA pattern
- Sin side effects en el repo
