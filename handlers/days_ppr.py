from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from keybords.common import first_3_day_keyboard
from keybords.parsing import exit_to_menu_keyboard, get_date_schedule
from utils import StateForDaysPPR, get_days_ppr, MonthSchedule
from datetime import datetime

router=Router()

@router.callback_query(F.data=="get_days_ppr")
async def get_days(callback:CallbackQuery, state:FSMContext):
    print(f"{datetime.now()} Хэндлер подсчета доступных дней ппр, пользователь: {callback.from_user.id}")
    await state.set_state(StateForDaysPPR.waiting_month)
    return await callback.message.edit_text(text="Выбери месяц на который нужны дни для ППР: ",reply_markup=await get_date_schedule())

@router.callback_query(MonthSchedule.filter(),StateForDaysPPR.waiting_month)
async def read_month(callback:CallbackQuery, callback_data:MonthSchedule, state:FSMContext):
    await state.set_state(StateForDaysPPR.waiting_date)
    month=callback_data.month
    return await callback.message.edit_text(text="Выбери первый день полной смены в месяце: ",reply_markup=await first_3_day_keyboard(month))

@router.callback_query(StateForDaysPPR.waiting_date)
async def push_date_str(callback:CallbackQuery, state:FSMContext):
    await state.clear()
    date=callback.data
    msg = await get_days_ppr(date)
    return await callback.message.edit_text(text=msg,reply_markup=await exit_to_menu_keyboard())

