from aiogram.types import CallbackQuery
from config import config
from database.crud import create_schedule_from_list, insert_workers
from loguru import logger
from parsing_data.ai_parsing import ai_parsing_tasks, ai_parsing_workers
from keybords.parsing import exit_to_menu_keyboard
from parsing_data.pandas_parsing import ReadCVSToObject

async def get_message_func(event, id_msg):
    if isinstance(event, CallbackQuery):
        await event.answer()  # Гасим часики на инлайн-кнопке
        chat_id = event.message.chat.id
        # Если id_msg не передан, берем ID сообщения, на котором нажали кнопку
        target_msg_id = id_msg if id_msg else event.message.message_id
        user_id = event.from_user.id  # В колбэке юзер лежит тут!
    else:
        chat_id = event.chat.id
        # Для сообщения обязательно должен быть передан id_msg (так как мы редактируем сообщение бота)
        target_msg_id = id_msg if id_msg else event.message_id
        user_id = event.from_user.id
        # Вспомогательная функция для сокращения кода редактирования
    async def edit_text(text, reply_markup=None):
        return await event.bot.edit_message_text(
            chat_id=chat_id,
            message_id=target_msg_id,
            text=text,
            reply_markup=reply_markup
        )
    return edit_text, user_id


async def parsing_tasks_in_handler(event, csv, month, db_session, id_msg=None):
    read_cvs = ReadCVSToObject(csv, month=month)
    read_cvs.parse_tasks()
    finish_csv = read_cvs.list_object
    edit_text, user_id = await get_message_func(event, id_msg)
    if read_cvs.errors and config.ai_token and config.ai_api_url and config.ai_model:
        await edit_text("Я не справился самостоятельно с парсингом, попрошу ИИ помочь, придется "
                                         "подождать чуть подольше....", reply_markup=await exit_to_menu_keyboard())
        result_ai_parsing, ai_errors = await ai_parsing_tasks(csv, month)
        if ai_errors:
            return await edit_text(f"ИИ тоже не справился с твоей таблицей, его проблема: "
                                                    f"{ai_errors}", reply_markup=await exit_to_menu_keyboard())
        finish_csv = result_ai_parsing
    elif read_cvs.errors and (config.ai_token is None or config.ai_api_url is None or config.ai_model is None):
        return await edit_text("Ошибка парсинга гугл таблицы,"
                                                " проверь ее структуру, название столбцов,"
                                                " возможно не совпадает указанный месяц и даты в таблице",
                                                reply_markup=await exit_to_menu_keyboard())
    if not await create_schedule_from_list(db_session, finish_csv, user_id):
        return await edit_text("Ошибка записи в БД, проверь "
                                                          "возможно уже есть график на этот месяц",
                                                reply_markup=await exit_to_menu_keyboard())
    logger.debug(f"Хэндлер парсинга графика ппр, данные добавлены")
    return await edit_text("Данные добавлены", reply_markup=await exit_to_menu_keyboard())

async def parsing_workers_in_handler(event, csv, db_session, id_msg=None):
    read_cvs = ReadCVSToObject(csv)
    read_cvs.parse_workers()
    finish_data = read_cvs.list_object
    edit_text, user_id = await get_message_func(event, id_msg)
    if read_cvs.errors and config.ai_token and config.ai_api_url and config.ai_model:
        await edit_text("Я не справился самостоятельно с парсингом, попрошу ИИ помочь, придется "
                                         "подождать чуть подольше....", reply_markup=await exit_to_menu_keyboard())
        result_ai_parsing, ai_errors = await ai_parsing_workers(csv)
        if ai_errors:
            return await edit_text(f"ИИ тоже не справился с твоей таблицей, его проблема: "
                                                    f"{ai_errors}", reply_markup=await exit_to_menu_keyboard())
        finish_data = result_ai_parsing
    elif read_cvs.errors and (config.ai_token is None or config.ai_api_url is None or config.ai_model is None):
        return await edit_text("Ошибка парсинга гугл таблицы, проверь ее структуру и данные",
                               reply_markup=await exit_to_menu_keyboard())
    if not await insert_workers(session=db_session, workers=finish_data, tg_id=user_id):
        return await edit_text("Ошибка записи в БД",reply_markup=await exit_to_menu_keyboard())
    logger.debug(f"Хэндлер парсинга справочника сотрудников, данные добавлены")
    return await edit_text("Сотрудники обновлены", reply_markup=await exit_to_menu_keyboard())