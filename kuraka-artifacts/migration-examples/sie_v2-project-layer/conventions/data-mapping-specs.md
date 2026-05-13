
# Data Mapping Specs — Especificaciones de Transformación de Datos

El mapeo de datos es el corazón de cualquier integración. Una spec clara evita errores silenciosos, pérdida de datos y semanas de debugging.

---

## Plantilla de spec de mapeo

```markdown
# Data Mapping: [Sistema Origen] → [Sistema Destino]

**Versión:** 1.0.0  
**Fecha:** YYYY-MM-DD  
**Autor:** [nombre]  
**Trigger:** [Cuándo se ejecuta esta transformación]  
**Dirección:** Unidireccional / Bidireccional

---

## Objeto: [Nombre del objeto mapeado]

| Campo Origen | Tipo Origen | Campo Destino | Tipo Destino | Transformación | Requerido | Valor por defecto | Notas |
|---|---|---|---|---|---|---|---|
| `expediente_id` | string UUID | `ref_interna` | string | Sin transformación | ✅ | — | Usar como idempotency key |
| `fecha_apertura` | ISO 8601 datetime | `fecha_alta` | DD/MM/YYYY string | Reformatear fecha | ✅ | — | Generali no acepta ISO |
| `gremio` | enum GUAI | `cod_especialidad` | string 3 chars | Ver tabla GREMIO_MAP | ✅ | — | |
| `importe_presupuesto` | decimal(10,2) EUR | `importe` | integer céntimos | × 100, redondear | No | 0 | Convertir a céntimos |
| `industrial.nombre` | string | `nombre_proveedor` | string(100) | Truncar a 100 chars | No | null | |
| `delegacion_id` | enum (ALC/VLC/CAS) | `provincia` | string | Ver tabla DELEGACION_MAP | ✅ | — | |
| `notas_internas` | text | — | — | **NO mapear** | — | — | Campo privado, no enviar |

---

## Tablas de conversión

### GREMIO_MAP (GUAI → Generali)
| GUAI | Generali | Descripción |
|---|---|---|
| fontanería | FON | Trabajos de fontanería y saneamiento |
| electricidad | ELE | Instalaciones eléctricas |
| carpintería | CAR | Puertas, ventanas, muebles |
| pintura | PIN | Pintura interior/exterior |
| cristalería | CRI | Cristales y espejos |
| cerrajería | CER | Cerraduras y accesos |
| otro | OTR | Resto de especialidades |

### ESTADO_MAP (GUAI → Generali)
| GUAI | Generali | Condición adicional |
|---|---|---|
| abierto | NUEVO | — |
| en_gestion | EN_TRAMITE | — |
| pendiente_cliente | ESPERA_ASEGURADO | — |
| cerrado | CERRADO | Solo si `fecha_cierre` está informada |
| anulado | ANULADO | Incluir `motivo_anulacion` en el body |

---

## Reglas de transformación

### Fechas
```python
# GUAI usa ISO 8601, Generali usa DD/MM/YYYY
def formatear_fecha_generali(fecha_iso: str) -> str:
    """'2026-02-15T10:30:00Z' → '15/02/2026'"""
    return datetime.fromisoformat(fecha_iso.replace('Z', '+00:00')).strftime('%d/%m/%Y')
```

### Importes
```python
# GUAI almacena en euros con decimales, Generali espera céntimos enteros
def euros_a_centimos(importe_euros: Decimal) -> int:
    """10.50 → 1050"""
    return int((importe_euros * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
```

### Strings largos
```python
# Truncar con sufijo para indicar que se ha cortado
def truncar(texto: str, max_chars: int, sufijo: str = "...") -> str:
    if len(texto) <= max_chars:
        return texto
    return texto[:max_chars - len(sufijo)] + sufijo
```

---

## Manejo de nulos y valores por defecto

| Escenario | Tratamiento | Ejemplo |
|---|---|---|
| Campo requerido es null en origen | Error — no enviar, alertar | `expediente_id` null → excepción |
| Campo opcional es null en origen | Omitir campo del payload (no enviar `null`) | `notas` null → no incluir clave |
| Campo destino requerido, origen no existe | Usar valor por defecto documentado | `prioridad` → "NORMAL" |
| Enum no mapeado | Error con log + alerta operaciones | gremio "albanileria" sin mapa → error |

---

## Validación del mapping

```python
def validar_payload_antes_de_enviar(payload: dict, esquema: dict) -> list[str]:
    """
    Valida que el payload transformado cumple el esquema del destino.
    Devuelve lista de errores (vacía si todo OK).
    """
    errores = []
    for campo, regla in esquema["requeridos"].items():
        if campo not in payload or payload[campo] is None:
            errores.append(f"Campo requerido ausente: {campo}")
    for campo, tipo in esquema["tipos"].items():
        if campo in payload and not isinstance(payload[campo], tipo):
            errores.append(f"Tipo incorrecto en {campo}: esperado {tipo.__name__}")
    return errores
```

---

## Registro de cambios del mapping

```markdown
## Historial de cambios

| Fecha | Versión | Cambio | Motivo |
|---|---|---|---|
| 2026-02-15 | 1.0.0 | Versión inicial | Nueva integración Generali |
| 2026-03-01 | 1.1.0 | Añadir campo `cod_postal` | Requerido por nueva normativa |
| 2026-03-15 | 1.1.1 | Fix: `importe` en céntimos, no euros | Bug detectado en staging |
```
