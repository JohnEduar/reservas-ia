# Arquitectura del sistema

## Diagrama de contenedores

```
┌─────────────────────────────────────────────────────────────┐
│  docker-compose.yml                                          │
│                                                              │
│  ┌──────────┐      ┌───────────┐      ┌──────────────────┐  │
│  │  db      │      │  backend  │      │  frontend        │  │
│  │ MySQL 8  │◄─────│ FastAPI   │◄─────│ nginx (React)    │  │
│  │ :3307    │      │ :8000     │      │ :80              │  │
│  └──────────┘      └───────────┘      └──────────────────┘  │
│       │                  │                                   │
│  mysql_data         uploads_data                             │
│  (volumen)          (volumen compartido nginx↔backend)       │
└─────────────────────────────────────────────────────────────┘
```

El frontend (React compilado) es servido por **nginx**, que también proxea las rutas `/api` y `/uploads` hacia el backend. Esto elimina problemas de CORS en producción.

---

## Capas del backend

```
┌──────────────────────────────────┐
│        API Layer (Routers)       │  ← FastAPI endpoints, validación HTTP
├──────────────────────────────────┤
│      Service Layer               │  ← Lógica de negocio, reglas de dominio
├──────────────────────────────────┤
│      Repository Layer            │  ← Acceso a datos via SQLAlchemy
├──────────────────────────────────┤
│      Models / Schemas            │  ← ORM models + Pydantic schemas
└──────────────────────────────────┘
```

**Principio clave:** los endpoints nunca tocan SQLAlchemy directamente. Toda la lógica de negocio vive en los servicios; los repositorios solo acceden a datos.

---

## Decisiones arquitectónicas

### Patrón Repository + Service
Cada módulo tiene su propio repositorio (acceso a datos) y servicio (lógica de negocio). Los endpoints son delgados — validan la entrada HTTP y delegan al servicio.

### Excepciones de dominio tipadas
Cada servicio lanza sus propias excepciones (`AccommodationNotFoundError`, `DuplicateReviewError`, etc.) que un handler global en `exception_handlers.py` convierte a códigos HTTP. Los endpoints no tienen try/except.

### Soft delete universal
Usuarios y alojamientos usan `is_active = False` — nunca se eliminan filas. El listado público filtra solo activos.

### Intervalo semi-abierto `[check_in, check_out)`
El check-out es el día de salida — no se cobra esa noche. Esto permite reservas adyacentes sin conflicto.

### JWT con refresh token
El access token expira en 60 minutos. El refresh token (7 días) permite renovarlo sin reautenticar. El frontend almacena el access token en `localStorage` y lo adjunta automáticamente via interceptor de Axios.

---

## Modelo de datos

```
users
  id, email, full_name, hashed_password
  is_active, is_superuser
  created_at, updated_at

accommodations
  id, title, description, location
  price_per_night, max_guests
  owner_id → users.id
  is_active, created_at, updated_at

accommodation_images
  id, accommodation_id, url, is_primary, sort_order

amenities
  id, name, icon

accommodation_amenities  (tabla join)
  accommodation_id, amenity_id

accommodation_availability
  id, accommodation_id, date
  (solo fechas BLOQUEADAS — ausencia de fila = disponible)

seasonal_prices
  id, accommodation_id, start_date, end_date, price_per_night

reservations
  id, accommodation_id, guest_id
  check_in, check_out, guest_count
  total_price, status (confirmed | cancelled)
  notes, created_at, updated_at

reviews
  id, accommodation_id, reviewer_id
  rating (1-5), comment
  created_at
  UNIQUE(reviewer_id, accommodation_id)
```

---

## Suite de tests

El backend tiene **191 tests** con pytest, cubriendo happy path y casos de error (401, 403, 404, 409, 422) para todos los módulos.

| Módulo | Tests |
|---|---|
| Autenticación (JWT) | 16 |
| Usuarios | 23 |
| Alojamientos + imágenes | 38 |
| Disponibilidad + precios | 29 |
| Reservas | 31 |
| Reseñas | 17 |
| Admin (analíticas) | 37 |
| **Total** | **191** |

Ejecutar la suite:

```bash
cd backend
pytest
```
