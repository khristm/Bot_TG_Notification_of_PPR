from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event
from config import config
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

DB_PATH = f"sqlite+aiosqlite:///{str(config.db_path)}"
dvijok = create_async_engine(DB_PATH, echo=False)

async_session = async_sessionmaker(dvijok, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

#Настройка SQLite при каждом подключении
@event.listens_for(dvijok.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    # Включаем режим Write-Ahead Logging
    cursor.execute("PRAGMA journal_mode=WAL")
    # Оптимизируем синхронизацию (безопасно для WAL)
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()