---
layout: home

hero:
  name: "GlampBook"
  text: "Plataforma de reservas para glamping"
  tagline: Gestión integral de alojamientos, disponibilidad y reservas — construida con React, FastAPI y MySQL.
  image:
    src: https://em-content.zobj.net/source/twitter/376/tent_26fa.png
    alt: GlampBook
  actions:
    - theme: brand
      text: Inicio rápido
      link: /guia-inicio
    - theme: alt
      text: Ver en GitHub
      link: https://github.com/JohnEduar/reservas-ia

features:
  - icon: 🏕️
    title: Catálogo de alojamientos
    details: Los administradores gestionan el catálogo completo con imágenes, amenidades, precios por temporada y bloqueo de fechas.

  - icon: 📅
    title: Motor de disponibilidad
    details: Calendario de disponibilidad en tiempo real con precios de temporada. Las reservas se validan de forma síncrona y atómica.

  - icon: 🔐
    title: Autenticación JWT
    details: Login seguro con tokens de acceso y refresh. Roles diferenciados entre huésped y administrador.

  - icon: 📊
    title: Dashboard administrativo
    details: KPIs de ingresos, ocupación por alojamiento, actividad reciente y gestión completa de usuarios y reservas.

  - icon: ⭐
    title: Sistema de reseñas
    details: Los huéspedes pueden calificar alojamientos tras completar su estancia. Una reseña por usuario por alojamiento.

  - icon: 🐳
    title: Despliegue con Docker
    details: Entorno completo con Docker Compose — base de datos, backend y frontend listos con un solo comando.
---

## Sobre el proyecto

GlampBook es una aplicación web full-stack desarrollada como actividad académica de la asignatura **Ingeniería de Software** (Semestre 6). Aplica principios de arquitectura limpia, patrón Repository + Service, y está completamente contenerizada con Docker Compose.

| Capa | Tecnología |
|---|---|
| Frontend | React 18 + Vite 5 + TailwindCSS |
| Backend | FastAPI + SQLAlchemy 2 + Pydantic v2 |
| Base de datos | MySQL 8 |
| Autenticación | JWT (PyJWT + bcrypt) |
| Migraciones | Alembic |
| Contenedores | Docker + Docker Compose |

**Autores:** Samuel Zapata · John Eduar Pérez — 2026
