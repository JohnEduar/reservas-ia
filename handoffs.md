# Bitácora de Transferencia de Contexto (Handoffs)

> Archivo generado según la técnica de **Context Handoff** para mitigar el desgaste de tokens en sesiones largas de desarrollo asistido por IA.  
> Cada entrada representa una transferencia limpia de contexto entre sesiones o bloques de issues.

---

## Handoff #1 — Issues #7 y #8
**Fecha:** 2026-05-16  
**Rama:** `Implementar-módulo-de-gestión-de-alojamientos`  
**Commit:** `a27a222`  
**Autor:** Samuel Zapata

### Componentes construidos

#### Issue #7 — Módulo de usuarios
| Archivo | Tipo | Descripción |
|---------|------|-------------|
| `backend/app/schemas/user.py` | Modificado | Añadido `UserUpdate` (campos opcionales) y timestamps en `UserResponse` |
| `backend/app/repositories/user.py` | Modificado | Añadidos `soft_delete()` y `email_exists_for_other()` |
| `backend/app/services/user.py` | Nuevo | `UserService`: `get_by_id`, `get_all`, `update`, `soft_delete` |
| `backend/app/api/v1/endpoints/users.py` | Modificado | Endpoints CRUD completos: `GET /`, `PUT /me`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}` |

#### Issue #8 — Módulo de alojamientos
| Archivo | Tipo | Descripción |
|---------|------|-------------|
| `backend/app/models/accommodation.py` | Nuevo | Modelos `Accommodation`, `AccommodationImage`, `Amenity`, tabla join `accommodation_amenities` |
| `backend/app/schemas/accommodation.py` | Nuevo | Schemas: `AccommodationCreate/Update/Response`, `AmenityCreate/Response`, `AccommodationImageResponse` |
| `backend/app/repositories/accommodation.py` | Nuevo | Tres repositorios con filtros dinámicos (location, price, guests, amenities) |
| `backend/app/services/accommodation.py` | Nuevo | `AccommodationService`: CRUD, gestión de imágenes, validación de ownership |
| `backend/app/api/v1/endpoints/accommodations.py` | Nuevo | 8 endpoints: CRUD + imágenes + set-primary |
| `backend/app/api/v1/endpoints/amenities.py` | Nuevo | 2 endpoints: listar y crear amenidades |
| `backend/migrations/versions/20260516_b5c6d7e8f9a0_accommodations.py` | Nuevo | Migración Alembic: 4 tablas nuevas |
| `backend/app/main.py` | Modificado | Mount de `StaticFiles` en `/uploads` y creación automática del directorio |

### Decisiones arquitectónicas consolidadas

1. **Patrón Repository + Service**: toda la lógica de negocio vive en `services/`, los repositorios solo acceden a datos. Los endpoints nunca tocan SQLAlchemy directamente.
2. **Soft delete universal**: tanto usuarios como alojamientos usan `is_active=False` — nunca se borran filas. El listado público filtra solo activos.
3. **Control de ownership en el Service**: `_check_ownership()` centraliza la validación de permisos por recurso. Si el requester no es owner ni superusuario → `AccommodationForbiddenError`.
4. **Imágenes en disco local**: archivos guardados en `uploads/accommodations/` con UUID como nombre. La URL relativa se almacena en BD. La primera imagen sube como primaria; al eliminar la primaria, la siguiente se auto-promueve.
5. **Filtros dinámicos en repositorio**: `get_public()` construye el query WHERE de forma incremental según los parámetros recibidos — sin ORM N+1.
6. **Errores como excepciones de dominio**: cada servicio lanza excepciones propias (`UserNotFoundError`, `AccommodationForbiddenError`, etc.) que los endpoints capturan y mapean a HTTP codes.

### Estado de los endpoints al cierre del handoff

```
GET  /api/v1/users/              → lista activos (superuser)
POST /api/v1/users/              → registro público
GET  /api/v1/users/me            → perfil propio
PUT  /api/v1/users/me            → actualizar perfil propio
GET  /api/v1/users/{id}          → obtener por ID (superuser)
PUT  /api/v1/users/{id}          → actualizar (superuser)
DELETE /api/v1/users/{id}        → soft delete (superuser)

GET  /api/v1/accommodations/     → listado público + filtros
POST /api/v1/accommodations/     → crear (autenticado)
GET  /api/v1/accommodations/{id} → detalle público
PUT  /api/v1/accommodations/{id} → actualizar (owner/superuser)
DELETE /api/v1/accommodations/{id} → soft delete (owner/superuser)
POST /api/v1/accommodations/{id}/images          → subir imagen
DELETE /api/v1/accommodations/{id}/images/{img}  → eliminar imagen
PATCH /api/v1/accommodations/{id}/images/{img}/primary → set primaria

GET  /api/v1/amenities/          → listar (público)
POST /api/v1/amenities/          → crear (superuser)
```

### Elementos pendientes al inicio del próximo contexto

- [ ] **Issue #9+**: identificar qué issues del backlog quedaron desbloqueados por #7 y #8
- [ ] **Tests automatizados (pytest)**: los issues #7 y #8 carecen de suite de pruebas en código — solo se verificaron con `curl` manual
- [ ] **Reactivación de usuarios**: `UserUpdate` no expone `is_active`; un admin no puede reactivar un usuario eliminado lógicamente via API
- [ ] **Validación de tamaño de imagen**: el endpoint de upload no restringe el tamaño del archivo (pendiente añadir límite de 5 MB)
- [ ] **Paginación en respuesta**: los endpoints de lista no retornan metadatos de paginación (`total`, `page`, `pages`)
- [ ] **ralph/once.sh**: el script de ejecución autónoma no existe en el repositorio — bloqueante para el flujo automatizado

---

## Handoff #2 — Issue #13
**Fecha:** 2026-05-28  
**Rama:** `HEAD`  
**Autor:** Samuel Zapata

### Componentes construidos

#### Issue #13 — Sistema de reseñas y calificaciones
| Archivo | Tipo | Descripción |
|---------|------|-------------|
| `backend/app/models/review.py` | Nuevo | Modelo `Review` con `UniqueConstraint(reviewer_id, accommodation_id)` para prevenir duplicados |
| `backend/app/models/__init__.py` | Modificado | `Review` exportada en el registro central |
| `backend/app/schemas/review.py` | Nuevo | `ReviewCreate` (rating 1-5, comment opcional), `ReviewUpdate`, `ReviewResponse`, `ReviewSummary` |
| `backend/app/repositories/review.py` | Nuevo | `ReviewRepository`: `get_by_accommodation`, `get_user_review`, `get_average_rating`, `count_by_accommodation` |
| `backend/app/services/review.py` | Nuevo | `ReviewService`: `create`, `list_by_accommodation`, `get_summary`, `delete` + excepciones tipadas |
| `backend/app/api/v1/endpoints/reviews.py` | Nuevo | 3 endpoints: `GET /reviews/accommodations/{id}`, `POST /reviews/`, `DELETE /reviews/{id}` |
| `backend/app/api/v1/router.py` | Modificado | Router de reseñas registrado en `/reviews` |
| `backend/app/core/exception_handlers.py` | Modificado | Mapeadas 4 nuevas excepciones: `ReviewNotFoundError`, `ReviewForbiddenError`, `DuplicateReviewError`, `SelfReviewError` |
| `backend/migrations/versions/20260528_c9d1e2f3a4b5_reviews.py` | Nuevo | Migración Alembic: tabla `reviews` con 3 índices y constraint único |
| `backend/tests/test_reviews.py` | Nuevo | 16 tests: happy path, 401, 403, 404, 409, 422 |

### Reglas de negocio implementadas

1. **Sin auto-reseñas**: el propietario de un alojamiento no puede reseñarse a sí mismo → `SelfReviewError` (422).
2. **Sin duplicados**: un usuario solo puede tener una reseña por alojamiento → `DuplicateReviewError` (409). Garantizado por UniqueConstraint en BD y validación en servicio.
3. **Calificación 1-5**: validada por Pydantic (`ge=1, le=5`); fuera de rango → 422.
4. **Borrado solo por autor o superusuario**: `ReviewForbiddenError` (403) si otro usuario intenta eliminar.
5. **Cascade delete**: al eliminar un alojamiento, sus reseñas se eliminan (`ondelete="CASCADE"`).
6. **Reviewer se pone a NULL** si el usuario se elimina (`ondelete="SET NULL"`).
7. **Promedio calculado en BD**: `func.avg()` en SQLAlchemy, no en Python.

### Endpoints al cierre del handoff

```
GET  /api/v1/reviews/accommodations/{id}  → listado con average_rating y total_reviews (público)
POST /api/v1/reviews/                     → crear reseña (autenticado)
DELETE /api/v1/reviews/{review_id}        → eliminar reseña (autor o superusuario)
```

### Elementos pendientes al inicio del próximo contexto

- [ ] **Validar reserva completada**: el issue requería verificar que el reviewer haya tenido una reserva completada en el alojamiento. Bloqueado hasta que exista el módulo de reservas (booking). La lógica debe agregarse en `ReviewService.create()`.
- [ ] **Paginación en `get_summary`**: actualmente `get_summary` carga hasta 1000 reseñas en memoria para calcular el total; separar en consultas dedicadas `count_by_accommodation` ya existe en repo.
- [ ] **Edición de reseña**: `ReviewUpdate` schema existe pero no hay endpoint `PATCH /reviews/{id}` — puede añadirse si se requiere.

---

*Próxima sesión: iniciar con este documento como contexto base, ignorar el historial de chat anterior.*

---

## Handoff #2 — Issue #9: Motor de disponibilidad de alojamientos
**Fecha:** 2026-05-25  
**Rama:** `main`  
**Commit:** pendiente  
**Autor:** Claude Sonnet 4.6

### Componentes construidos

| Archivo | Tipo | Descripción |
|---------|------|-------------|
| `backend/app/models/accommodation.py` | Modificado | Añadidos `AccommodationAvailability` y `SeasonalPrice`; relaciones `blocked_dates` y `seasonal_prices` en `Accommodation` |
| `backend/app/schemas/availability.py` | Nuevo | `AvailabilityBlockCreate/Response`, `AvailabilityCalendarDayResponse`, `AvailabilityCheckResponse`, `SeasonalPriceCreate/Update/Response` |
| `backend/app/repositories/availability.py` | Nuevo | `AvailabilityRepository` (queries por rango, inclusive/exclusivo), `SeasonalPriceRepository` (solapamiento, precio por fecha) |
| `backend/app/services/availability.py` | Nuevo | `AvailabilityService`: calendario, check, block/unblock, CRUD precios de temporada; `assert_available()` para uso futuro por Reservas |
| `backend/app/api/v1/endpoints/availability.py` | Nuevo | 8 endpoints montados bajo `/accommodations` |
| `backend/app/core/exception_handlers.py` | Modificado | 6 nuevas excepciones de dominio registradas |
| `backend/app/api/v1/router.py` | Modificado | Router `availability` incluido con prefix `/accommodations` |
| `backend/migrations/versions/20260525_d7e8f9a0b1c2_availability.py` | Nuevo | Migración Alembic: tablas `accommodation_availability` y `seasonal_prices` |
| `backend/tests/test_availability.py` | Nuevo | 29 tests: happy path, 401, 403, 404, 409, 422 |

### Decisiones arquitectónicas

1. **Solo se almacenan fechas bloqueadas**: `accommodation_availability` solo guarda registros para días NO disponibles. Ausencia de fila = disponible. Más eficiente que almacenar todos los días.
2. **Unicidad por (accommodation_id, date)**: constraint `uq_availability_acc_date` previene duplicados a nivel DB.
3. **Rangos de temporada sin solapamiento**: `SeasonalPriceRepository.get_overlapping()` valida que no existan rangos conflictivos para el mismo alojamiento.
4. **`check_availability` devuelve bool, no lanza excepción**: la comprobación es informativa. `assert_available()` sí lanza `AccommodationNotAvailableError` para uso interno por el futuro módulo de Reservas.
5. **Precio por día en calendario y check**: cada día se evalúa individualmente contra `SeasonalPrice`; si hay tarifa de temporada activa ese día, se usa en lugar del base.
6. **Límite de 365 días en calendario**: evita respuestas masivas en calendarios muy amplios.

### Estado de los endpoints al cierre del handoff

```
GET  /api/v1/accommodations/{id}/availability/calendar        → calendario (público)
GET  /api/v1/accommodations/{id}/availability/check           → verificar disponibilidad (público)
POST /api/v1/accommodations/{id}/availability/blocked-dates   → bloquear fechas (owner/superuser)
DELETE /api/v1/accommodations/{id}/availability/blocked-dates/{date} → desbloquear (owner/superuser)
GET  /api/v1/accommodations/{id}/seasonal-prices              → listar precios (público)
POST /api/v1/accommodations/{id}/seasonal-prices              → crear precio (owner/superuser)
PUT  /api/v1/accommodations/{id}/seasonal-prices/{price_id}   → actualizar precio (owner/superuser)
DELETE /api/v1/accommodations/{id}/seasonal-prices/{price_id} → eliminar precio (owner/superuser)
```

### Elementos pendientes al inicio del próximo contexto

- [ ] **Issue #10+**: módulo de Reservas desbloqueado — `AvailabilityService.assert_available()` ya está listo para ser consumido
- [ ] **Reservas solapadas**: la validación de solapamiento de reservas reales (vs bloqueadas) se completará en el módulo de Reservas
- [ ] **Límite de calendario configurable**: actualmente hardcodeado en 365 días en `availability.py:_MAX_CALENDAR_DAYS`
- [ ] **Paginación en lista de precios de temporada**: el endpoint devuelve todos los registros sin paginación

---

*Próxima sesión: iniciar con este documento como contexto base, ignorar el historial de chat anterior.*

---

## Handoff #3 — Issue #10: Flujo de reservas
**Fecha:** 2026-05-25
**Rama:** `10-implementar-flujo-de-reservas`
**Commit:** pendiente
**Autor:** Claude Sonnet 4.6

### Componentes construidos

| Archivo | Tipo | Descripción |
|---------|------|-------------|
| `backend/app/models/reservation.py` | Nuevo | `Reservation` ORM model con `ReservationStatus` enum (`confirmed`/`cancelled`) |
| `backend/app/models/__init__.py` | Modificado | Exporta `Reservation` para que SQLAlchemy incluya la tabla en `Base.metadata` |
| `backend/app/schemas/reservation.py` | Nuevo | `ReservationCreate`, `ReservationResponse` |
| `backend/app/repositories/reservation.py` | Nuevo | `ReservationRepository`: `get_by_guest`, `get_by_accommodation`, `get_overlapping` |
| `backend/app/services/reservation.py` | Nuevo | `ReservationService` con 6 excepciones de dominio; lógica de negocio completa |
| `backend/app/api/v1/endpoints/reservations.py` | Nuevo | Router `/reservations`: crear, historial propio, detalle, cancelar |
| `backend/app/api/v1/endpoints/accommodation_reservations.py` | Nuevo | Router `/accommodations`: listar reservas por alojamiento (host view) |
| `backend/app/core/exception_handlers.py` | Modificado | 6 nuevas excepciones de dominio registradas |
| `backend/app/api/v1/router.py` | Modificado | Routers `reservations` y `accommodation_reservations` incluidos |
| `backend/migrations/versions/20260525_f0a1b2c3d4e5_reservations.py` | Nuevo | Migración Alembic: tabla `reservations` |
| `backend/tests/test_reservations.py` | Nuevo | 31 tests: happy path, 401, 403, 404, 409, 422 |

### Decisiones arquitectónicas

1. **Estado `confirmed` por defecto**: la reserva se crea directamente como confirmada. No existe estado `pending` — la validación de disponibilidad es síncrona y atómica.
2. **Cancelación como transición de estado, no soft delete**: `status = "cancelled"` en lugar de `is_active = False`. El campo `status` es el dominio correcto para reservas.
3. **Doble verificación de conflicto**: el servicio verifica tanto fechas bloqueadas manualmente (`accommodation_availability`) como reservas activas solapadas (`reservations`). La query de solapamiento excluye reservas canceladas.
4. **Semántica de intervalo semi-abierto [check_in, check_out)**: check_out es el día de salida — no se paga esa noche. Permite reservas adyacentes sin conflicto.
5. **Host view separado en router propio**: `accommodation_reservations.py` montado en `/accommodations` sigue el mismo patrón que `availability.py`.
6. **Precio calculado al momento de reserva**: `total_price` se persiste para preservar el precio histórico aunque los precios de temporada cambien posteriormente.

### Estado de los endpoints al cierre del handoff

```
POST /api/v1/reservations/                          → crear reserva (autenticado)
GET  /api/v1/reservations/me                        → historial propio (autenticado)
GET  /api/v1/reservations/{id}                      → detalle (guest / owner / superuser)
POST /api/v1/reservations/{id}/cancel               → cancelar (guest / superuser)
GET  /api/v1/accommodations/{id}/reservations       → vista del host (owner / superuser)
```

### Elementos pendientes al inicio del próximo contexto

- [ ] **Issue #11+**: revisar backlog para identificar próximo issue desbloqueado
- [ ] **Notificaciones**: no se envían emails/webhooks al crear o cancelar una reserva
- [ ] **Paginación con metadatos**: los listados devuelven arrays planos sin `total`/`page`/`pages`
- [ ] **Validación de fecha mínima**: no se impide reservar fechas pasadas (podría requerirse según regla de negocio)

---

*Próxima sesión: iniciar con este documento como contexto base, ignorar el historial de chat anterior.*

---

## Handoff #4 — Issue #11: Dashboard de huéspedes (frontend)
**Fecha:** 2026-05-25
**Rama:** `10-implementar-flujo-de-reservas`
**Commit:** pendiente
**Autor:** Claude Sonnet 4.6

### Componentes construidos

| Archivo | Tipo | Descripción |
|---------|------|-------------|
| `frontend/package.json` | Nuevo | Dependencias: React 18, React Router 6, TanStack Query 5, Axios, Tailwind CSS 3, Vite 5 |
| `frontend/vite.config.js` | Nuevo | Proxy `/api` → `http://localhost:8000` para desarrollo local |
| `frontend/tailwind.config.js` | Nuevo | Paleta `primary` verde, content paths configurados |
| `frontend/index.html` | Nuevo | Entry point HTML |
| `frontend/src/main.jsx` | Nuevo | Root render con `QueryClientProvider` (staleTime 5 min) |
| `frontend/src/App.jsx` | Nuevo | Router raíz con rutas protegidas y `AuthProvider` |
| `frontend/src/lib/axios.js` | Nuevo | Instancia Axios con interceptor Bearer y redirección automática en 401 |
| `frontend/src/api/auth.js` | Nuevo | `login()` con form-urlencoded (OAuth2PasswordRequestForm) |
| `frontend/src/api/reservations.js` | Nuevo | CRUD wrapper para `/reservations/me`, `/{id}`, `/{id}/cancel` |
| `frontend/src/api/users.js` | Nuevo | `me()` y `update()` para `/users/me` |
| `frontend/src/context/AuthContext.jsx` | Nuevo | Estado global de sesión; `login`, `logout`, `refreshUser` |
| `frontend/src/components/ProtectedRoute.jsx` | Nuevo | Guard de rutas; spinner durante carga inicial |
| `frontend/src/components/Layout.jsx` | Nuevo | Navbar responsiva con NavLink activos y botón de salir |
| `frontend/src/components/Spinner.jsx` | Nuevo | Spinner animado en 3 tamaños (sm/md/lg) |
| `frontend/src/components/StatusBadge.jsx` | Nuevo | Badge `confirmed`/`cancelled` con colores semánticos |
| `frontend/src/components/ReservationCard.jsx` | Nuevo | Tarjeta de reserva con fechas, noches, total y enlace al detalle |
| `frontend/src/pages/LoginPage.jsx` | Nuevo | Formulario de login con manejo de errores y redirect tras autenticación |
| `frontend/src/pages/DashboardPage.jsx` | Nuevo | Inicio: stats (activas/próximas/en curso/total) + listado de reservas activas |
| `frontend/src/pages/ReservationsPage.jsx` | Nuevo | Historial con filtros Todas / Activas / Canceladas |
| `frontend/src/pages/ReservationDetailPage.jsx` | Nuevo | Detalle completo + flujo de cancelación con confirmación en dos pasos |
| `frontend/src/pages/ProfilePage.jsx` | Nuevo | Edición de nombre, email y contraseña; info de cuenta (id, estado, fecha de alta) |
| `.gitignore` | Modificado | Añadidos `frontend/node_modules/`, `frontend/dist/`, `frontend/.env.local` |

### Decisiones arquitectónicas

1. **Sin backend nuevo**: todos los endpoints necesarios ya existían (Issue #10). El frontend consume `/reservations/me`, `/reservations/{id}`, `/reservations/{id}/cancel`, `/users/me`, `PUT /users/me`.
2. **Proxy Vite**: el servidor de desarrollo redirige `/api` al backend en `localhost:8000`, eliminando la necesidad de configurar CORS extra en desarrollo.
3. **TanStack Query como cache**: `queryKey: ['reservations', 'me']` se comparte entre Dashboard y Reservations; una cancelación invalida ambas vistas automáticamente via `invalidateQueries`.
4. **Token en localStorage**: el interceptor de Axios adjunta el Bearer token en cada petición y redirige a `/login` en respuestas 401.
5. **Cancelación con confirmación en dos pasos**: el botón "Cancelar reserva" primero muestra un panel de confirmación antes de ejecutar la mutación.
6. **Solo reservas futuras cancelables**: el botón solo aparece si `status === 'confirmed'` AND `check_in > hoy`.

### Rutas de la SPA

```
/login                    → LoginPage (pública)
/dashboard                → DashboardPage (autenticado)
/reservations             → ReservationsPage (autenticado)
/reservations/:id         → ReservationDetailPage (autenticado)
/profile                  → ProfilePage (autenticado)
/                         → redirect a /dashboard
```

### Cómo iniciar el frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

### Elementos pendientes al inicio del próximo contexto

- [ ] **Nombre del alojamiento en tarjetas**: actualmente se muestra `Alojamiento #ID`; requeriría enriquecer `ReservationResponse` con datos del alojamiento o un endpoint adicional
- [ ] **Registro desde el frontend**: no hay página de registro — solo login
- [ ] **Refresh token**: el interceptor no renueva tokens expirados automáticamente
- [ ] **Tests de frontend**: no hay tests automatizados (Vitest/Testing Library)
- [ ] **Producción**: URL del backend hardcodeada vía proxy Vite; en producción se necesitará `VITE_API_URL`

---

*Próxima sesión: iniciar con este documento como contexto base, ignorar el historial de chat anterior.*

---

## Handoff #5 — Issue #admin: Dashboard administrativo y analíticas
**Fecha:** 2026-05-26
**Rama:** `main`
**Commit:** pendiente
**Autor:** Claude Sonnet 4.6

### Componentes construidos

| Archivo | Tipo | Descripción |
|---------|------|-------------|
| `backend/app/schemas/admin.py` | Nuevo | Schemas: `KPISummary`, `OccupancyStats`, `RevenueByPeriod`, `AccommodationRevenue`, `AdminReservationResponse`, `AdminAccommodationResponse`, `ActivityReport` |
| `backend/app/repositories/admin.py` | Nuevo | `AdminRepository`: conteos, sumas de ingresos, agrupaciones por mes/alojamiento, estadísticas de ocupación, listados con JOIN de usuario y alojamiento |
| `backend/app/services/admin.py` | Nuevo | `AdminService`: orquesta el repositorio, construye los schemas de respuesta |
| `backend/app/api/v1/endpoints/admin.py` | Nuevo | 7 endpoints GET todos protegidos con `get_current_superuser` |
| `backend/app/api/v1/router.py` | Modificado | Registra `admin.router` en `/admin` |
| `backend/migrations/versions/20260526_a1b2c3d4e5f6_admin_analytics.py` | Nuevo | Migración marcador (sin cambios de esquema); `down_revision = f0a1b2c3d4e5` |
| `backend/tests/test_admin.py` | Nuevo | 37 tests: happy path, 401, 403, 422 por endpoint |

### Endpoints implementados

```
GET /api/v1/admin/kpis                          → KPI global (usuarios, alojamientos, reservas, ingresos)
GET /api/v1/admin/stats/occupancy               → Ocupación por alojamiento en rango de fechas
GET /api/v1/admin/stats/revenue/period          → Ingresos agrupados por mes (filtro opcional por año)
GET /api/v1/admin/stats/revenue/accommodation   → Ingresos y reservas por alojamiento (top N)
GET /api/v1/admin/reservations                  → Todas las reservas con datos de huésped y alojamiento
GET /api/v1/admin/accommodations                → Todos los alojamientos (incluye inactivos por defecto)
GET /api/v1/admin/reports/activity              → Últimas reservas, cancelaciones y registros de usuario
```

### Decisiones arquitectónicas

1. **Sin nuevas tablas**: toda la analítica se computa con consultas de agregación sobre los modelos existentes. La migración `a1b2c3d4e5f6` es un marcador sin DDL.
2. **`AdminRepository` independiente**: no extiende `BaseRepository` porque sus consultas son analíticas (agregados, JOINs multi-tabla), no CRUD sobre una sola entidad.
3. **Occupancy calculado en Python**: la superposición de noches con el rango dado usa `max(check_in, start)` / `min(check_out, end)`, más legible en Python que en SQL dialectal.
4. **Ingresos basados en `created_at`**: `revenue_this_month` y `revenue_by_month` agrupan por fecha de creación de la reserva, no por `check_in`.
5. **`AdminReservationResponse` desde dict**: los datos vienen de `execute()` con JOIN multi-tabla; el schema se construye desde el dict ensamblado en el repositorio.
6. **`status` validado con `pattern` en Query**: acepta solo `confirmed` o `cancelled`; FastAPI devuelve 422 automáticamente para valores inválidos.
7. **Protección uniforme**: todos los endpoints usan `get_current_superuser` → 401 sin token, 403 con token de usuario normal.

### Elementos pendientes al inicio del próximo contexto

- [ ] **Dashboard frontend**: no hay UI para el panel de administración; los endpoints existen pero falta la SPA
- [ ] **Paginación con metadatos**: los listados devuelven arrays planos sin `total`/`page`/`pages`
- [ ] **Filtros adicionales en `/admin/reservations`**: no hay filtro por rango de fechas ni por alojamiento
- [ ] **Export de reportes**: no se puede exportar a CSV/Excel desde los endpoints de analítica
- [ ] **Gestión de usuarios desde admin**: `PUT /users/{id}` y `DELETE /users/{id}` ya existen (superuser); no se duplicaron en `/admin`

---

*Próxima sesión: iniciar con este documento como contexto base, ignorar el historial de chat anterior.*

---

## Handoff #6 — Issue #admin: Dashboard administrativo frontend
**Fecha:** 2026-05-26
**Rama:** `main`
**Autor:** Claude Sonnet 4.6

### Componentes construidos

| Archivo | Tipo | Descripción |
|---------|------|-------------|
| `frontend/src/api/admin.js` | Nuevo | Servicio API para todos los endpoints `/admin/*` y `GET /users/` |
| `frontend/src/components/AdminRoute.jsx` | Nuevo | Guard de ruta: redirige a `/dashboard` si `user.is_superuser !== true` |
| `frontend/src/components/AdminLayout.jsx` | Nuevo | Layout con navbar índigo separado del layout de huéspedes; links a Métricas, Usuarios, Reservas y vuelta al panel huéspedes |
| `frontend/src/pages/admin/AdminDashboardPage.jsx` | Nuevo | KPI cards (6), tabla de ingresos por mes (año actual), actividad reciente (últimas reservas + nuevos usuarios) |
| `frontend/src/pages/admin/AdminUsersPage.jsx` | Nuevo | Tabla de todos los usuarios: ID, nombre, email, estado, rol (Admin/Huésped), fecha de registro |
| `frontend/src/pages/admin/AdminReservationsPage.jsx` | Nuevo | Tabla de todas las reservas con filtro por pestañas (Todas / Confirmadas / Canceladas) |
| `frontend/src/App.jsx` | Modificado | Añadidas rutas `/admin`, `/admin/users`, `/admin/reservations` bajo `ProtectedRoute → AdminRoute → AdminLayout` |
| `frontend/src/pages/LoginPage.jsx` | Modificado | Redirección automática: superusuarios van a `/admin`, el resto a `/dashboard` |

### Rutas de la SPA (actualizadas)

```
/login                    → LoginPage (pública)
/admin                    → AdminDashboardPage (superuser)
/admin/users              → AdminUsersPage (superuser)
/admin/reservations       → AdminReservationsPage (superuser)
/dashboard                → DashboardPage (autenticado)
/reservations             → ReservationsPage (autenticado)
/reservations/:id         → ReservationDetailPage (autenticado)
/profile                  → ProfilePage (autenticado)
/                         → redirect a /dashboard
```

### Decisiones arquitectónicas

1. **`AdminRoute` liviano**: no duplica la lógica de loading/auth de `ProtectedRoute`; solo verifica `user.is_superuser`. Por estar siempre anidado bajo `ProtectedRoute`, `user` está garantizado como no-nulo cuando `AdminRoute` se ejecuta.
2. **Layout separado**: `AdminLayout` usa navbar índigo (`bg-indigo-900`) para diferenciarse visualmente del layout de huéspedes. Incluye enlace "Panel huéspedes →" para volver sin logout.
3. **Usuarios via `GET /users/`**: la lista de usuarios usa el endpoint existente (no se duplicó en `/admin`). Solo superusuarios pueden acceder a ese endpoint.
4. **Filtro de reservas con React Query**: el `queryKey` incluye el `statusFilter`; cambiar de pestaña invalida y recarga automáticamente sin estado local adicional.
5. **Redirección post-login**: `login()` ya devuelve los datos del usuario; se usa `userData.is_superuser` para decidir la ruta sin una segunda petición.

### Elementos pendientes al inicio del próximo contexto

- [ ] **Registro desde el frontend**: no hay página de registro — solo login
- [ ] **Refresh token**: el interceptor no renueva tokens expirados automáticamente
- [ ] **Paginación con metadatos**: los listados devuelven arrays planos sin `total`/`page`/`pages`
- [ ] **Filtros adicionales en reservas admin**: no hay filtro por rango de fechas ni por alojamiento
- [ ] **Export de reportes**: no se puede exportar a CSV/Excel
- [ ] **Tests de frontend**: no hay tests automatizados (Vitest/Testing Library)

---

*Próxima sesión: iniciar con este documento como contexto base, ignorar el historial de chat anterior.*
