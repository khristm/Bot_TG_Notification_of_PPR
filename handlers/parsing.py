import aiohttp
from aiogram import Router, types, F
from aiogram.types import Message, CallbackQuery
from keybords.parsing import get_date_schedule, cancel_keyboard, exit_to_menu_keyboard
from utils import MonthSchedule, ParsingState
from aiogram.fsm.context import FSMContext
from parsing_data.parsing import ModifyUrl, ReadCVSToObject, RequestToGoogle
from sqlalchemy.ext.asyncio import AsyncSession
from database.crud import create_schedule_from_list



router=Router()



@router.callback_query(F.data=='parsing')
async def get_month_for_parsing(callback:CallbackQuery):
    """Первый хэндлер для добавления графика, вызывает клавиатуру где динамически формируются 4 месяца - текущий и 3 следующих"""
    await callback.message.delete()
    await callback.message.answer(text="Укажи месяц на который добавляем график:", reply_markup=await get_date_schedule())


@router.callback_query(MonthSchedule.filter())
async def enter_url(callback:CallbackQuery, callback_data:MonthSchedule, state:FSMContext):
    """Событие нажатия кнопки в клавиатуре с динамическими кнопками с месяцами"""
    month=callback_data.month
    ParsingState.date=month
    await state.set_state(ParsingState.url)
    await callback.message.delete()
    sent_msg = await callback.message.answer(f"Ты выбрал месяц: {month}, теперь введи URL таблицы и отправь",
                                  reply_markup=await cancel_keyboard())
    await state.update_data(id_msg=sent_msg.message_id)

@router.message(F.text,ParsingState.url)
async def parsing_url(message:Message, session:AsyncSession, state:FSMContext):
    """Хэндлер на перехват ссылки юзера здесь будем начинать парсинг"""

    await message.bot.delete_messages(message.chat.id, ParsingState.id_msg)
    await message.delete()
    user_url=ModifyUrl(message.text)
    if user_url.errors:
        return await message.answer("Некоректная ссылка", reply_markup=await cancel_keyboard())
    if user_url.url_with_gid is None:
        return await message.answer("Тут создам клавиатуру для выбора gid")
    async with aiohttp.ClientSession() as httpsession:
        down_data=RequestToGoogle(user_url.url_with_gid,httpsession,sheet_id=None)
        res = await down_data.get_cvs()
        if res is None:
            return await message.answer("Ошибка запроса на скачивание данных с гугл таблицы, проверь открыт ли доступ к ней",
                                        reply_markup=await exit_to_menu_keyboard())
    data=ReadCVSToObject(res,ParsingState.date)
    if data.errors:
        return await message.answer("Ошибка парсинга гугл таблицы, проверь ее структуру и название столбцов",
                                    reply_markup=await exit_to_menu_keyboard())
    if not await create_schedule_from_list(session,data.list_object,message.from_user.id):
        return await message.answer("Ошибка записи в БД, проверь возможно уже есть график на этот месяц",
                                    reply_markup=await exit_to_menu_keyboard())
    return await message.answer("Данные добавлены", reply_markup=await exit_to_menu_keyboard())

