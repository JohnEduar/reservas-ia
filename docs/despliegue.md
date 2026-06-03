# Despliegue con Docker Compose

## Arquitectura de contenedores

El `docker-compose.yml` define tres servicios que arrancan en orden:

```
db (MySQL 8)
  ↓ healthcheck: mysqladmin ping
backend (FastAPI + Uvicorn)
  ↓ depends_on: db (healthy)
frontend (nginx sirviendo React)
  ↓ depends_on: backend
```

### Puertos expuestos

| Servicio | Puerto externo | Puerto interno |
|---|---|---|
| Frontend (nginx) | 80 | 80 |
| Backend (Uvicorn) | 8000 | 8000 |
| MySQL | 3307 | 3306 |

::: warning
El puerto externo de MySQL es **3307** (no 3306) para evitar conflictos con instalaciones locales de MySQL.
:::

---

## Variables de entorno

### `.env` (raíz del proyecto)
```env
DB_PASSWORD=password_segura_aqui
DB_NAME=glampbook
```

### `backend/.env`
```env
DB_HOST=db
DB_PORT=3306
DB_NAME=glampbook
DB_USER=glampbook_user
DB_PASSWORD=password_segura_aqui

JWT_SECRET_KEY=clave_secreta_minimo_32_caracteres
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

ALLOWED_ORIGINS=http://localhost
```

---

## Flujo de arranque

El `entrypoint.sh` del backend ejecuta en orden:

```bash
alembic upgrade head   # Aplica todas las migraciones pendientes
uvicorn app.main:app   # Inicia la API
```

Las migraciones son idempotentes — si ya están aplicadas, Alembic no hace nada.

---

## Comandos útiles

```bash
# Levantar todo en background
docker compose up --build -d

# Ver estado de los contenedores
docker compose ps

# Ver logs en tiempo real
docker compose logs -f

# Detener todo
docker compose down

# Detener y eliminar volúmenes (borra la BD)
docker compose down -v

# Rebuild de un servicio específico
docker compose up --build backend -d
```

---

## Volúmenes persistentes

| Volumen | Contenido |
|---|---|
| `mysql_data` | Datos de MySQL — persiste entre reinicios |
| `uploads_data` | Imágenes de alojamientos — compartido entre `backend` y `frontend` |

---

## Notas de producción

::: warning Pendiente para producción real
- **HTTPS/TLS**: nginx no tiene certificado configurado. Se recomienda añadir Certbot o un reverse proxy externo (Traefik, Caddy).
- **Múltiples workers**: el entrypoint usa un solo worker de Uvicorn. Para carga real se recomienda `--workers 4` o Gunicorn como process manager.
- **Variables de entorno en frontend**: las variables `VITE_*` se hornean en build time. Si la URL del backend cambia en producción, hay que reconstruir la imagen del frontend.
:::
