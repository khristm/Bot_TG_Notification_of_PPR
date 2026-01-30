from sqlalchemy import select, delete
from schemas import UserSchema, TaskSchema
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Task
from typing import List
from datetime import datetime, timedelta




async def get_user(session:AsyncSession,tg_token):
    """На входе объект сессии и токен пользователя телеграмм ищем в БД юзера с таким токеном,
    если есть возвращаем объект пользователя где атрибуты поля из таблицы, если нет то None"""
    res=await session.execute(select(User).where(User.tg_id==tg_token))
    user=res.scalar_one_or_none()
    return user

async def create_user(session:AsyncSession,user_data:UserSchema):
    """Создание юзера в бд, перед добавлением поиск в бд юзера с таким же ид телеграмм
    если результат не None, возвращаем False"""
    user= await get_user(session,user_data.tg_id)
    if user is not None:
        return False
    user=User(phone_number=user_data.phone_number,tg_id=user_data.tg_id)
    session.add(user)
    await session.commit()
    return True

async def update_chat_id(session:AsyncSession,user_data:UserSchema):
    user = await get_user(session,user_data.tg_id)
    if user is None:
        return False
    user.chat_id=user_data.chat_id
    await session.commit()
    return True

async def create_schedule(session:AsyncSession,user_task:TaskSchema,tg_id):
    """Создание расписания, проверка существования пользователя, проверка дублирования месяца"""
    user = await get_user(session,tg_id)
    if user is None:
        return False
    res = await session.execute(select(Task).where(Task.month==user_task.month,Task.user_id==user.id))
    task = res.scalar_one_or_none()
    if task is not None:
        return False
    task=Task(user_id=user.id,adress=user_task.adress,month=user_task.month,date_time=str(user_task.date_time),
              number=user_task.number,workers=user_task.workers,type=user_task.type)
    session.add(task)
    await session.commit()
    return True

async def create_schedule_from_list(session:AsyncSession,user_task_list:List[TaskSchema],tg_id):
    """Создание расписания из списка объектов, проверка существования пользователя,
         проверка дублирования месяца - данные для этой проверки берем из первого объекта в списке,
         у всех объектов эти данные одинаковые"""
    user = await get_user(session,tg_id)
    if user is None:
        print("Не нашли пользователя")
        return False
        #нет пользователя в бд
    print("Проверили существование пользователя")
    res = await session.execute(select(Task).where(Task.month==user_task_list[0].month,Task.user_id==user.id))
    task = res.scalar()
    if task is not None:
        print("res.scalar() вернул не None, у этого пользователя есть записи на этот месяц")
        return False
        #записи этого месяца уже есть, нужно сначала их удалить чтоб не допустить битой информации
    print("Проверили данные из бд на дублирование")
    task_list=[Task(user_id=user.id,adress=el.adress,month=el.month,date_time=str(el.date_time),
              number=el.number,workers=el.workers,type=el.type) for el in user_task_list]
    session.add_all(task_list)
    await session.commit()
    return True

async def delete_tasks(session:AsyncSession,tg_id, month):
    user = await get_user(session,tg_id)
    if user is None:
        return False
    await session.execute(delete(Task).where(Task.month==month,Task.user_id==user.id))
    await session.commit()
    return True

async def get_months(session:AsyncSession,tg_id):
    """Возращает список месяцев которые есть у юзера в бд"""
    user = await get_user(session,tg_id)
    if user is None:
        return False
    res = await session.execute(select(Task.month).
                                where(Task.user_id==user.id)
                                .distinct()
                                .order_by(Task.month))
    return res.scalars().all()

async def get_task_in_month(session,month,tg_id):
    user = await get_user(session,tg_id)
    if user is None:
        return []
    res = await session.execute(select(Task).where(Task.month==month,Task.user_id==user.id).order_by(Task.date_time))
    return res.scalars().all()

async def delete_task_in_month(session, month,tg_id):
    user = await get_user(session,tg_id)
    if user is None:
        return False
    try:
        await session.execute(delete(Task).where(Task.month==month,Task.user_id==user.id))
        await session.commit()
        return True
    except:
        await session.rollback()
        return False

async def get_tasks_today(session:AsyncSession,user:User,date_check, date_now):
    """Функция запроса задач из БД, для ежедневного бота оповещателя """
    # user = await get_user(session,tg_id)
    # if user is None:
    #     return None
    # date_now = datetime.now()
    # date_chek = date_now + timedelta(hours=23)
    res = await session.execute(select(Task,User.chat_id).join(User, Task.user_id == User.id).
                                where(Task.date_time>date_now,
                                      Task.date_time<date_check,Task.user_id==user.id).order_by(Task.date_time))
    return res.all()

async def get_all_user(session):
    """Выборка всех пользователей с указанным chat_id для оповещений"""
    res = await session.execute(select(User).where(User.chat_id!=None))
    user_list = res.scalars().all()
    return user_list

async def get_list_today_tasks(session:AsyncSession):
    """Запрос актуальных задач, для пользователей с указанным chat_id"""
    user_list = await get_all_user(session)
    date_now = datetime.now()
    date_check = date_now + timedelta(hours=23)
    task_list = []
    for user in user_list:
        res = await get_tasks_today(session, user, date_check, date_now)
        task_list.append(res)
    return task_list

async def delete_chat_id(session:AsyncSession,tg_id):
    user = await get_user(session, tg_id)
    if user is None:
        return False
    user.chat_id=None
    await session.commit()
    return True