# Frontend

## Stack

| Tecnología | Uso |
|---|---|
| React 18 | UI con hooks y componentes funcionales |
| Vite 5 | Build tool y servidor de desarrollo |
| TailwindCSS 3 | Estilos utilitarios |
| React Router 6 | Enrutamiento SPA |
| TanStack Query 5 | Caché y sincronización de estado servidor |
| Axios | HTTP client con interceptores JWT |

---

## Rutas de la aplicación

### Área pública
| Ruta | Página | Descripción |
|---|---|---|
| `/login` | LoginPage | Formulario de login y registro en tabs |

### Área de huésped (requiere autenticación)
| Ruta | Página | Descripción |
|---|---|---|
| `/dashboard` | DashboardPage | Resumen de reservas activas y estadísticas |
| `/accommodations` | AccommodationsPage | Catálogo con filtros de búsqueda |
| `/accommodations/:id` | AccommodationDetailPage | Detalle, galería y botón de reserva |
| `/reservations` | ReservationsPage | Historial completo con filtros por estado |
| `/reservations/:id` | ReservationDetailPage | Detalle y opción de cancelación |
| `/profile` | ProfilePage | Edición de nombre, email y contraseña |

### Panel administrativo (requiere `is_superuser`)
| Ruta | Página | Descripción |
|---|---|---|
| `/admin` | AdminDashboardPage | KPIs, ingresos por mes y actividad reciente |
| `/admin/accommodations` | AdminAccommodationsPage | CRUD de alojamientos con modal de edición |
| `/admin/users` | AdminUsersPage | Listado de usuarios registrados |
| `/admin/reservations` | AdminReservationsPage | Todas las reservas filtradas por estado |

---

## Flujos principales

### Flujo de reserva
```
/accommodations
  → click en tarjeta de alojamiento
  → /accommodations/:id  (detalle + galería)
  → click "Reservar ahora"
  → modal de reserva (accommodation pre-cargado)
  → confirmación → redirige a /reservations
```

### Flujo de autenticación
```
/login  →  LoginPage
  Iniciar sesión: POST /auth/token → guarda access_token en localStorage
  Registrarse:   POST /users/      → auto-login tras registro exitoso

Al entrar con is_superuser=true → redirige a /admin
Al entrar con usuario normal    → redirige a /dashboard

Interceptor Axios: adjunta Bearer token en cada request
Al recibir 401: borra token y redirige a /login
```

---

## Componentes compartidos

| Componente | Descripción |
|---|---|
| `Layout` | Navbar verde con links de navegación para huéspedes |
| `AdminLayout` | Navbar índigo para el panel administrativo |
| `ProtectedRoute` | Redirige a `/login` si no hay sesión activa |
| `AdminRoute` | Redirige a `/dashboard` si no es superusuario |
| `CreateReservationModal` | Modal de reserva — acepta `accommodation` pre-cargado o ID manual |
| `ReservationCard` | Tarjeta de reserva con fechas, noches y estado |
| `StatusBadge` | Badge de estado `confirmed` / `cancelled` con color semántico |
| `Spinner` | Indicador de carga en tres tamaños (sm / md / lg) |

---

## Gestión del estado

TanStack Query gestiona todo el estado del servidor. Las claves de cache más importantes:

| Query Key | Datos |
|---|---|
| `['reservations', 'me']` | Reservas del usuario autenticado |
| `['accommodations', params]` | Listado de alojamientos (staleTime: 0) |
| `['accommodation', id]` | Detalle de un alojamiento |
| `['admin', 'accommodations']` | Listado admin de alojamientos |
| `['admin', 'reservations', status]` | Reservas admin filtradas por estado |

Al crear o cancelar una reserva, `invalidateQueries` refresca automáticamente el Dashboard y la página de reservas sin recarga manual.
