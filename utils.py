from aiogram.filters.callback_data import CallbackData
from datetime import datetime, timedelta
import calendar

class MonthSchedule(CallbackData, prefix='MonthSchedule'):
    month: str

def get_4_month():
    final_list = []
    month = datetime.now().replace(day=1)
    for i in range(4):
        final_list.append(str(month.year) + '-' + str(month.month))
        day_in_month = calendar.monthrange(month.year, month.month)[1]
        month = month+timedelta(days=day_in_month)
    return final_list


