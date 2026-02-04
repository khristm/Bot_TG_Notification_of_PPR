from calendar import monthrange
from aiogram.filters.callback_data import CallbackData
from datetime import datetime, timedelta
import calendar
from aiogram.fsm.state import State, StatesGroup
from database.crud import get_list_today_tasks
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.exceptions import TelegramForbiddenError


async def everyday_check_to_msg(session:AsyncSession,bot):
    list_tasks=await get_list_today_tasks(session)
    #Результат выборки [[(<database.models.Task object at 0x0000015EFCFBA660>, 'чат ид тг'), (<database.models.Task object at 0x0000015EFD000B90>, 'чат ид тг')]]
    for users in list_tasks:
        if not users:
            continue
        msg=f'🔔В ближайшее время запланированны задания:\n'
        chat_id=0
        #нужно проверить что список не пустой
        for task in users:
            if not task:
                continue
            if task.Task.number is None: number_task="❌"
            else: number_task=task.Task.number
            if task.Task.adress is None: adress_task="❌"
            else: adress_task=task.Task.adress
            if task.Task.workers is None: workers="❌"
            else: workers=task.Task.workers
            if task.Task.type is None: type_work="❌"
            else: type_work=task.Task.type
            date_time=task.Task.date_time
            chat_id=task[1]
            result_info=(f'-------------------------\n'
                         f' 🔹<i>Номер задания:</i><b> {number_task}</b>\n'
                         f' 🏢<i>Адрес: </i><b>{adress_task}</b>\n'
                         f' ⏰<i>Дата: </i><b>{date_time}</b>\n'
                         f' 👥<i>Исполнители: </i><b>{workers}</b>\n'
                         f' 🛠<i>Тип задачи: </i><b>{type_work}</b>\n')
            msg=msg+result_info
        try:
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode='HTML')
        except TelegramForbiddenError:
            print(f"Бот заблокирован в чате {chat_id}, не смогли туда послать оповещение")


class MonthSchedule(CallbackData, prefix='MonthSchedule'):
    """Класс колбэков использую при создании динамической клавиатуры с месяцами для добавления графика"""
    month: str

class ParsingState(StatesGroup):
    """Класс для изменения стадий парсинга и передачи между ними данных"""
    waiting_url=State()
    waiting_gid=State()
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



