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
