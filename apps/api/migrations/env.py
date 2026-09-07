"""Alembic environment.

Reads the conn string from app settings (so it honors DATABASE_URL) and imports
the full model set for autogenerate.
"""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.db.base import Base
import app.models  # noqa: F401  (registers all models)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.database_url or "sqlite+aiosqlite:///./medfree.db")
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    _conf = config.get_section(config.config_ini_section, {})
    # Supabase's managed pooler is pgBouncer (transaction mode), which does not
    # support asyncpg's server-side prepared statements -> they collide with
    # "DuplicatePreparedStatementError". Disable those caches when asyncpg.
    _extra_kwargs = {}
    if (settings.database_url or "").startswith("postgresql+asyncpg://"):
        _extra_kwargs["connect_args"] = {
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
        }
    connectable = async_engine_from_config(
        _conf,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        **_extra_kwargs,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
