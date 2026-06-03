# Referencia de la API

Base URL: `http://localhost:8000/api/v1`

::: tip Documentación interactiva
Con el proyecto corriendo, la documentación Swagger completa está disponible en **http://localhost:8000/docs** — permite probar todos los endpoints directamente desde el navegador.
:::

---

## Autenticación

La mayoría de endpoints requieren un Bearer token en el header:

```
Authorization: Bearer <access_token>
```

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| POST | `/auth/token` | Login — devuelve `access_token` y `refresh_token` | No |
| POST | `/auth/refresh` | Renovar access token con el refresh token | No |

**Ejemplo de login:**
```json
// POST /auth/token  (form-data, no JSON)
username=usuario@ejemplo.com
password=mipassword
```

---

## Usuarios

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| POST | `/users/` | Registro de nueva cuenta | No |
| GET | `/users/me` | Perfil del usuario autenticado | ✓ |
| PUT | `/users/me` | Actualizar perfil propio | ✓ |
| GET | `/users/` | Listar todos los usuarios | Admin |
| GET | `/users/{id}` | Obtener usuario por ID | Admin |
| PUT | `/users/{id}` | Actualizar usuario | Admin |
| DELETE | `/users/{id}` | Desactivar usuario (soft delete) | Admin |

---

## Alojamientos

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| GET | `/accommodations/` | Listado público con filtros | No |
| GET | `/accommodations/{id}` | Detalle de alojamiento | No |
| POST | `/accommodations/` | Crear alojamiento | Admin |
| PUT | `/accommodations/{id}` | Editar alojamiento | Admin |
| DELETE | `/accommodations/{id}` | Desactivar alojamiento | Admin |
| POST | `/accommodations/{id}/images` | Subir imagen | Admin |
| DELETE | `/accommodations/{id}/images/{img_id}` | Eliminar imagen | Admin |
| PATCH | `/accommodations/{id}/images/{img_id}/primary` | Definir imagen primaria | Admin |

**Filtros disponibles en `GET /accommodations/`:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `location` | string | Búsqueda parcial por ubicación |
| `min_price` | decimal | Precio mínimo por noche |
| `max_price` | decimal | Precio máximo por noche |
| `min_guests` | integer | Capacidad mínima requerida |
| `amenity_ids` | integer[] | IDs de amenidades requeridas |
| `limit` | integer | Máximo de resultados (default 20, max 100) |

---

## Disponibilidad y precios de temporada

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| GET | `/accommodations/{id}/availability/calendar` | Calendario de disponibilidad (máx. 365 días) | No |
| GET | `/accommodations/{id}/availability/check` | Verificar disponibilidad y precio total | No |
| POST | `/accommodations/{id}/availability/blocked-dates` | Bloquear fecha | Admin |
| DELETE | `/accommodations/{id}/availability/blocked-dates/{date}` | Desbloquear fecha | Admin |
| GET | `/accommodations/{id}/seasonal-prices` | Listar precios de temporada | No |
| POST | `/accommodations/{id}/seasonal-prices` | Crear precio de temporada | Admin |
| PUT | `/accommodations/{id}/seasonal-prices/{price_id}` | Actualizar precio | Admin |
| DELETE | `/accommodations/{id}/seasonal-prices/{price_id}` | Eliminar precio | Admin |

---

## Reservas

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| POST | `/reservations/` | Crear reserva | ✓ |
| GET | `/reservations/me` | Mis reservas | ✓ |
| GET | `/reservations/{id}` | Detalle de reserva | ✓ |
| POST | `/reservations/{id}/cancel` | Cancelar reserva | ✓ |
| GET | `/accommodations/{id}/reservations` | Reservas de un alojamiento | Admin |

**Cuerpo de `POST /reservations/`:**
```json
{
  "accommodation_id": 1,
  "check_in": "2026-07-10",
  "check_out": "2026-07-13",
  "guest_count": 2,
  "notes": "Llegamos tarde, sobre las 10pm"
}
```

**Estados de una reserva:** `confirmed` → `cancelled`

---

## Reseñas

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| GET | `/reviews/accommodations/{id}` | Reseñas de un alojamiento con promedio | No |
| POST | `/reviews/` | Crear reseña | ✓ |
| DELETE | `/reviews/{id}` | Eliminar reseña | ✓ (autor) |

**Reglas de negocio:**
- Solo se puede reseñar un alojamiento si se tuvo una reserva completada.
- Una reseña por usuario por alojamiento (constraint único en BD).
- El propietario no puede reseñar su propio alojamiento.
- Calificación de 1 a 5.

---

## Amenidades

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| GET | `/amenities/` | Listar todas las amenidades | No |
| POST | `/amenities/` | Crear amenidad | Admin |

---

## Panel administrativo

Todos los endpoints de `/admin/*` requieren rol de superusuario.

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/admin/kpis` | KPIs globales: usuarios, alojamientos, reservas, ingresos |
| GET | `/admin/stats/occupancy` | Ocupación por alojamiento en rango de fechas |
| GET | `/admin/stats/revenue/period` | Ingresos agrupados por mes |
| GET | `/admin/stats/revenue/accommodation` | Ingresos por alojamiento (top N) |
| GET | `/admin/reservations` | Todas las reservas con datos de huésped |
| GET | `/admin/accommodations` | Todos los alojamientos (incluye inactivos) |
| GET | `/admin/reports/activity` | Últimas reservas, cancelaciones y registros |

---

## Códigos de respuesta

| Código | Significado |
|---|---|
| 200 | OK |
| 201 | Recurso creado |
| 401 | Token inválido o ausente |
| 403 | Sin permisos para esta operación |
| 404 | Recurso no encontrado |
| 409 | Conflicto (email duplicado, reserva solapada, reseña duplicada) |
| 415 | Tipo de archivo no soportado (imágenes) |
| 422 | Error de validación en el cuerpo de la petición |
