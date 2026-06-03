# Inicio rápido

## Requisitos previos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y corriendo
- Git

## Levantar el entorno completo

### 1. Clonar el repositorio

```bash
git clone https://github.com/JohnEduar/reservas-ia.git
cd reservas-ia
```

### 2. Configurar variables de entorno

```bash
# Variables del entorno raíz (MySQL)
cp .env.example .env
# Editar .env y completar DB_PASSWORD

# Variables del backend (JWT, base de datos)
cp backend/.env.example backend/.env
# Editar backend/.env y completar DB_PASSWORD y JWT_SECRET_KEY
```

Campos obligatorios en `backend/.env`:

```env
DB_HOST=db
DB_PORT=3306
DB_NAME=glampbook
DB_USER=glampbook_user
DB_PASSWORD=tu_password_segura

JWT_SECRET_KEY=una_clave_secreta_larga_y_aleatoria
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 3. Levantar con Docker Compose

```bash
docker compose up --build -d
```

El primer arranque tarda ~1-2 minutos mientras se descargan las imágenes y se ejecutan las migraciones de base de datos automáticamente.

### 4. Verificar que todo corre

| Servicio | URL |
|---|---|
| **Frontend** | http://localhost |
| **Backend API** | http://localhost:8000 |
| **Swagger (docs interactivos)** | http://localhost:8000/docs |

### 5. Ver logs

```bash
# Todos los servicios
docker compose logs -f

# Solo el backend
docker compose logs -f backend
```

---

## Desarrollo local (sin Docker)

Para desarrollar con hot-reload es más conveniente correr los servicios por separado.

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # completar credenciales

# Ejecutar migraciones (requiere MySQL corriendo)
alembic upgrade head

# Iniciar servidor
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

::: tip Proxy de desarrollo
El servidor de Vite proxea automáticamente `/api` hacia `localhost:8000`, por lo que no se necesita configurar CORS adicional en desarrollo.
:::

---

## Crear el primer usuario administrador

La API no expone un endpoint público para crear superusuarios. Para el primer admin, conectarse directamente a la base de datos:

```sql
UPDATE users SET is_superuser = 1 WHERE email = 'admin@ejemplo.com';
```

O usando el contenedor de MySQL:

```bash
docker compose exec db mysql -u glampbook_user -p glampbook
```
