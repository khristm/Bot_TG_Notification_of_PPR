from sqlalchemy.orm import DeclarativeBase
from config import config
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

DB_PATH = f"sqlite+aiosqlite:///{str(config.db_path)}"
dvijok = create_async_engine(DB_PATH, echo=True)

async_session = async_sessionmaker(dvijok, expire_on_commit=False)

# async def get_db():
#     """Генератор сессий, дает при вызове один экзампляр сессии, перехватываем исключения
#     выполняем автоматический откат всех транзакций в сессии, в конце автоматическое закрытие сессии"""
#     async with async_session() as session:
#         try:
#             print("Получаем сессию")
#             yield session
#         except Exception as e:
#             print(e)
#             await session.rollback()
#         finally:
#             await session.close()
#             print("Закрыли сессию")

class Base(DeclarativeBase):
    pass

