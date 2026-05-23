import asyncio
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

async def main():
    pool = AsyncConnectionPool("postgresql://localhost/dummy")
    saver = AsyncPostgresSaver(pool)
    print("Success")

asyncio.run(main())
