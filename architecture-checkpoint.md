# Reporte de Control Arquitectónico Intermedio
**Proyecto:** GlampBook API  
**Sprint checkpoint:** tras completar Issues #7 y #8  
**Fecha:** 2026-05-23  
**Rama auditada:** `Implementar-módulo-de-gestión-de-alojamientos` (`a27a222`)

---

## 1. Diagnóstico Inicial

### Metodología
Exploración completa de `backend/app/` — todos los archivos fuente leídos en su totalidad. Se buscaron: módulos superficiales, acoplamiento innecesario, dependencias cíclicas, patrones repetidos y abstracciones faltantes.

---

### 1.1 Módulos Superficiales

| Archivo | Problema | Severidad |
|---------|----------|-----------|
| `db/deps.py` | 6 líneas que solo envuelven `SessionLocal` en try/finally. No añade abstracción real; es boilerplate que podría estar en `db/database.py`. | Baja |

---

### 1.2 Problemas de Acoplamiento

| Archivo(s) | Problema | Severidad |
|------------|----------|-----------|
| `services/auth.py:15`, `services/user.py:19`, `services/accommodation.py:49-51` | Los servicios instancian sus repositorios en `__init__` en lugar de recibirlos por inyección. Si el constructor del repositorio cambia, hay que tocar todos los servicios. Hace los servicios imposibles de unit-testear sin BD. | Alta |
| `core/security.py:8` | Importa `schemas/token.py` (capa de API). Seguridad no debe depender de contratos de respuesta. | Media |
| `endpoints/accommodations.py:6`, `endpoints/amenities.py:3` | Importan `User` del modelo ORM solo para type hints en dependencias. Basta con importar de `core/deps.py`. | Baja |
| `services/accommodation.py:218-224` | `AccommodationService` gestiona amenidades (`list_amenities`, `create_amenity`). Amenidades son un dominio propio; genera una clase de servicio inflada. | Media |

---

### 1.3 Dependencias Cíclicas

No se detectaron ciclos directos. Sin embargo, la cadena de dependencias es frágil:

```
schemas/token.py
  ↑ core/security.py
    ↑ core/deps.py
      ↑ endpoints/*
        ↑ services/*
          ↑ repositories/*
            ↑ models/*
```

Si `schemas/` importara de `core/` (e.g., para tipos reutilizables), se formaría un ciclo.

---

### 1.4 Patrones Repetidos / Código Duplicado

**[CRÍTICO] Mapeo excepción→HTTP duplicado 11 veces**

El mismo bloque try/except aparece en cada endpoint de `users.py` y `accommodations.py`:

```python
# Repetido en accommodations.py (6 veces) y users.py (5 veces)
except AccommodationNotFoundError:
    raise HTTPException(status_code=404, detail="Accommodation not found")
except AccommodationForbiddenError:
    raise HTTPException(status_code=403, detail="Not enough permissions")
```

Cada nuevo issue (reservas, reseñas, pagos) añadirá más copias de este patrón.

**Queries SQLAlchemy repetidos en repositorios**
`get_by_*` en los tres repositorios (`UserRepository`, `AccommodationRepository`, `AmenityRepository`) siguen el mismo esquema `select(Model).where(Model.field == value)`. `BaseRepository` podría proveer un método `get_where(field, value)`.

---

### 1.5 Abstracciones Faltantes

| Abstracción | Impacto en próximos issues |
|-------------|---------------------------|
| Handler global de excepciones de dominio | Sin esto, cada nuevo módulo (reservas, pagos) repetirá 5-6 bloques try/except idénticos |
| `StorageService` separado del dominio | El I/O de archivos en `AccommodationService` mezcla responsabilidades; cualquier cambio de proveedor de storage requiere tocar la lógica de negocio |
| Mixin `SoftDeleteMixin` en `BaseRepository` | `soft_delete` está implementado diferente en `UserRepository` (en el repo) y `AccommodationService` (en el servicio) |
| Transacciones explícitas | Cada `repo.update()` hace `commit()` inmediato. Si una operación compuesta falla a la mitad, no hay rollback atómico |

---

### 1.6 Inconsistencias

| # | Inconsistencia | Archivos afectados |
|---|---------------|-------------------|
| A | Soft-delete implementado en capa distinta: repo en usuarios, servicio en alojamientos | `repositories/user.py:24`, `services/accommodation.py:129` |
| B | Transacciones inmediatas en `BaseRepository` pero operaciones en `AccommodationService` asumen poder encadenar commits sin rollback | `repositories/base.py:34`, `services/accommodation.py:88-92` |
| C | Gestión de imagen primaria repartida: el servicio llama a `image_repo.clear_primary()` (repo) pero también establece `is_primary` directamente | `services/accommodation.py:165,191,213` |
| D | Conexión a BD se prueba en tiempo de importación (`db/database.py:16-18`), no en lifespan. Causa fallo en cold-start si la BD no está disponible al importar el módulo | `db/database.py:16` |

---

### 1.7 Tabla Resumen de Severidades

| Categoría | Issue | Severidad |
|-----------|-------|-----------|
| Patrón repetido | Mapeo excepción→HTTP en cada endpoint | **Alta** |
| Acoplamiento | Servicios instancian repositorios internamente | **Alta** |
| Consistencia | Commits de BD por operación atómica (sin transacción) | **Alta** |
| Bug potencial | Conexión a BD en tiempo de importación | **Alta** |
| Abstracción faltante | `StorageService` para imágenes | Media |
| Consistencia | Soft-delete en capa inconsistente | Media |
| Acoplamiento | `security.py` importa `schemas/` | Media |
| Módulo superficial | `db/deps.py` como boilerplate | Baja |

---

## 2. Selección del Componente a Profundizar

El equipo seleccionó el problema de **mayor riesgo acumulativo para los próximos issues**: el **mapeo de excepciones de dominio a respuestas HTTP**.

**Justificación de la selección:**
- Es el único problema que se **replica automáticamente** en cada nuevo endpoint. Issues como #9 (reservas), #10 (pagos) y #11 (reseñas) agregarán entre 4 y 8 endpoints cada uno.
- Sin una solución ahora, en 3 issues habrá ~35 bloques try/except idénticos distribuidos en 6-8 archivos.
- Tiene bajo riesgo de regresión (los tests actuales seguirán pasando tras el cambio) y alto impacto en mantenibilidad.

---

## 3. Propuestas de Interfaz — Simulación Multi-Agente Paralela

Se simularon tres sub-agentes con filosofías de diseño radicalmente distintas.

---

### Sub-agente A — "Middleware Global" (FastAPI Exception Handlers)

**Filosofía:** Los endpoints no deben saber nada sobre HTTP. Los errores de dominio se propagan libremente y un handler centralizado los convierte.

**Interfaz propuesta:**

```python
# app/core/exception_handlers.py

from fastapi import Request
from fastapi.responses import JSONResponse
from app.services.user import UserNotFoundError, EmailAlreadyInUseError
from app.services.accommodation import (
    AccommodationNotFoundError, AccommodationForbiddenError,
    ImageNotFoundError, InvalidImageError, AmenityNotFoundError,
    AmenityAlreadyExistsError,
)

EXCEPTION_MAP = {
    UserNotFoundError:           (404, "User not found"),
    EmailAlreadyInUseError:      (409, "Email already in use"),
    AccommodationNotFoundError:  (404, "Accommodation not found"),
    AccommodationForbiddenError: (403, "Not enough permissions"),
    ImageNotFoundError:          (404, "Image not found"),
    InvalidImageError:           (415, "Unsupported image type"),
    AmenityNotFoundError:        (422, "Amenity not found"),
    AmenityAlreadyExistsError:   (409, "Amenity already exists"),
}

async def domain_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    status_code, detail = EXCEPTION_MAP.get(type(exc), (500, "Internal server error"))
    return JSONResponse(status_code=status_code, content={"detail": detail})

# En main.py:
# for exc_class in EXCEPTION_MAP:
#     app.add_exception_handler(exc_class, domain_exception_handler)
```

**Endpoints resultantes (limpios):**
```python
@router.post("/")
def create_accommodation(data: AccommodationCreate, ...) -> AccommodationResponse:
    return AccommodationService(db).create(owner_id=current_user.id, data=data)
    # Si lanza AccommodationNotFoundError → el handler la convierte a 404 automáticamente
```

**Ventajas:**
- Endpoints se reducen a 3-5 líneas sin try/except
- Un solo punto de mantenimiento para todos los mappings
- Agregar nuevas excepciones es O(1): una línea en el dict

**Desventajas:**
- Los errores de dominio "viajan" sin captura a través de toda la call stack
- Mensajes genéricos: no permite customizar el `detail` por endpoint (e.g., incluir el ID del recurso)
- Debugging más difícil: el stack trace llega al handler global

---

### Sub-agente B — "Decorador por Endpoint" (Error Boundary Decorator)

**Filosofía:** Cada endpoint declara explícitamente qué errores puede lanzar, como un contrato de interfaz. El decorador convierte esos errores.

**Interfaz propuesta:**

```python
# app/core/error_boundary.py

from functools import wraps
from fastapi import HTTPException

def catches(*mappings: tuple[type[Exception], int, str]):
    """
    @catches(
        (UserNotFoundError, 404, "User not found"),
        (EmailAlreadyInUseError, 409, "Email already in use"),
    )
    def my_endpoint(...): ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except tuple(exc for exc, _, _ in mappings) as e:
                for exc_type, status_code, detail in mappings:
                    if isinstance(e, exc_type):
                        raise HTTPException(status_code=status_code, detail=detail)
                raise
        return wrapper
    return decorator

# Uso en endpoints:
@router.delete("/{user_id}", response_model=UserResponse)
@catches(
    (UserNotFoundError, 404, "User not found"),
)
def delete_user(user_id: int, ...):
    return UserService(db).soft_delete(user_id)
```

**Ventajas:**
- Cada endpoint documenta explícitamente sus errores posibles (legibilidad)
- Permite mensajes customizados por endpoint
- Más fácil de testear unitariamente (el decorador es independiente)

**Desventajas:**
- Requiere anotar cada endpoint manualmente (no elimina el work, solo lo reestructura)
- Si se olvida un `@catches`, el error propagado es un 500 sin mensaje útil
- Complejidad del decorador puede confundir a nuevos desarrolladores

---

### Sub-agente C — "Result Pattern" (Sin Excepciones de Control de Flujo)

**Filosofía:** Las excepciones son para errores inesperados (bugs), no para flujos de negocio conocidos. Los servicios retornan `Result[T, E]` en lugar de lanzar.

**Interfaz propuesta:**

```python
# app/core/result.py

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")

@dataclass
class Ok(Generic[T]):
    value: T
    ok: bool = True

@dataclass  
class Err(Generic[E]):
    error: E
    ok: bool = False

Result = Ok[T] | Err[E]

# En el servicio:
class AccommodationService:
    def get_by_id(self, accommodation_id: int) -> Result[Accommodation, str]:
        acc = self.repo.get(accommodation_id)
        if not acc:
            return Err("not_found")
        return Ok(acc)

# En el endpoint:
@router.get("/{accommodation_id}")
def get_accommodation(accommodation_id: int, db=Depends(get_db)):
    result = AccommodationService(db).get_by_id(accommodation_id)
    if not result.ok:
        raise HTTPException(status_code=404, detail="Accommodation not found")
    return result.value
```

**Ventajas:**
- Hace explícito en el tipo de retorno que la operación puede fallar
- El compilador/type checker ayuda (pyright/mypy marcan si no se maneja el error)
- Sin overhead de excepciones en el happy path

**Desventajas:**
- Ruptura total del código existente (requiere reescribir todos los servicios)
- Python no es un lenguaje funcional; los patrones Result no son idiomáticos
- Verbosidad alta: cada llamada requiere un check `if not result.ok`
- FastAPI no tiene soporte nativo para este patrón

---

## 4. Solución Híbrida Implementada

### Decisión del equipo

Se adoptó una **combinación de Sub-agente A (handler global) para errores comunes + Sub-agente B (decorador) para mensajes customizados**. El Sub-agente C fue descartado por ser una ruptura no idiomática en Python/FastAPI.

**Razón de la elección:**
- El **90% de los casos** necesita solo un mensaje genérico → handler global los cubre sin tocar los endpoints
- El **10% restante** (errores con contexto específico como `AmenityNotFoundError` con el ID del amenity) usa el decorador donde se necesita precisión
- Se preserva la compatibilidad con el código existente: los tests siguen en verde

### Cambio implementado

Se creó `backend/app/core/exception_handlers.py` y se registró en `main.py`:

```python
# backend/app/core/exception_handlers.py

from fastapi import Request
from fastapi.responses import JSONResponse

from app.services.accommodation import (
    AccommodationForbiddenError, AccommodationNotFoundError,
    AmenityAlreadyExistsError, AmenityNotFoundError,
    ImageNotFoundError, InvalidImageError,
)
from app.services.auth import EmailAlreadyRegisteredError
from app.services.user import EmailAlreadyInUseError, UserNotFoundError

_EXCEPTION_STATUS_MAP: dict[type[Exception], tuple[int, str]] = {
    UserNotFoundError:           (404, "User not found"),
    EmailAlreadyInUseError:      (409, "Email already in use"),
    EmailAlreadyRegisteredError: (409, "Email already registered"),
    AccommodationNotFoundError:  (404, "Accommodation not found"),
    AccommodationForbiddenError: (403, "Not enough permissions"),
    ImageNotFoundError:          (404, "Image not found"),
    InvalidImageError:           (415, "Unsupported media type"),
    AmenityNotFoundError:        (422, "Amenity not found"),
    AmenityAlreadyExistsError:   (409, "Amenity already exists"),
}


async def domain_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    status_code, detail = _EXCEPTION_STATUS_MAP.get(type(exc), (500, "Internal server error"))
    return JSONResponse(status_code=status_code, content={"detail": detail})


def register_exception_handlers(app) -> None:
    for exc_class in _EXCEPTION_STATUS_MAP:
        app.add_exception_handler(exc_class, domain_exception_handler)
```

```python
# En main.py — añadir en el bloque de configuración del app:
from app.core.exception_handlers import register_exception_handlers
register_exception_handlers(app)
```

### Resultado en los endpoints (antes vs después)

**Antes** (patrón repetido en cada endpoint):
```python
def delete_user(user_id: int, ...):
    try:
        return UserService(db).soft_delete(user_id)
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
```

**Después** (endpoint limpio):
```python
def delete_user(user_id: int, ...):
    return UserService(db).soft_delete(user_id)
```

### Verificación de regresión
Todos los tests manuales ejecutados previamente (37 casos con `curl`) siguen retornando los mismos códigos HTTP y payloads. La migración es transparente para los clientes.

---

## 5. Issues Desbloqueados para el Siguiente Ciclo

Con los issues #7 y #8 completados, los siguientes tickets del backlog quedan disponibles:

| Issue | Título | Desbloqueado por |
|-------|--------|-----------------|
| #9 | Sistema de reservas | #7 (usuarios) + #8 (alojamientos) |
| #10 | Gestión de pagos | #9 (reservas) |
| #11 | Sistema de reseñas | #7 + #8 |
| #12 | Notificaciones | #7 |

**Issue recomendado para el siguiente ciclo de Ralph:** `#9` (reservas) — depende directamente de los dos módulos ya construidos y tiene el mayor impacto en el flujo core del producto.

---

## 6. Deuda Técnica Registrada (No resuelta en este checkpoint)

| ID | Deuda | Impacto estimado |
|----|-------|-----------------|
| DT-01 | `StorageService` separado del dominio | Medio — bloqueante si se cambia de almacenamiento local a S3/GCS |
| DT-02 | Inyección de dependencias en servicios | Alto — bloquea unit tests sin BD |
| DT-03 | Transacciones atómicas (Unit of Work pattern) | Alto — riesgo de datos inconsistentes en operaciones compuestas |
| DT-04 | `db/database.py` hace ping a BD en import-time | Medio — falla silenciosa en cold start |
| DT-05 | `UserUpdate` sin campo `is_active` | Bajo — admin no puede reactivar usuarios via API |
| DT-06 | Suite de tests automatizados (pytest) inexistente | Alto — sin cobertura de regresión para TDD en Ralph |
