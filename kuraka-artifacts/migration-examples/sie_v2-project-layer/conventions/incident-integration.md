
# Incident Integration — Runbooks de Incidentes de Integración

Los incidentes de integración son los más difíciles de diagnosticar: el problema puede estar en tu sistema, en la red, o en el sistema externo. Este runbook estructura el proceso de diagnóstico.

---

## Árbol de decisión de diagnóstico rápido

```
¿El problema afecta a TODOS los expedientes o solo a algunos?
    ├── TODOS → Problema de conectividad o autenticación (Nivel 1)
    └── ALGUNOS → Problema de datos o lógica (Nivel 2)

¿El problema es en envío (GUAI → Compañía) o recepción (Compañía → GUAI)?
    ├── ENVÍO → Revisar cola de salida, logs del conector
    └── RECEPCIÓN → Revisar logs de webhook, estado del endpoint receptor
```

---

## Runbook: API de aseguradora no responde

**Síntomas:** Timeouts, connection refused, HTTP 502/503/504

```bash
# 1. Verificar conectividad básica
curl -v --max-time 10 https://api.generali.com/health
ping api.generali.com

# 2. Verificar si el problema es nuestro firewall/proxy
curl -v --max-time 10 https://api.generali.com/health --proxy http://proxy-interno:3128

# 3. Consultar estado publicado de la compañía
# Generali: https://status.generali.es
# AXA: https://status.axa.es

# 4. Revisar si hay expiración de certificado (mTLS)
openssl s_client -connect api.generali.com:443 -showcerts 2>/dev/null | \
  openssl x509 -noout -dates

# 5. Ver cola de mensajes pendientes
SELECT COUNT(*), MIN(created_at) as mas_antiguo
FROM mensajes_salida
WHERE estado = 'pendiente' AND compania = 'GENERALI';
```

**Acción mientras dura el incidente:**
```python
# Los mensajes NO se pierden — van a la cola de reintentos
# Verificar que el job de reintentos está activo
systemctl status guai-retry-worker

# Si el worker está caído, reiniciarlo
systemctl restart guai-retry-worker

# Ver estado de la cola
redis-cli llen "cola:reintentos:generali"
```

**Comunicación al equipo operaciones:**
```
⚠️ INTEGRACIÓN GENERALI DEGRADADA
Inicio: HH:MM
Impacto: Expedientes pendientes de sincronización: N
Estado: Mensajes en cola, se procesarán automáticamente cuando la API se recupere
Próxima actualización: en 30 minutos
```

---

## Runbook: Expedientes desincronizados (estados distintos en GUAI y compañía)

**Síntomas:** Expediente "cerrado" en GUAI pero "EN_TRAMITE" en la compañía, o viceversa

```sql
-- 1. Identificar expedientes con discrepancia
SELECT
    e.id,
    e.ref_externa_generali,
    e.estado AS estado_guai,
    s.estado_compania,
    e.updated_at AS ultima_modificacion_guai,
    s.consultado_en
FROM expedientes e
JOIN sincronizacion_estados s ON s.expediente_id = e.id
WHERE e.estado != s.estado_mapeado
  AND e.compania = 'GENERALI'
ORDER BY e.updated_at DESC;
```

```python
# 2. Para cada expediente desincronizado, decidir cuál es la fuente de verdad
# Regla: el estado más reciente gana, pero SIEMPRE con revisión humana

async def resolver_discrepancia(expediente_id: str, compania: str):
    estado_guai = obtener_estado_guai(expediente_id)
    estado_compania = await consultar_api_compania(expediente_id, compania)
    
    logger.info(f"Discrepancia {expediente_id}: GUAI={estado_guai}, {compania}={estado_compania}")
    
    # No resolver automáticamente — crear tarea para revisión manual
    crear_tarea_operaciones(
        tipo="discrepancia_estado",
        expediente_id=expediente_id,
        detalle=f"GUAI: {estado_guai} | {compania}: {estado_compania}",
        prioridad="alta" if estado_guai == "cerrado" else "media"
    )
```

---

## Runbook: Webhooks entrantes que no llegan

**Síntomas:** La compañía dice que envió el webhook pero no se registró en GUAI

```bash
# 1. Verificar que el endpoint de webhooks está activo
curl -X POST https://api.guaierp.com/api/webhooks/generali \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
# Esperado: 200 {"status": "recibido"}

# 2. Revisar logs del servidor de webhooks (últimas 2 horas)
journalctl -u guai-api --since "2 hours ago" | grep "webhook"

# 3. Verificar que el webhook no llegó con firma inválida
grep "Firma inválida" /var/log/guai/webhooks.log | tail -20

# 4. Verificar si el problema es el SSL (certificado del servidor)
openssl s_client -connect api.guaierp.com:443 2>/dev/null | openssl x509 -noout -dates

# 5. Comprobar si la IP de la compañía está en el whitelist
# (si tenemos whitelist de IPs para webhooks)
cat /etc/nginx/conf.d/webhooks-whitelist.conf | grep "generali"
```

**Si el webhook llegó pero falló en procesamiento:**
```sql
-- Ver webhooks recibidos pero con error de procesamiento
SELECT evento_id, compania, recibido_en, error, intentos
FROM webhooks_log
WHERE estado = 'error'
  AND recibido_en > NOW() - INTERVAL '24 hours'
ORDER BY recibido_en DESC;

-- Reprocesar webhook específico
UPDATE webhooks_log SET estado = 'pendiente', intentos = 0 WHERE evento_id = 'XXX';
```

---

## Runbook: Token de autenticación expirado

**Síntomas:** HTTP 401 en todas las llamadas a una compañía concreta

```bash
# 1. Confirmar que es un problema de autenticación
grep "401\|Unauthorized\|token" /var/log/guai/integraciones.log | tail -20

# 2. Renovar token manualmente
python3 manage.py renovar_token --compania generali --force

# 3. Verificar que el token nuevo funciona
python3 manage.py test_conexion --compania generali

# 4. Si usa certificado mTLS, verificar vigencia
openssl pkcs12 -in certs/generali-client.p12 -noout -info 2>/dev/null | grep "Not After"

# 5. Procesar cola de mensajes pendientes tras renovar token
python3 manage.py reprocesar_cola --compania generali --desde "hace 2 horas"
```

---

## Dashboard de salud de integraciones

```sql
-- Vista rápida del estado de todas las integraciones
SELECT
    compania,
    COUNT(*) FILTER (WHERE estado = 'pendiente') AS pendientes,
    COUNT(*) FILTER (WHERE estado = 'error' AND created_at > NOW() - INTERVAL '1h') AS errores_ultima_hora,
    MAX(last_success_at) AS ultimo_exito,
    EXTRACT(EPOCH FROM (NOW() - MAX(last_success_at)))/60 AS minutos_sin_exito
FROM mensajes_salida
GROUP BY compania
ORDER BY errores_ultima_hora DESC;
```

---

## Escalado y contactos

| Compañía | Contacto técnico | Teléfono incidencias | Portal de estado |
|---|---|---|---|
| Generali | [nombre] | +34 XXX XXX | status.generali.es |
| AXA / Interpartner | [nombre] | +34 XXX XXX | status.axa.es |
| Mapfre | [nombre] | +34 XXX XXX | — |
