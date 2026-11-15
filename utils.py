from calendar import monthrange
from aiogram.filters.callback_data import CallbackData
from datetime import datetime, timedelta
import calendar
from aiogram.fsm.state import State, StatesGroup
from database.crud import get_list_today_tasks, search_workers_by_name
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import asyncio


async def get_workers_nicknames_cache(worker_list: set, user_id: int, session: AsyncSession)->dict:
    workers_nicknames = {}
    workers = await search_workers_by_name(worker_list, session, user_id)
    logger.debug(f"WORKERS FROM DB: {workers}")
    if not workers:
        return workers_nicknames
    for worker in worker_list:
        for worker_from_db in workers:
            if worker in worker_from_db.name:
                workers_nicknames[worker] = worker_from_db.nickname
                break
    return workers_nicknames

async def everyday_check_to_msg(session:AsyncSession,bot):
    try:
        list_tasks=await get_list_today_tasks(session)
        #Результат выборки [[(<database.models.Task object at 0x0000015EFCFBA660>, 'чат ид тг', 'tg_id юзера'),
        # (<database.models.Task object at 0x0000015EFD000B90>, 'чат ид тг')]]
        # сбор кэша никнеймов сотрудников
        workers_in_task = {}
        cache_nicknames = {}
        for task in list_tasks:
            for user_task in task:
                user_id = user_task[2]
                workers_str_in_task = user_task.Task.workers.split(",")
                workers_str_in_task = [worker.strip() for worker in workers_str_in_task]
                if workers_in_task.get(user_id):
                    workers_in_task[user_id] += workers_str_in_task
                else:
                    workers_in_task[user_id] = workers_str_in_task
        for user in workers_in_task.keys():
            cache_nicknames[user] = await get_workers_nicknames_cache(set(workers_in_task[user]), user, session)
        # итерация для рассылки оповещений
        for users in list_tasks:
            msg=f'🔔В ближайшее время запланированны задания:\n'
            chat_id=0
            #нужно проверить что список не пустой
            if not users: continue
            for task in users:
                user_id = task[2]
                if task.Task.number is None: number_task="❌"
                else: number_task=task.Task.number
                if task.Task.address is None: address_task= "❌"
                else: address_task=task.Task.address
                if task.Task.workers is None: str_workers_to_tg="❌"
                else:
                    workers=task.Task.workers
                    workers_list = workers.split(",")
                    str_workers_to_tg = ""
                    for worker in workers_list:
                        if cache_nicknames.get(user_id) is None:
                            str_workers_to_tg = workers
                            break
                        str_workers_to_tg += f"{worker} {cache_nicknames[user_id].get(worker.strip())}, " \
                            if cache_nicknames[user_id].get(worker.strip()) else f"{worker}, "
                    str_workers_to_tg = str_workers_to_tg.rstrip(", ")
                if task.Task.type is None: type_work="❌"
                else: type_work=task.Task.type
                date_time=task.Task.date_time
                chat_id=task[1]
                result_info=(f'-------------------------\n'
                             f' 🔹<i>Номер задания:</i><b> {number_task}</b>\n'
                             f' 🏢<i>Адрес: </i><b>{address_task}</b>\n'
                             f' ⏰<i>Дата: </i><b>{date_time}</b>\n'
                             f' 👥<i>Исполнители: </i><b>{str_workers_to_tg}</b>\n'
                             f' 🛠<i>Тип задачи: </i><b>{type_work}</b>\n')
                msg=msg+result_info
            retry = 3
            i = 1
            while True:
                try:
                    await bot.send_message(chat_id=chat_id, text=msg, parse_mode='HTML')
                    break
                except Exception as e:
                    logger.error(f"Бот словил ошибку при попытке отправки ежедневного оповещения в чат: {chat_id},"
                                 f" попытка: {i}"
                                 f" ошибка: {e}")
                    if i == retry:
                        logger.exception(e)
                        break
                    i += 1
                    await asyncio.sleep(3)
    except Exception as e:
        logger.exception(e)
        return False
    return True


class MonthSchedule(CallbackData, prefix='MonthSchedule'):
    """Класс колбэков использую при создании динамической клавиатуры с месяцами для добавления графика"""
    month: str

class ParsingState(StatesGroup):
    """Класс для изменения стадий парсинга и передачи между ними данных"""
    waiting_url=State()
    waiting_gid=State()
    waiting_url_workers = State()
    waiting_gid_workers = State()
    waiting_month=State()
    waiting_month_for_delete=State()

class StateForDaysPPR(StatesGroup):
    waiting_month=State()
    waiting_date=State()

def get_4_month():
    final_list = []
    month = datetime.now().replace(day=1)
    for i in range(4):
        final_list.append(str(month.year) + '-' + str(month.month))
        day_in_month = calendar.monthrange(month.year, month.month)[1]
        month = month+timedelta(days=day_in_month)
    return final_list

async def get_3_days(month:str):
    month = datetime.strptime(month, '%Y-%m').replace(day=1)
    list_days=[f"{str(month.year)}-{str(month.month)}-{str(month.day)}"]
    for i in range(2):
        month = month + timedelta(days=1)
        list_days.append(f"{str(month.year)}-{str(month.month)}-{str(month.day)}")
    return list_days


async def get_days_ppr(first_day:str):
    first_day=datetime.strptime(first_day, '%Y-%m-%d')
    month=first_day.month
    day_ppr=first_day
    list_days=[]
    while day_ppr.month==month:
        list_days.append(day_ppr)
        day_ppr+=timedelta(days=2)
    final_str=f"Список дат доступных для ППР на {first_day.strftime('%m.%Y')}:\n"
    day_week=("понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье")
    day_in_month=monthrange(first_day.year,first_day.month)[1]
    for day in list_days:
        if day<first_day.replace(day=1)+timedelta(days=3) or day>first_day.replace(day=day_in_month)-timedelta(days=2):
            continue
        if day.weekday()!=5 and day.weekday()!=6 and day.weekday()!=0:
            day_str=f"🌙  {day.strftime('%d.%m')} {day_week[day.weekday()]}\n"
            final_str+=day_str
    return final_str



