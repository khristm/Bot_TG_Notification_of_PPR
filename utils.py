from aiogram.filters.callback_data import CallbackData
from datetime import datetime, timedelta
import calendar
from aiogram.fsm.state import State, StatesGroup
from database.crud import get_list_today_tasks
from sqlalchemy.ext.asyncio import AsyncSession


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
            number_task=task.Task.number
            adress_task=task.Task.adress
            workers=task.Task.workers
            type_work=task.Task.type
            date_time=task.Task.date_time
            chat_id=task[1]
            result_info=(f'------------------------------\n'
                         f' 🔹Номер задания: {number_task}\n'
                         f' 🏢Адрес: {adress_task}\n'
                         f' ⏰Дата: {date_time}\n'
                         f' 👥Исполнители: {workers}\n'
                         f' 🛠Тип задачи: {type_work}\n')
            msg=msg+result_info
        await bot.send_message(chat_id=chat_id, text=msg)







class MonthSchedule(CallbackData, prefix='MonthSchedule'):
    """Класс колбэков использую при создании динамической клавиатуры с месяцами для добавления графика"""
    month: str

class ParsingState(StatesGroup):
    """Класс для изменения стадий парсинга и передачи между ними данных"""
    waiting_url=State()
    waiting_gid=State()
    waiting_month=State()
    waiting_month_for_delete=State()

def get_4_month():
    final_list = []
    month = datetime.now().replace(day=1)
    for i in range(4):
        final_list.append(str(month.year) + '-' + str(month.month))
        day_in_month = calendar.monthrange(month.year, month.month)[1]
        month = month+timedelta(days=day_in_month)
    return final_list


