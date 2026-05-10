import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# ── sys.path ──────────────────────────────────────────────────────────────────
# Añade backend/ al path para que "from app.*" funcione cuando Alembic
# invoca este archivo directamente desde la CLI.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ── Alembic config object ──────────────────────────────────────────────────────
config = context.config

# ── Logging ───────────────────────────────────────────────────────────────────
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── App imports ───────────────────────────────────────────────────────────────
from app.core.config import settings  # noqa: E402
from app.db.database import Base  # noqa: E402
import app.models  # noqa: E402, F401 — must be imported to register models with Base.metadata

# ── DATABASE URL desde settings (no hardcodeada en alembic.ini) ───────────────
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# ── Target metadata para autogenerate ─────────────────────────────────────────
target_metadata = Base.metadata


# ── Offline mode ──────────────────────────────────────────────────────────────
# Genera un script SQL sin conectarse a la BD.
# Útil para revisar qué se ejecutará antes de aplicar.
# Uso: alembic upgrade head --sql > migration.sql
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online mode ───────────────────────────────────────────────────────────────
# Conecta a la BD y aplica las migraciones directamente.
# Uso: alembic upgrade head
def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # sin pool en migraciones: una conexión, una transacción
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,           # detecta cambios de tipo (VARCHAR(100) → VARCHAR(255))
            compare_server_default=False, # evita falsos positivos en MySQL con defaults
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
