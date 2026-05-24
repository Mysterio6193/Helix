import asyncio

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool


async def main():
    pool = AsyncConnectionPool("postgresql://localhost/dummy")
    AsyncPostgresSaver(pool)

asyncio.run(main())
