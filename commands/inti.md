---
description: "Bootstrap a greenfield (no-code-yet) project: invoke the inti agent to run a structured discovery interview and produce docs/discovery/vision.md + requirements.md. Use once, at day 0, before any code exists. Feeds into /arki (architecture bootstrap)."
argument-hint: "[descripción corta del proyecto, opcional]"
---

# Task: Discovery de un proyecto nuevo con inti

Arrancá un proyecto **greenfield** (idea sin código todavía) generando los
documentos de discovery que necesita `arki` para proponer la arquitectura.

**Portabilidad**: el vault se lee de `$KURAKA_VAULT` (fallback al default del
autor). No requiere `kuraka.config.yaml` ni `.claude/project/` — inti opera en el
día 0.

Descripción inicial del proyecto (si la hay): $ARGUMENTS

## Paso 1 — Verificar que es greenfield

Si el proyecto YA tiene código fuente o un `kuraka.config.yaml`, PARÁ y avisá al
usuario: esto es brownfield → usar `/amauta` en su lugar. inti es solo para
proyectos que existen únicamente como idea.

## Paso 2 — Invocar al agente inti

Invocá el subagente **`inti`** (Task tool, `subagent_type: inti`) con estas
instrucciones:

> Conducí la entrevista de discovery (8–15 preguntas, una por turno, adaptativa)
> siguiendo tu definición. No propongas arquitectura (eso es de `arki`). Al
> terminar, escribí `docs/discovery/vision.md` y `docs/discovery/requirements.md`,
> y presentá el resumen (≤300 palabras) para que el usuario apruebe antes de
> pasar a arki.

Si la Task falla porque `inti` no es un subagente conocido, los agentes no están
registrados: decile al usuario que reinicie Claude Code (`/exit` + sesión nueva)
y corra `/inti` de nuevo — los subagentes se registran solo al iniciar sesión.

## Paso 3 — Relevar la salida de inti

Presentá el resumen de inti (visión, requisitos, integraciones, preguntas
abiertas) y la pregunta de aprobación. No marques el discovery como listo hasta
que el usuario confirme los documentos.

## Notas

- Corré esto **una vez por proyecto nuevo**. Después: `/arki` para la arquitectura,
  y luego `/kuraka <requerimiento>` para el primer ciclo.
- inti no escribe código — solo `docs/discovery/`.
