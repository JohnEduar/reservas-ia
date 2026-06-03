# GlampBook

> Plataforma web profesional de reservas para resorts de glamping — desarrollada con React, FastAPI y MySQL.

---

## Descripción

GlampBook es una aplicación web full-stack diseñada para gestionar de forma integral las reservas de un resort de glamping. Ofrece una experiencia de usuario moderna y fluida para los huéspedes, junto con un panel administrativo completo que permite gestionar alojamientos, disponibilidad, reservas y analíticas del negocio en tiempo real.

El proyecto es desarrollado como actividad académica oficial de la asignatura **Ingeniería de Software** (Semestre 6), aplicando principios de arquitectura limpia, buenas prácticas de desarrollo y herramientas de IA como soporte técnico durante el ciclo de vida del software.

---

## Objetivo General

Construir una plataforma de reservas escalable, segura y mantenible que permita a los usuarios explorar alojamientos de glamping, realizar y gestionar reservas por fechas, y que ofrezca a los administradores del resort un panel centralizado con estadísticas, gestión de disponibilidad e historial de operaciones.

---

## Stack Tecnológico

| Capa | Tecnología | Versión |
|---|---|---|
| Frontend | React + Vite | React 18 / Vite 5 |
| Estilos | TailwindCSS | 3.x |
| Backend | FastAPI | 0.110+ |
| ORM | SQLAlchemy | 2.x |
| Base de datos | MySQL | 8.x |
| Autenticación | JWT (PyJWT + bcrypt) | — |
| Migraciones | Alembic | — |
| Validación | Pydantic v2 | — |
| HTTP Client | Axios | — |
| Contenedores | Docker + Docker Compose | — |

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────┐
│                     CLIENTE (Browser)                   │
│              React + Vite + TailwindCSS                 │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTP/REST (JSON)
                          │ JWT en Authorization Header
┌─────────────────────────▼───────────────────────────────┐
│                   BACKEND (FastAPI)                     │
│                                                         │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ API Layer  │→ │Service Layer │→ │ Repository     │  │
│  │ (Routers)  │  │(Business     │  │ Layer          │  │
│  │            │  │ Logic)       │  │ (Data Access)  │  │
│  └────────────┘  └──────────────┘  └───────┬────────┘  │
└──────────────────────────────────────────── │ ──────────┘
                                              │ SQLAlchemy ORM
┌─────────────────────────────────────────────▼───────────┐
│                    MySQL Database                       │
└─────────────────────────────────────────────────────────┘
```

**Patrón arquitectónico**: Layered Architecture + Repository Pattern

- El frontend consume exclusivamente la API REST versionada (`/api/v1/`)
- La capa de servicios encapsula toda la lógica de negocio
- El repositorio abstrae las operaciones de base de datos via SQLAlchemy
- JWT manejado en cada request mediante interceptores de Axios

---

## Estructura de Carpetas

```
glampbook/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── auth.py
│   │   │   │   │   ├── users.py
│   │   │   │   │   ├── accommodations.py
│   │   │   │   │   ├── reservations.py
│   │   │   │   │   ├── availability.py
│   │   │   │   │   └── admin.py
│   │   │   │   └── router.py
│   │   │   └── deps.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── database.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── accommodation.py
│   │   │   ├── reservation.py
│   │   │   ├── availability.py
│   │   │   └── review.py
│   │   ├── schemas/
│   │   │   ├── user.py
│   │   │   ├── accommodation.py
│   │   │   ├── reservation.py
│   │   │   └── auth.py
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── user_service.py
│   │   │   ├── accommodation_service.py
│   │   │   ├── reservation_service.py
│   │   │   └── availability_service.py
│   │   ├── repositories/
│   │   │   ├── base_repo.py
│   │   │   ├── user_repo.py
│   │   │   ├── accommodation_repo.py
│   │   │   └── reservation_repo.py
│   │   └── main.py
│   ├── migrations/
│   │   └── versions/
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   ├── .env.example
│   ├── requirements.txt
│   ├── Dockerfile
│   └── alembic.ini
│
├── frontend/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   ├── layout/
│   │   │   └── shared/
│   │   ├── pages/
│   │   │   ├── auth/
│   │   │   ├── public/
│   │   │   ├── user/
│   │   │   └── admin/
│   │   ├── features/
│   │   │   ├── auth/
│   │   │   ├── accommodations/
│   │   │   ├── reservations/
│   │   │   └── admin/
│   │   ├── hooks/
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── store/
│   │   ├── utils/
│   │   ├── router/
│   │   │   ├── index.jsx
│   │   │   ├── ProtectedRoute.jsx
│   │   │   └── AdminRoute.jsx
│   │   └── App.jsx
│   ├── public/
│   ├── index.html
│   ├── tailwind.config.js
│   ├── vite.config.js
│   └── package.json
│
├── docker-compose.yml
└── README.md
```

---

## Funcionalidades Principales

### Para huéspedes
- Registro e inicio de sesión con JWT
- Exploración de alojamientos con filtros (tipo, capacidad, precio)
- Vista detallada de cada alojamiento (galería, amenidades, descripción)
- Selección de fechas con calendario de disponibilidad en tiempo real
- Flujo de reserva: selección → resumen → confirmación
- Dashboard personal con reservas activas e historial
- Cancelación de reservas dentro del plazo permitido
- Sistema de reseñas y calificaciones

### Para administradores
- Dashboard con KPIs: ocupación, ingresos, reservas del período
- Gestión completa de alojamientos (CRUD + imágenes + amenidades)
- Gestión y seguimiento de reservas (confirmar, cancelar, completar)
- Calendario de disponibilidad: bloquear y desbloquear fechas
- Gestión de usuarios registrados
- Reportes de actividad

---

## Entidades de Base de Datos

```
users              → datos de cuenta, rol (guest / admin)
accommodations     → alojamientos disponibles en el resort
reservations       → reservas realizadas con estado y fechas
availability       → disponibilidad por fecha por alojamiento
reviews            → calificaciones y comentarios por reserva
```

**Estados de una reserva**: `pending` → `confirmed` → `completed` | `cancelled`

---

## Roadmap de Desarrollo

### Fase 1 — Fundación `[Completada]`
- [x] Diseño de arquitectura del sistema
- [x] Definición de entidades y módulos
- [x] Setup inicial del backend con FastAPI
- [x] Setup del frontend con React + Vite
- [x] Configuración de Docker y MySQL
- [x] Migraciones iniciales con Alembic
- [x] Sistema de autenticación con JWT

### Fase 2 — Core de Reservas `[Completada]`
- [x] CRUD de alojamientos
- [x] Motor de disponibilidad por fechas
- [x] Flujo completo de reserva
- [x] Listado con filtros

### Fase 3 — Panel de Usuario `[Completada]`
- [x] Dashboard personal con reservas
- [x] Historial y detalle de reserva
- [x] Gestión de perfil
- [x] Cancelación de reservas

### Fase 4 — Panel Administrativo `[Completada]`
- [x] Dashboard con KPIs y estadísticas
- [x] CRUD de alojamientos
- [x] Gestión de reservas
- [x] Listado de usuarios

### Fase 5 — Calidad y Producción `[Completada]`
- [x] Sistema de reseñas (backend)
- [x] Tests unitarios e integración (191 tests)
- [x] Deploy con Docker Compose
- [ ] Notificaciones por email
- [ ] Optimización y paginación

---

## Instalación

### Requisitos previos

- Python 3.11+
- Node.js 20+
- Docker Desktop
- MySQL 8 (o usar el contenedor incluido)

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/glampbook.git
cd glampbook
```

### 2. Configurar el backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Editar .env con tus credenciales de MySQL
```

### 3. Configurar el frontend

```bash
cd frontend
npm install
cp .env.example .env.local
# Editar .env.local con la URL del backend
```

### 4. Levantar la base de datos con Docker

```bash
docker-compose up -d db
```

### 5. Ejecutar migraciones

```bash
cd backend
alembic upgrade head
```

---

## Ejecución Local

### Backend (FastAPI)

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API disponible en: `http://localhost:8000`
Documentación interactiva: `http://localhost:8000/docs`

### Frontend (React + Vite)

```bash
cd frontend
npm run dev
```

App disponible en: `http://localhost:5173`

### Con Docker Compose (entorno completo)

```bash
docker-compose up --build
```

| Servicio | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| MySQL | localhost:3306 |

---

## Variables de Entorno

### Backend `.env`

```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/glampbook
SECRET_KEY=tu_clave_secreta_muy_larga
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
ALLOWED_ORIGINS=http://localhost:5173
```

### Frontend `.env.local`

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

---

## Convenciones de Código

### Python
- Estilo: PEP 8
- Type hints obligatorios en servicios y endpoints
- Schemas separados por propósito: `Create`, `Update`, `Response`

### JavaScript / React
- Componentes funcionales con hooks, sin clases
- Estilos exclusivamente con TailwindCSS
- Imports absolutos con alias `@` configurado en Vite

### Git — Conventional Commits

```
feat:   nueva funcionalidad
fix:    corrección de bug
chore:  tareas de mantenimiento
docs:   cambios en documentación
test:   adición o modificación de tests
refactor: refactorización sin cambio de funcionalidad
```

### Estrategia de ramas

```
main        → código estable de producción
develop     → rama de integración
feature/*   → nuevas funcionalidades
fix/*       → correcciones puntuales
```

---

## Metodología de Trabajo

El proyecto sigue un enfoque de desarrollo iterativo por fases, con entregas incrementales de valor. Cada fase produce funcionalidad completa y funcional (frontend + backend + DB), siguiendo principios de:

- **Separación de responsabilidades**: cada capa tiene un rol claro y único
- **API-first**: el contrato de la API se define antes de implementar el frontend
- **Validación temprana**: Pydantic valida toda entrada antes de procesarla
- **Código sin sorpresas**: nombres descriptivos, sin comentarios redundantes, sin abstracciones prematuras
- **Seguridad por defecto**: contraseñas hasheadas, JWT con expiración, CORS configurado, sin secretos en el código

---

## Uso de Claude Code en el Desarrollo

Este proyecto integra **Claude Code** como herramienta de asistencia técnica a lo largo de todo el ciclo de desarrollo, bajo la supervisión del desarrollador.

### Rol de Claude Code en el proyecto

| Área | Uso |
|---|---|
| **Arquitectura** | Diseño del sistema, definición de capas y patrones |
| **Planificación** | Definición de entidades, módulos y roadmap de fases |
| **Generación de código** | Scaffolding de modelos, schemas, servicios y endpoints |
| **Revisión de código** | Identificación de errores, vulnerabilidades y mejoras |
| **Documentación** | README, docstrings, especificaciones técnicas |
| **Debugging** | Análisis de errores y propuesta de soluciones |
| **Buenas prácticas** | Convenciones, seguridad, escalabilidad |

### Principio de uso

Claude Code actúa como **par de programación sénior**, no como reemplazo del desarrollador. Cada sugerencia es evaluada, adaptada y validada por el desarrollador antes de integrarse al proyecto. El control de versiones (git) mantiene trazabilidad total de cada decisión tomada.

---

## Autores

**Samuel Zapata**
[lazarosamuelza45@gmail.com](mailto:lazarosamuelza45@gmail.com)

**John Eduar Pérez**
[johneduar777@gmail.com](mailto:johneduar777@gmail.com)

**Juan Esteban Osorno**

**Juan Camilo Patiño**


---

*Proyecto académico — Actividad Oficial · 2026*
