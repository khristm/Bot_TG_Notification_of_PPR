from database.database import Base, dvijok
from database.models import User, Task
from sqlalchemy import text

async def migration(conn):
    result = await conn.execute(text(f"PRAGMA table_info(tasks);"))
    columns = [row[1] for row in result.fetchall()]
    if columns and "adress" in columns and "address" not in columns:
        await conn.execute(text("ALTER TABLE tasks RENAME COLUMN adress TO address;"))

async def init_db():
    async with dvijok.begin() as conn:
        await migration(conn)
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("PRAGMA wal_checkpoint(TRUNCATE);"))