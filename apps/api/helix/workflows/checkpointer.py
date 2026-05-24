"""Postgres-backed LangGraph Checkpointer."""

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

from helix.core.config import get_settings
from helix.core.logging import get_logger

log = get_logger(__name__)

# Global checkpointer instances
pool: AsyncConnectionPool | None = None
checkpointer: AsyncPostgresSaver | None = None

async def setup_checkpointer() -> AsyncPostgresSaver:
    global pool, checkpointer
    if checkpointer is not None:
        return checkpointer

    settings = get_settings()
    conn_str = settings.db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    pool = AsyncConnectionPool(
        conninfo=conn_str,
        max_size=settings.db_pool_size,
        kwargs={"autocommit": True}
    )
    # open pool
    await pool.open()
    
    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()
    log.info("checkpointer.setup_complete")
    return checkpointer

async def close_checkpointer():
    global pool, checkpointer
    if pool is not None:
        await pool.close()
        pool = None
        checkpointer = None

