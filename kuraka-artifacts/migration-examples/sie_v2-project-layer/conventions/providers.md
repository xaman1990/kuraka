# Providers (Integraciones Externas)

---

## 1. Estructura de Providers

Los providers implementan la integracion con sistemas externos (Asitur, Generali, IMA, etc.).

```
api/services/providers/
├── base.py                # BaseProvider (ABC)
├── factory.py             # ProviderFactory (registry)
└── asitur/
    ├── __init__.py        # AsiturProvider(BaseProvider)
    ├── client.py          # Cliente HTTP para la API externa
    ├── processor.py       # Transformacion de datos crudos
    └── output.py          # Outbound a aseguradora (si aplica)
```

---

## 2. BaseProvider

```python
class BaseProvider:
    """Clase base para todos los providers."""
    async def authenticate(self) -> str:
        raise NotImplementedError
    async def fetch_expedientes(self, **options) -> list:
        raise NotImplementedError
    async def process_expedientes(self, raw_data: list) -> list:
        raise NotImplementedError
```

---

## 3. Checklist para Agregar un Nuevo Provider

1. [ ] Crear directorio: `api/services/providers/{provider_name}/`
2. [ ] Crear clase extending `BaseProvider`
3. [ ] Implementar metodos abstractos requeridos
4. [ ] Registrar en `ProviderFactory` (`factory.py`)
5. [ ] Agregar configuracion en base de datos (compania)
6. [ ] Crear tests en `tests/unit/providers/`
7. [ ] Actualizar documentacion

---

## 4. Providers Registrados

- `asitur/` - Asitur
- `generali/` - Generali
- `ima/` - IMA
- `multiasistencia/` - MultiAsistencia
- `mutua_madrilena/` - Mutua Madrilena
- `caser/` - Caser
- `santander/` - Santander
- `pelayo/` - Pelayo
- `lagunaro/` - Lagunaro
- `linea_directa/` - Linea Directa
- `kutxa/` - Kutxa
- `proyecta/` - Proyecta
