from database.database import dvijok, Base, async_session
from database.models import User, Task
from database.crud import (create_user, update_chat_id, create_schedule, create_schedule_from_list,
                           delete_tasks, get_tasks_today)
import asyncio
from schemas import UserSchema, TaskSchema


async def init_db():
    async with dvijok.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def test(data_user_list, tg_id):
    async with async_session() as ses:
        await create_schedule_from_list(ses, data_user_list, tg_id)
    await dvijok.dispose()

async def test2(token,month):
    async with async_session() as s:
        await delete_tasks(s,token,month)
    await dvijok.dispose()

async def test3(token):
    async with async_session() as s:
        res = await get_tasks_today(s,token)
    await dvijok.dispose()
    if res:
        (print(res[0].adress,res[0].date_time))
    else: print(res)

if __name__ == '__main__':
    tg = "someid"
    # data=[TaskSchema(month='2026-01',date_time='2026-01-22',adress="Комсомольская 26",number=7222636,
    #                 workers="Ледышев, Плаксенко",type="ППР А2"),
    #       TaskSchema(month='2026-01',date_time='2026-01-28',adress="Финский 22",number=7222736,
    #                 workers="Пьянов, Федоровский",type="ППР А2")
    #       ]
    #asyncio.run(test(data,tg))
    #asyncio.run(test2(tg,"2026-02"))
    asyncio.run(
        test3(tg)
    )