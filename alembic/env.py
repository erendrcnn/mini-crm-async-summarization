from __future__ import with_statement
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from sqlalchemy import create_engine
from alembic import context
import os

# this is the Alembic Config object, which provides access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
from app.core.database import Base  # type: ignore
from app.core.config import settings  # type: ignore
from app.models.user import User  # noqa
from app.models.note import Note  # noqa

target_metadata = Base.metadata


def get_url():
    # Reuse application's normalized URL, but force sync driver for Alembic
    db_url = settings.db_url or os.getenv("DATABASE_URL", "sqlite:///./app.db")
    # Alembic runs in sync mode; swap async driver to sync equivalent
    if db_url.startswith("postgresql+asyncpg"):
        db_url = db_url.replace("postgresql+asyncpg", "postgresql+psycopg", 1)
    if db_url.startswith("sqlite+aiosqlite"):
        db_url = db_url.replace("sqlite+aiosqlite", "sqlite", 1)
    return db_url


def run_migrations_offline():
    url = get_url()
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    configuration = config.get_section(config.config_ini_section)
    if configuration is None:
        configuration = {}
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
