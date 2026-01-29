from sqlalchemy.orm import DeclarativeBase
from config import config
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

DB_PATH = f"sqlite+aiosqlite:///{str(config.db_path)}"
dvijok = create_async_engine(DB_PATH, echo=False)

async_session = async_sessionmaker(dvijok, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

