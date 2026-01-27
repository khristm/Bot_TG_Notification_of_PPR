from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from keybords.common import month_user_keyboard
from keybords.parsing import exit_to_menu_keyboard
from utils import ParsingState
from database.crud import get_months, get_task_in_month

router=Router()

@router.callback_query(F.data=="view_schedule")
async def view_schedule(callback:CallbackQuery, session:AsyncSession, state:FSMContext):
    await callback.answer()
    await callback.message.delete()
    res = await get_months(session, int(callback.from_user.id))
    if not res:
        return await callback.message.answer("У тебя нет добавленных записей ППР",reply_markup=await exit_to_menu_keyboard())
    else:
        await state.set_state(ParsingState.waiting_month)
        return await callback.message.answer(text="Выбери месяц который просматриваем:",
                                      reply_markup=await month_user_keyboard(res))


@router.callback_query(ParsingState.waiting_month)
async def get_schedule(callback:CallbackQuery, session:AsyncSession, state:FSMContext):
    await callback.answer()
    await callback.message.delete()
    month=callback.data
    list_task=await get_task_in_month(session, month, callback.from_user.id)
    await state.clear()
    if not list_task:
        return await callback.message.answer("Не нашли у тебя графиков ППР",reply_markup=await exit_to_menu_keyboard())
    else:
        for task in list_task:
            await callback.message.answer(text=f"№ здания: {task.number}\n"
                                               f"Дата: {task.date_time}\n"
                                               f"Адрес: {task.adress}\n"
                                               f"Вид работ: {task.type}\n"
                                               f"Исполнители: {task.workers}")
        return await callback.message.answer("Выше список работ на месяц",reply_markup=await exit_to_menu_keyboard())


