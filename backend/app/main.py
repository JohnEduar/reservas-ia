from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.db.database import engine
from app.schemas.health import HealthResponse

# Ensure upload directory exists before StaticFiles mount
Path("uploads/accommodations").mkdir(parents=True, exist_ok=True)

_OPENAPI_TAGS = [
    {
        "name": "Health",
        "description": "Endpoints de estado del servicio para monitoreo e infraestructura.",
    },
    {
        "name": "Root",
        "description": "Información general de la API.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    openapi_tags=_OPENAPI_TAGS,
    contact={
        "name": "GlampBook Team",
        "email": "dev@glampbook.com",
    },
    license_info={
        "name": "MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
    expose_headers=["X-Request-ID"],
    max_age=600,
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
register_exception_handlers(app)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Infrastructure health check",
    description=(
        "Lightweight health check for load balancers and container orchestrators. "
        "Does not check database connectivity."
    ),
)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc),
    )


@app.get("/", tags=["Root"], include_in_schema=False)
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
        "api": settings.API_V1_PREFIX,
    }
