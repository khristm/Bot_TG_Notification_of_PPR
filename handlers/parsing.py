import aiohttp
from aiogram import Router, types, F
from aiogram.types import Message, CallbackQuery
from keybords.parsing import get_date_schedule, cancel_keyboard, exit_to_menu_keyboard, get_gid_keyboard
from utils import MonthSchedule, ParsingState
from aiogram.fsm.context import FSMContext
from parsing_data.parsing import ModifyUrl, ReadCVSToObject, RequestToGoogle
from sqlalchemy.ext.asyncio import AsyncSession
from database.crud import create_schedule_from_list



router=Router()



@router.callback_query(F.data=='parsing',F.message.chat.type == "private")
async def get_month_for_parsing(callback:CallbackQuery,state:FSMContext):
    """Первый хэндлер для добавления графика, вызывает клавиатуру где динамически формируются 4 месяца - текущий и 3 следующих"""
    # await callback.message.delete()
    await state.set_state(ParsingState.waiting_month)
    await callback.message.edit_text(text="Укажи месяц на который добавляем график:", reply_markup=await get_date_schedule())


@router.callback_query(MonthSchedule.filter(),ParsingState.waiting_month)
async def enter_url(callback:CallbackQuery, callback_data:MonthSchedule, state:FSMContext):
    """Событие нажатия кнопки в клавиатуре с динамическими кнопками с месяцами"""
    month=callback_data.month
    await state.set_state(ParsingState.waiting_url)
    # await callback.message.delete()
    sent_msg = await callback.message.edit_text(f"Ты выбрал месяц: {month}, теперь введи URL таблицы и отправь",
                                  reply_markup=await cancel_keyboard())
    await state.update_data(id_msg=sent_msg.message_id, date=month)

@router.message(F.text,ParsingState.waiting_url)
async def parsing_url(message:Message, session:AsyncSession, state:FSMContext):
    """Хэндлер на перехват ссылки юзера здесь будем начинать парсинг"""
    data=await state.get_data()
    month=data.get("date")
    id_msg=data.get("id_msg")
    await message.bot.delete_message(message.chat.id,id_msg)
    await message.delete()
    user_url=ModifyUrl(message.text)
    async with aiohttp.ClientSession() as httpsession:
        if user_url.errors:
            return await message.answer("Некоректная ссылка", reply_markup=await cancel_keyboard())
        if user_url.url_with_gid is None:
            request = RequestToGoogle(url_user=None,session_obj=httpsession,sheet_id=user_url.id_sheet)
            gid_list=await request.get_gid()
            if len(gid_list)>0:
                await state.set_state(ParsingState.waiting_gid)
                await state.update_data(url=message.text,gid_list=gid_list)
                return await message.answer("Ты прислал ссылку на гугл таблицу без указания конкретно листа,"
                                            " укажи с кого листа добавляем данные",reply_markup=await get_gid_keyboard(gid_list))
            else:
                return await message.answer("Я не смог прочитать листы из твоей таблицы, проверь настройки доступа к ней",
                                        reply_markup=await exit_to_menu_keyboard())
        down_data=RequestToGoogle(user_url.url_with_gid,httpsession,sheet_id=None)
        res = await down_data.get_cvs()
        if res is None:
            return await message.answer("Ошибка запроса на скачивание данных с гугл таблицы, проверь открыт ли доступ к ней",
                                            reply_markup=await exit_to_menu_keyboard())
        data=ReadCVSToObject(res,month)
        if data.errors:
            return await message.answer("Ошибка парсинга гугл таблицы, проверь ее структуру и название столбцов",
                                        reply_markup=await exit_to_menu_keyboard())
        if not await create_schedule_from_list(session,data.list_object,message.from_user.id):
            return await message.answer("Ошибка записи в БД, проверь возможно уже есть график на этот месяц",
                                        reply_markup=await exit_to_menu_keyboard())
        return await message.answer("Данные добавлены", reply_markup=await exit_to_menu_keyboard())

@router.callback_query(ParsingState.waiting_gid)
async def enter_gid(callback:CallbackQuery, session:AsyncSession, state:FSMContext):
    data = await state.get_data()
    month=data.get("date")
    gid_list=data.get("gid_list")
    url=data.get("url")
    gid_user_index=callback.data
    user_url=ModifyUrl(url)
    user_url.create_url_with_gid(gid_list[int(gid_user_index)]['gid'])
    # await callback.message.delete()
    async with aiohttp.ClientSession() as httpsession:
        request = RequestToGoogle(url_user=user_url.url_with_gid,session_obj=httpsession,sheet_id=None)
        cvs_data = await request.get_cvs()
        read_cvs = ReadCVSToObject(cvs_data,month)
        if read_cvs.errors:
            return await callback.message.edit_text("Ошибка парсинга гугл таблицы,"
                                                 " проверь ее структуру, название столбцов,"
                                                 " возможно не совпадает указанный месяц и даты в таблице",
                                        reply_markup=await exit_to_menu_keyboard())
        if not await create_schedule_from_list(session,read_cvs.list_object,callback.from_user.id):
            return await callback.message.edit_text("Ошибка записи в БД, проверь возможно уже есть график на этот месяц",
                                        reply_markup=await exit_to_menu_keyboard())
        return await callback.message.edit_text("Данные добавлены", reply_markup=await exit_to_menu_keyboard())



