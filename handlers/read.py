from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from keybords.common import month_user_keyboard
from keybords.parsing import exit_to_menu_keyboard
from utils import ParsingState
from database.crud import get_months, get_task_in_month
from datetime import datetime
from loguru import logger

router=Router()

@router.callback_query(F.data=="view_schedule",F.message.chat.type == "private")
async def view_schedule(callback:CallbackQuery, session:AsyncSession, state:FSMContext):
    logger.debug(f"Хэндлер просмотра графика ППР, пользователь: {callback.from_user.id}")
    await callback.answer()
    res = await get_months(session, int(callback.from_user.id))
    if not res:
        return await callback.message.edit_text("У тебя нет добавленных записей ППР",reply_markup=await exit_to_menu_keyboard())
    else:
        await state.set_state(ParsingState.waiting_month)
        return await callback.message.edit_text(text="Выбери месяц который просматриваем:",
                                      reply_markup=await month_user_keyboard(res))


@router.callback_query(ParsingState.waiting_month)
async def get_schedule(callback:CallbackQuery, session:AsyncSession, state:FSMContext):
    await callback.answer()
    month=callback.data
    list_task=await get_task_in_month(session, month, callback.from_user.id)
    await state.clear()
    if not list_task:
        return await callback.message.edit_text("Не нашли у тебя графиков ППР",reply_markup=await exit_to_menu_keyboard())
    else:
        task_msg="Cписок работ на выбранный месяц:\n"
        for task in list_task:
            if task.number is None: number=""
            else: number=task.number
            if task.adress is None: adress=""
            else: adress=task.adress
            if task.type is None: type_task=""
            else: type_task=task.type
            if task.workers is None: workers=""
            else: workers=task.workers
            task_from_db=(f"--------------\n"
                        f"<i>№ задания:</i> <b>{number}</b>\n"
                        f"<i>Дата:</i> <b>{task.date_time}</b>\n"
                        f"<i>Адрес:</i> <b>{adress}</b>\n"
                        f"<i>Вид работ:</i> <b>{type_task}</b>\n"
                        f"<i>Исполнители: </i><b>{workers}</b>\n")
            task_msg+=task_from_db
        return await callback.message.edit_text(task_msg,reply_markup=await exit_to_menu_keyboard(), parse_mode='HTML')


