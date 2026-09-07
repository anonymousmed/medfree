"""Async SQLAlchemy engine + session factory."""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# Supabase's managed pooler is pgBouncer in transaction mode, which does NOT
# support asyncpg's server-side prepared statements (they collide across
# multiplexed sessions -> "DuplicatePreparedStatementError"). Disable the
# asyncpg statement/prepared-statement caches for pooled/transaction pooling.
_connect_args = (
    {"statement_cache_size": 0, "prepared_statement_cache_size": 0}
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
