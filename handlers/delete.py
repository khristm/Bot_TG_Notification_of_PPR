from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from keybords.common import month_user_keyboard
from keybords.parsing import exit_to_menu_keyboard
from utils import ParsingState
from database.crud import get_months, delete_task_in_month
from datetime import datetime

router=Router()

@router.callback_query(F.data=="delete_schedule",F.message.chat.type == "private")
async def delete_schedule(callback:CallbackQuery, session:AsyncSession, state:FSMContext):
    print(f"{datetime.now()} Хэндлер удаления графика ППР, пользователь: {callback.from_user.id}")
    await callback.answer()
    # await callback.message.delete()
    res = await get_months(session, int(callback.from_user.id))
    if not res:
        return await callback.message.edit_text("У тебя нет добавленных записей ППР", reply_markup=await exit_to_menu_keyboard())
    else:
        await state.set_state(ParsingState.waiting_month_for_delete)
        return await callback.message.edit_text(text="Выбери месяц который удаляем:",
                                      reply_markup=await month_user_keyboard(res))

@router.callback_query(ParsingState.waiting_month_for_delete)
async def delete_month(callback:CallbackQuery, session:AsyncSession, state:FSMContext):
    await callback.answer()
    # await callback.message.delete()
    month = callback.data
    res =await delete_task_in_month(session,month,callback.from_user.id)
    await state.clear()
    if res:
        return await callback.message.edit_text("Успешно удалили график ППР на указанный месяц",
                                             reply_markup=await exit_to_menu_keyboard())
    return await callback.message.edit_text("Словили какую-то ошибку и не смогли удалить, попробуй позже",
                                         reply_markup=await exit_to_menu_keyboard())