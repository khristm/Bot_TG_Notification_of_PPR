from aiogram.filters.callback_data import CallbackData
from datetime import datetime, timedelta
import calendar
from aiogram.fsm.state import State, StatesGroup

class MonthSchedule(CallbackData, prefix='MonthSchedule'):
    """Класс колбэков использую при создании динамической клавиатуры с месяцами для добавления графика"""
    month: str

class ParsingState(StatesGroup):
    """Класс для изменения стадий парсинга и передачи между ними данных"""
    waiting_url=State()
    waiting_gid=State()

def get_4_month():
    final_list = []
    month = datetime.now().replace(day=1)
    for i in range(4):
        final_list.append(str(month.year) + '-' + str(month.month))
        day_in_month = calendar.monthrange(month.year, month.month)[1]
        month = month+timedelta(days=day_in_month)
    return final_list


