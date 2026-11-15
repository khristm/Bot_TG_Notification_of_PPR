from database.crud import get_all_workers
import aiohttp
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from keybords.parsing import cancel_keyboard, exit_to_menu_keyboard, get_gid_keyboard
from utils import ParsingState
from aiogram.fsm.context import FSMContext
from parsing_data.csv_parsing import ModifyUrl, RequestToGoogle
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from parsing_data import parsing_workers_in_handler

router = Router()

@router.callback_query(F.data=="view_workers",F.message.chat.type == "private")
async def get_workers(callback:CallbackQuery, session:AsyncSession):
    user_id = callback.from_user.id
    await callback.answer()
    workers = await get_all_workers(session=session, tg_id=user_id)
    if not workers:
        return await callback.message.edit_text(text="Справочник сотрудников пустой...",
                                             reply_markup=await exit_to_menu_keyboard())
    text = "Сотрудники:\n"
    for worker in workers:
        text += f"<b>{worker.name}</b>, никнейм: {worker.nickname} \n"
    return await callback.message.edit_text(text=text,
                                            reply_markup=await exit_to_menu_keyboard(),
                                            parse_mode='HTML')

@router.callback_query(F.data == 'upload_workers')
async def get_workers_url(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ParsingState.waiting_url_workers)
    msg = await callback.message.edit_text(
        f"Отправь ссылку на гугл таблицу с именами исполнителей и их никами в ТГ, "
            f"ожидаю таблицу с именами колонок: ФИО, ник",
        reply_markup=await cancel_keyboard())
    await state.update_data(id_msg=msg.message_id)
    return

@router.message(F.text,ParsingState.waiting_url_workers)
async def check_workers_url(message:Message, session:AsyncSession, state: FSMContext):
    await message.delete()
    data = await state.get_data()
    id_msg = data.get("id_msg")
    user_url = ModifyUrl(message.text)
    async with aiohttp.ClientSession() as httpsession:
        if user_url.errors:#если класс не смог найти ссылку на гугл таблицу в присланном атрибут ошибка встает в статус истина
            return await message.bot.edit_message_text(chat_id=message.chat.id,message_id=id_msg,
                                                       text="Некоректная ссылка", reply_markup=await cancel_keyboard())
        if user_url.url_with_gid is None:#если не смогли получить ссылку на конкретную таблицу из документа этот атрибут None
            request = RequestToGoogle(url_user=None,session_obj=httpsession,sheet_id=user_url.id_sheet)#мой класс для сетевых запросов для запроса к гуглу нужен id документа
            gid_list=await request.get_gid()#сам запрос к гуглу, вернет список листов в гугл таблице
            if len(gid_list)>0:#проверка что список листов не пустой
                await state.set_state(ParsingState.waiting_gid_workers)
                await state.update_data(url=message.text,gid_list=gid_list)
                #сменили этап FSM и записали данные в хранилище FSM дальше вызываем создание новой клавиатуры куда аргументом передаем список листов
                return await message.bot.edit_message_text(chat_id=message.chat.id,message_id=id_msg,
                                                           text="Ты прислал ссылку на гугл таблицу без указания конкретно листа,"
                                            " укажи с кого листа добавляем данные",reply_markup=await get_gid_keyboard(gid_list))
            return await message.bot.edit_message_text(chat_id=message.chat.id,message_id=id_msg,
                                text=f"Не нашел листов в твоем гугл документе, проверь открыт ли доступ по ссылке",
                                                       reply_markup=await exit_to_menu_keyboard())
        down_data = RequestToGoogle(url_user=user_url.url_with_gid, session_obj=httpsession,sheet_id=None)
        csv = await down_data.get_cvs()
        if csv is None:
            return message.bot.edit_message_text(chat_id=message.chat.id,message_id=id_msg,text="Ошибка загрузки "
                                                                                                "данных с гугл таблиц",
                                                 reply_markup=await exit_to_menu_keyboard())
    return await parsing_workers_in_handler(message, csv, session, id_msg)


@router.callback_query(ParsingState.waiting_gid_workers)
async def enter_gid_workers(callback:CallbackQuery, session:AsyncSession, state:FSMContext):
    data = await state.get_data()
    gid_list = data.get("gid_list")
    url = data.get("url")
    gid_user_index = callback.data  # в колбэке приходит индекс выбранного листа из списка листов
    user_url = ModifyUrl(url)  # снова создаем объект с введеным пользователем адресом
    user_url.create_url_with_gid(gid_list[int(gid_user_index)]['gid'])
    # вызываем метод ручного создания ссылку на таблицу с конретным листом обрщаемся к списку листов выбранным пользователем индексом
    async with aiohttp.ClientSession() as httpsession:
        request = RequestToGoogle(url_user=user_url.url_with_gid, session_obj=httpsession, sheet_id=None)
        # аналогичное скачивание с готовой ссылкой на cvs
        try:
            cvs_data = await request.get_cvs()
        except Exception as e:
            logger.error(f"Неуспешная попытка загрузить данные с гугл таблиц: {e}")
            return await callback.message.edit_text(f"Ошибка при загрузке данных с гугл таблицы, "
                                                    f"попробуйте повторить позже",
                                                    reply_markup=await exit_to_menu_keyboard())
    return await parsing_workers_in_handler(callback, cvs_data, session)