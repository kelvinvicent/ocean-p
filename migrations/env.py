"""
Alembic env.py — usa los modelos de SQLModel y el DATABASE_URL de la app.

Permite:
- Desarrollo local: `alembic upgrade head` con `DATABASE_URL=sqlite:///./ocean_p.db`
- Producción:        `alembic upgrade head` con `DATABASE_URL=postgresql://...` (Neon)
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from alembic import context

# Importar modelos para que SQLModel.metadata los registre antes del autogenerate
from app.config import settings
from app.models import (  # noqa: F401
    User,
    TestSession,
    ItemResponse,
    Score,
    Report,
    EmailDelivery,
    NormTable,
)


config = context.config
# Sobrescribir la URL del .ini con la del entorno (más seguro que hardcodear en alembic.ini)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url") or ""
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=url.startswith("sqlite"),
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        is_sqlite = connection.dialect.name == "sqlite"
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=is_sqlite,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
