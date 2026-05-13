# Frontend Standards - Vue 3 + TypeScript

---

## 1. Stack del Frontend

- **Framework**: Vue 3 (Composition API)
- **Lenguaje**: TypeScript estricto (**TODO tipado, NO any, NO untyped**)
- **Build**: Vite
- **Estado**: Pinia
- **Estilos**: Tailwind CSS
- **Routing**: Vue Router 4
- **Comunicacion en vivo**: WebSocket (datos de BD en tiempo real)
- **Contenedor**: Docker + nginx

---

## 2. TypeScript Tipado Obligatorio

Este proyecto usa **TypeScript, NO JavaScript vanilla**. La diferencia fundamental es que TODO debe estar tipado. Si no hay tipos, es JS vanilla disfrazado de TS y **NO SE ACEPTA**.

Reglas de tipado:
- **TODAS** las funciones deben tener tipos en parametros Y retorno
- **TODAS** las variables reactivas (`ref`, `computed`) deben tener tipo generico explicito
- **TODOS** los props y emits deben usar genericos tipados
- **TODOS** los datos de API deben tener interfaces definidas en `types/`
- **NUNCA** usar `any`, `unknown` (excepto en catch de errores), ni casteos sin justificar
- **NUNCA** dejar que TypeScript infiera `any` implicitamente

```typescript
// ❌ PROHIBIDO - Esto es JS vanilla con extension .ts
const data = ref([])
const user = ref(null)
function fetchData() { ... }
const props = defineProps(['title', 'count'])

// ❌ PROHIBIDO - any explicito o implicito
const response: any = await api.get('/tickets')
function process(item: any): any { return item }
const data = ref<any[]>([])

// ✅ OBLIGATORIO - TypeScript real, todo tipado
const tickets = ref<Ticket[]>([])
const currentUser = ref<User | null>(null)
const isLoading = ref<boolean>(false)
const error = ref<string | null>(null)

async function fetchTickets(): Promise<void> {
  const response = await apiClient.get<PaginatedResponse<Ticket>>('/tickets')
  tickets.value = response.data.items
}

const props = defineProps<{
  title: string
  count: number
  status?: TicketStatus
}>()

const emit = defineEmits<{
  (e: 'update', ticket: Ticket): void
  (e: 'delete', id: number): void
}>()

// ✅ Computed tipado
const activeTickets = computed<Ticket[]>(() =>
  tickets.value.filter(t => t.status === TicketStatus.IN_PROGRESS)
)

// ✅ Composables con tipos de retorno explicitos
interface UseTicketsReturn {
  tickets: Ref<Ticket[]>
  isLoading: Ref<boolean>
  error: Ref<string | null>
  fetchTickets: () => Promise<void>
  createTicket: (data: TicketCreate) => Promise<Ticket>
}

export function useTickets(): UseTicketsReturn { ... }
```

---

## 3. WebSocket Obligatorio para Datos en Vivo

Los datos que vienen de la base de datos deben mostrarse **en tiempo real** via WebSocket. El frontend NO debe depender solo de polling HTTP para refrescar datos.

**Patron**: El backend emite eventos via WebSocket cuando hay cambios en BD. El frontend escucha esos eventos y actualiza el estado automaticamente.

```
Backend (FastAPI)                    Frontend (Vue 3)
┌─────────────────┐                 ┌──────────────────┐
│ Service modifica│                 │ useWebSocket()   │
│ datos en BD     │──── WS ────>    │ recibe evento    │
│                 │                 │ actualiza store  │
└─────────────────┘                 └──────────────────┘
```

**Eventos WebSocket tipados**:
```typescript
// types/websocket.ts
type WSEventType =
  | 'expediente:created'
  | 'expediente:updated'
  | 'expediente:synced'
  | 'ticket:created'
  | 'ticket:updated'
  | 'ticket:assigned'
  | 'ticket:resolved'
  | 'task:started'
  | 'task:completed'
  | 'task:failed'
  | 'notification:new'

interface WSMessage<T = unknown> {
  event: WSEventType
  data: T
  timestamp: string
}

interface WSExpedienteEvent {
  id: number
  status: string
  compania: string
}

interface WSTicketEvent {
  id: number
  title: string
  status: TicketStatus
  assignee_id: number | null
}
```

**Uso en stores** (ejemplo Pinia):
```typescript
// stores/expedienteStore.ts
export const useExpedienteStore = defineStore('expediente', () => {
  const expedientes = ref<Expediente[]>([])
  const { data: wsData, connect } = useWebSocket({
    url: import.meta.env.VITE_WS_URL
  })

  // Escuchar cambios en vivo desde BD
  watch(wsData, (raw: string | null) => {
    if (!raw) return
    const msg: WSMessage = JSON.parse(raw)

    switch (msg.event) {
      case 'expediente:created':
        expedientes.value.unshift(msg.data as Expediente)
        break
      case 'expediente:updated':
      case 'expediente:synced':
        const idx = expedientes.value.findIndex(e => e.id === (msg.data as WSExpedienteEvent).id)
        if (idx !== -1) Object.assign(expedientes.value[idx], msg.data)
        break
    }
  })

  return { expedientes, connect }
})
```

---

## 4. Branding Guai Insurtech

```
Primary:    #CCFF00 (neon lime)
Background: #0A0A0A (near-black)
Text:       #E0E0E0 (light gray)
Accent:     #B7FF1E (bright lime)
Secondary:  #2E2E2E (dark gray)
Glow:       box-shadow 0px 10px 20px -3px #CCFF00
```

---

## 5. Convenciones Frontend

### Nombres
- **Componentes**: `PascalCase.vue` (`TicketList.vue`, `LoginPage.vue`)
- **Composables**: `useCamelCase.ts` (`useAuth.ts`, `useTickets.ts`, `usePermissions.ts`)
- **Stores (Pinia)**: `useCamelCaseStore.ts` (`useAuthStore.ts`, `useTicketStore.ts`)
- **Services/API**: `camelCase.ts` (`ticketService.ts`, `apiClient.ts`)
- **Types/Interfaces**: `PascalCase` (`Ticket`, `User`, `ApiResponse`)
- **Funciones/variables**: `camelCase` (`fetchTickets`, `isLoading`)
- **Constantes**: `UPPER_SNAKE_CASE` (`API_BASE_URL`, `MAX_FILE_SIZE`)

### TypeScript Estricto
```typescript
// ❌ PROHIBIDO
const data: any = response.data
function process(item: any): any { ... }

// ✅ OBLIGATORIO
interface Ticket {
  id: number
  title: string
  status: TicketStatus
  assignee: User | null
}

const data: Ticket[] = response.data
function process(item: Ticket): ProcessedTicket { ... }
```

### Estructura de Componente Vue 3
```vue
<script setup lang="ts">
// 1. Imports
import { ref, computed, onMounted } from 'vue'
import { useTicketStore } from '@/stores/ticketStore'
import type { Ticket } from '@/types'

// 2. Props y emits
const props = defineProps<{ ticketId: number }>()
const emit = defineEmits<{ (e: 'updated', ticket: Ticket): void }>()

// 3. Stores y composables
const ticketStore = useTicketStore()

// 4. Estado reactivo
const isLoading = ref(false)
const error = ref<string | null>(null)

// 5. Computed
const filteredTickets = computed(() => ticketStore.tickets.filter(...))

// 6. Funciones
async function fetchData() { ... }

// 7. Lifecycle
onMounted(() => { fetchData() })
</script>

<template>
  <!-- Template -->
</template>

<style scoped>
/* Estilos con scoped */
</style>
```

### Composables para Logica Reutilizable

```typescript
// composables/usePermissions.ts
export function usePermissions() {
  const authStore = useAuthStore()

  const canAccessModule = (module: string): boolean => {
    return authStore.user?.modules.includes(module) ?? false
  }

  const hasRole = (role: string): boolean => {
    return authStore.user?.role === role
  }

  return { canAccessModule, hasRole }
}
```

### Stores Pinia para Estado Global

```typescript
// stores/authStore.ts
export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))

  const isAuthenticated = computed(() => !!token.value)

  async function login(credentials: LoginRequest): Promise<void> {
    const response = await authService.login(credentials)
    token.value = response.token
    user.value = response.user
    localStorage.setItem('token', response.token)
  }

  function logout(): void {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  return { user, token, isAuthenticated, login, logout }
})
```

---

## 6. Modulos del Frontend

El frontend tiene 4 modulos principales, accesibles segun el rol del usuario:

| Modulo | Descripcion | Roles |
|--------|-------------|-------|
| **SIE** | Dashboard expedientes, companias, tareas | admin, responsable |
| **Ticketera** | CRUD tickets, admin categorias/urgencias | admin, soporte, usuario |
| **Tools** | Baremos, duplicidad, proyecta | admin, responsable |
| **Admin** | Gestion usuarios, roles, config global | admin |

### Roles del sistema:
`admin`, `responsable`, `product_owner`, `soporte`, `usuario`, `ia`
