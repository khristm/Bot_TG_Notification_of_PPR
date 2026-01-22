from database.database import Base, dvijok
from database.models import User, Task

async def init_db():
    async with dvijok.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)