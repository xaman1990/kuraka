
# Insurance API Connector — Integraciones con Compañías Aseguradoras

Patrones, plantillas y buenas prácticas para integrar el ERP GUAI con los sistemas de las compañías aseguradoras del sector multiasistencia.

---

## Contexto del dominio

Las integraciones con aseguradoras tienen particularidades críticas:
- **Sistemas heterogéneos**: cada compañía tiene su propia API, formato y vocabulario
- **Asincronía**: los cambios de estado viajan en ambas direcciones con retardo
- **Alta consecuencia del error**: un expediente mal sincronizado puede suponer pérdida económica
- **Quirks por compañía**: Generali usa fechas DD/MM/YYYY, AXA usa IDs numéricos de 8 dígitos, etc.

---

## Flujos estándar de integración

### Ciclo de vida de un expediente

```
GUAI ERP                          Compañía Aseguradora
    │                                      │
    ├──[1. Apertura]──────────────────────►│  POST /siniestros
    │◄─────────────────[ACK + ID externo]──┤  → 201 {"ref_compania": "GEN-2026-001"}
    │                                      │
    ├──[2. Asignación industrial]──────────►│  PUT /siniestros/{ref}/industrial
    │◄─────────────────────────────[ACK]───┤
    │                                      │
    │◄──[3. Validación presupuesto]─────────┤  WEBHOOK → /api/webhooks/presupuesto
    │                                      │
    ├──[4. Confirmación visita]────────────►│  POST /siniestros/{ref}/visita
    │                                      │
    ├──[5. Cierre + factura]───────────────►│  POST /siniestros/{ref}/factura
    │◄─────────────────────────────[ACK]───┤
```

---

## Plantilla de conector por compañía

```python
"""
Conector: [Nombre Compañía]
Versión API: [v1/v2]
Protocolo: REST / SOAP / AS2
Autenticación: OAuth2 / API Key / Certificado mTLS
Entorno producción: https://api.compania.com/v2
Entorno staging: https://api-test.compania.com/v2
Documentación: [URL doc oficial]
Contacto técnico: [nombre] — [email]
Última verificación: YYYY-MM-DD

Quirks conocidos:
- Las fechas van en formato DD/MM/YYYY (no ISO 8601)
- El campo 'estado' puede devolver null en expedientes > 6 meses
- Rate limit: 100 req/min — usar exponential backoff desde el primer 429
"""

class ConectorGenerali:

    # Mapeo de estados GUAI → estados Generali
    ESTADO_MAP = {
        "abierto":     "NUEVO",
        "en_gestion":  "EN_TRAMITE",
        "cerrado":     "CERRADO",
        "anulado":     "ANULADO",
    }

    # Mapeo de gremios GUAI → códigos Generali
    GREMIO_MAP = {
        "fontanería":   "FON",
        "electricidad": "ELE",
        "carpintería":  "CAR",
        "pintura":      "PIN",
        "cristalería":  "CRI",
    }
```

---

## Patrones críticos de integración

### Idempotencia — evitar duplicados

```python
def enviar_apertura_expediente(expediente_id: str) -> dict:
    """
    Usa el expediente_id como idempotency key.
    Si la compañía ya recibió este expediente, devuelve el registro existente
    en lugar de crear uno nuevo.
    """
    return requests.post(
        f"{BASE_URL}/siniestros",
        headers={
            "Authorization": f"Bearer {get_token()}",
            "Idempotency-Key": expediente_id,  # ← CRÍTICO
            "Content-Type": "application/json",
        },
        json=mapear_expediente_a_formato_compania(expediente_id),
    )
```

### Reintentos con exponential backoff

```python
import time
from typing import Callable

def con_reintento(
    funcion: Callable,
    max_intentos: int = 5,
    base_segundos: float = 1.0,
    errores_reintentables: tuple = (429, 500, 502, 503, 504),
) -> dict:
    """
    Reintenta la llamada con backoff exponencial.
    Los errores 4xx (salvo 429) son definitivos — no reintentar.
    """
    for intento in range(max_intentos):
        try:
            respuesta = funcion()
            respuesta.raise_for_status()
            return respuesta.json()
        except requests.HTTPError as e:
            codigo = e.response.status_code
            if codigo not in errores_reintentables or intento == max_intentos - 1:
                raise
            espera = base_segundos * (2 ** intento)
            logger.warning(f"Reintento {intento+1}/{max_intentos} en {espera}s — HTTP {codigo}")
            time.sleep(espera)
```

### Reconciliación de estados

```python
"""
Ejecutar cada hora para detectar desincronizaciones entre GUAI y las compañías.
Un expediente 'cerrado' en GUAI pero 'EN_TRAMITE' en la compañía indica
que el webhook de cierre no llegó — hay que reenviar.
"""
async def reconciliar_expedientes_abiertos(compania: str, horas: int = 24):
    expedientes_guai = obtener_expedientes_por_estado("en_gestion", compania, horas)
    
    discrepancias = []
    for exp in expedientes_guai:
        estado_compania = await consultar_estado_en_compania(exp.ref_externa, compania)
        if estado_compania != ESTADO_MAP[exp.estado]:
            discrepancias.append({
                "expediente_id": exp.id,
                "ref_compania": exp.ref_externa,
                "estado_guai": exp.estado,
                "estado_compania": estado_compania,
            })
    
    if discrepancias:
        logger.error(f"Reconciliación: {len(discrepancias)} discrepancias en {compania}")
        alertar_equipo_operaciones(discrepancias)
    
    return discrepancias
```

---

## Gestión de webhooks entrantes

```python
@app.post("/api/webhooks/{compania}")
async def recibir_webhook(
    compania: str,
    payload: dict,
    signature: str = Header(alias="X-Signature"),
):
    # 1. Verificar firma (evitar webhooks falsos)
    if not verificar_firma(payload, signature, SECRET_POR_COMPANIA[compania]):
        raise HTTPException(status_code=401, detail="Firma inválida")
    
    # 2. Responder 200 INMEDIATAMENTE (antes de procesar)
    # La compañía reintentará si no recibe 200 en < 5 segundos
    background_tasks.add_task(procesar_webhook, compania, payload)
    return {"status": "recibido"}

async def procesar_webhook(compania: str, payload: dict):
    # 3. Procesar de forma idempotente
    evento_id = payload.get("event_id")
    if await ya_procesado(evento_id):
        logger.info(f"Webhook duplicado ignorado: {evento_id}")
        return
    
    await marcar_procesando(evento_id)
    # ... lógica de negocio ...
    await marcar_procesado(evento_id)
```

---

## Documentación de quirks por compañía

Mantener `docs/integraciones/quirks.md`:

```markdown
## Generali / Interpartner
- Fechas: DD/MM/YYYY (no ISO 8601)
- Timeout API: 30s (aumentar cliente a 35s)
- Rate limit: 100 req/min por token
- Estados no documentados: "PENDIENTE_PERITO" (tratarlo como "en_gestion")
- El campo `industrial_ref` puede ser null incluso en estados activos

## AXA
- IDs siempre numéricos de 8 dígitos (padding con ceros: "00001234")
- Webhook de cierre llega con 2-5 min de retardo habitual
- Entorno de staging comparte BBDD con otro cliente — no usar datos reales

## Mapfre
- Autenticación: certificado mTLS (renovar antes del [fecha])
- API SOAP — usar cliente zeep, no requests
- Los errores de negocio devuelven HTTP 200 con campo "resultado": "ERROR"
```

---

## Checklist de nueva integración

- [ ] Entorno de staging/sandbox disponible y documentado
- [ ] Credenciales en Vault, no en código ni en `.env` del repo
- [ ] Mapeo completo de estados y campos documentado
- [ ] Idempotency key implementado en todas las escrituras
- [ ] Exponential backoff configurado
- [ ] Webhook con verificación de firma
- [ ] Reconciliación periódica programada
- [ ] Quirks conocidos documentados
- [ ] Tests de contrato con mocks realistas
- [ ] Runbook de incidentes específico para esta compañía
