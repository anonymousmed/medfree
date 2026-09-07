"""Async SQLAlchemy engine + session factory."""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# Supabase's managed pooler is pgBouncer in transaction mode, which does NOT
# support asyncpg's server-side prepared statements (they collide across
# multiplexed sessions -> "DuplicatePreparedStatementError"). Disable the
# asyncpg statement cache AND give every prepared statement a unique name so
# SQLAlchemy's asyncpg dialect never reuses a name retained by pgBouncer.
from uuid import uuid4

_connect_args = (
    {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        # SQLAlchemy asyncpg dialect: unique prepared-statement names.
        "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4().hex}__",
    }
    if (settings.database_url or "").startswith("postgresql+asyncpg://")
    else {}
)

engine = create_async_engine(
    settings.database_url or "sqlite+aiosqlite:///./medfree.db",
    echo=settings.db_echo,
    pool_pre_ping=True,
    connect_args=_connect_args,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
