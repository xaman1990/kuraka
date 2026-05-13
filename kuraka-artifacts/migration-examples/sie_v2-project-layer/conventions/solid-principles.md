# Principios SOLID (OBLIGATORIOS)

Los 5 principios SOLID son **OBLIGATORIOS** en todo el codigo del proyecto. No son sugerencias, son requisitos.

---

## S - Single Responsibility (Responsabilidad Unica)

Cada clase, modulo o funcion tiene **UNA sola razon para cambiar**. Si hace dos cosas, dividela.

```python
# ❌ MAL - El service hace logica de negocio Y envia emails Y formatea datos
class TicketService:
    def create_ticket(self, data, db):
        ticket = Ticket(**data)
        db.add(ticket)
        db.commit()
        # Enviar email directamente aqui
        smtp = smtplib.SMTP('smtp.office365.com')
        smtp.send_message(msg)
        # Formatear respuesta aqui
        return {"id": ticket.id, "created": ticket.created_at.isoformat()}

# ✅ BIEN - Cada clase hace UNA sola cosa
class TicketService:
    """Solo logica de negocio de tickets."""
    def create_ticket(self, data) -> Ticket:
        ticket = ticket_repository.create(data)
        notification_service.notify_new_ticket(ticket)
        return ticket

class NotificationService:
    """Solo notificaciones."""
    def notify_new_ticket(self, ticket: Ticket):
        email_service.send(to=ticket.assignee.email, template="new_ticket", data=ticket)

class TicketRepository:
    """Solo acceso a datos de tickets."""
    def create(self, data) -> Ticket:
        ticket = Ticket(**data)
        self.db.add(ticket)
        self.db.commit()
        return ticket
```

---

## O - Open/Closed (Abierto para Extension, Cerrado para Modificacion)

Para agregar funcionalidad nueva, crea archivos nuevos. No modifiques los existentes.

```python
# ❌ MAL - Cada compania nueva obliga a modificar esta funcion
def extract(company_name, file_path):
    if company_name == "ASITUR":
        return extract_asitur(file_path)
    elif company_name == "SANTANDER":
        return extract_santander(file_path)
    elif company_name == "GENERALI":  # Hay que tocar esta funcion cada vez
        return extract_generali(file_path)

# ✅ BIEN - Registry + Factory. Agregar compania = crear 1 archivo nuevo, registrarlo
EXTRACTOR_REGISTRY = {
    "ASITUR": AsiturExtractor,
    "SANTANDER": SantanderExtractor,
    "GENERALI": GeneraliExtractor,
}

def get_extractor(company_name: str) -> BaseExtractor:
    """Factory - agregar compania = anadir 1 linea aqui + crear clase."""
    cls = EXTRACTOR_REGISTRY.get(company_name)
    if not cls:
        raise ErrNotFound(f"Extractor no encontrado: {company_name}")
    return cls()
```

---

## L - Liskov Substitution (Sustitucion de Liskov)

Cualquier clase hija DEBE poder usarse donde se usa la clase padre **sin romper nada**. Si tu subclase necesita condiciones especiales, el diseno esta mal.

```python
# ✅ BIEN - Todos los extractors cumplen el mismo contrato
class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, file_path: Path) -> pd.DataFrame: ...

    @abstractmethod
    def normalize(self, df: pd.DataFrame) -> pd.DataFrame: ...

    def run(self, file_path: Path) -> pd.DataFrame:
        """Template method - funciona igual para TODOS los extractors."""
        raw = self.extract(file_path)
        return self.normalize(raw)

class AsiturExtractor(BaseExtractor):
    def extract(self, file_path: Path) -> pd.DataFrame:
        return pd.read_excel(file_path)
    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(columns=ASITUR_COLUMN_MAP)

# El pipeline no sabe ni le importa que extractor es:
extractor = get_extractor(company_name)  # Cualquiera funciona
result = extractor.run(file_path)
```

---

## I - Interface Segregation (Segregacion de Interfaces)

No obligues a una clase a implementar metodos que no necesita. Interfaces pequenas y especificas.

```python
# ❌ MAL - Provider de email obligado a implementar metodos de API
class BaseProvider:
    def authenticate(self, username, password): ...
    def fetch_via_api(self, session_id): ...
    def fetch_via_email(self, mailbox): ...
    def sync_jira(self): ...

# ✅ BIEN - Interfaces separadas segun necesidad
class APIProvider(ABC):
    @abstractmethod
    def authenticate(self) -> str: ...
    @abstractmethod
    def fetch_data(self, session_id: str) -> list: ...

class EmailProvider(ABC):
    @abstractmethod
    def connect_mailbox(self) -> None: ...
    @abstractmethod
    def fetch_emails(self, search: str) -> list: ...
```

---

## D - Dependency Inversion (Inversion de Dependencias)

Los modulos de alto nivel NO dependen de modulos de bajo nivel. Ambos dependen de abstracciones.

```python
# ❌ MAL - Service acoplado a implementacion concreta
from repositories.ticket_repository import TicketRepository

class TicketService:
    def __init__(self):
        self.repo = TicketRepository()  # Imposible de testear con mock

# ✅ BIEN - Inyeccion de dependencias (funciona con mock en tests)
class TicketService:
    def __init__(self, repository):
        self.repo = repository  # Puede ser real o mock

# En endpoints (inyeccion con Depends de FastAPI):
def get_ticket_service(db: Session = Depends(get_db)):
    repo = TicketRepository(db)
    return TicketService(repo)

# En tests:
def test_create_ticket():
    mock_repo = MockTicketRepository()
    service = TicketService(mock_repo)
    result = service.create(data)
    assert result.id is not None
```
