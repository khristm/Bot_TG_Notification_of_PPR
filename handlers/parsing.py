import aiohttp
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from keybords.parsing import get_date_schedule, cancel_keyboard, exit_to_menu_keyboard, get_gid_keyboard
from utils import MonthSchedule, ParsingState
from aiogram.fsm.context import FSMContext
from parsing_data.parsing import ModifyUrl, ReadCVSToObject, RequestToGoogle
from sqlalchemy.ext.asyncio import AsyncSession
from database.crud import create_schedule_from_list
from datetime import datetime



router=Router()



@router.callback_query(F.data=='parsing',F.message.chat.type == "private")
async def get_month_for_parsing(callback:CallbackQuery,state:FSMContext):
    """Первый хэндлер для добавления графика, вызывает клавиатуру где динамически формируются 4 месяца - текущий и 3 следующих"""
    # await callback.message.delete()
    print(f"{datetime.now()} Хэндлер начала парсинга графика ппр, пользователь: {callback.from_user.id}")
    await state.set_state(ParsingState.waiting_month)
    await callback.message.edit_text(text="Укажи месяц на который добавляем график:", reply_markup=await get_date_schedule())


@router.callback_query(MonthSchedule.filter(),ParsingState.waiting_month)
async def enter_url(callback:CallbackQuery, callback_data:MonthSchedule, state:FSMContext):
    """Событие нажатия кнопки в клавиатуре с динамическими кнопками с месяцами"""
    print(f"{datetime.now()} Хэндлер парсинга, выбран месяц, пользователь: {callback.from_user.id}")
    month=callback_data.month
    await state.set_state(ParsingState.waiting_url)
    # await callback.message.delete()
    sent_msg = await callback.message.edit_text(f"Ты выбрал месяц: {month}, теперь введи URL таблицы и отправь",
                                  reply_markup=await cancel_keyboard())
    await state.update_data(id_msg=sent_msg.message_id, date=month)

@router.message(F.text,ParsingState.waiting_url)
async def parsing_url(message:Message, session:AsyncSession, state:FSMContext):
    """Хэндлер на перехват ссылки юзера здесь будем начинать парсинг"""
    print(f"{datetime.now()} Хэндлер парсинга юзер ввел URL таблицы, пользователь: {message.from_user.id}")
    data=await state.get_data()
    month=data.get("date")
    id_msg=data.get("id_msg")#достаем данные из FSM
    #await message.bot.delete_message(message.chat.id,id_msg)
    await message.delete()
    user_url=ModifyUrl(message.text)#используем мой класс для модификации ссылки user_url теперь объект с атрибутами
    async with aiohttp.ClientSession() as httpsession:
        if user_url.errors:#если класс не смог найти ссылку на гугл таблицу в присланном атрибут ошибка встает в статус истина
            return await message.bot.edit_message_text(chat_id=message.chat.id,message_id=id_msg,
                                                       text="Некоректная ссылка", reply_markup=await cancel_keyboard())
        if user_url.url_with_gid is None:#если не смогли получить ссылку на конкретную таблицу из документа этот атрибут None
            request = RequestToGoogle(url_user=None,session_obj=httpsession,sheet_id=user_url.id_sheet)#мой класс для сетевых запросов для запроса к гуглу нужен id документа
            gid_list=await request.get_gid()#сам запрос к гуглу, вернет список листов в гугл таблице
            if len(gid_list)>0:#проверка что список листов не пустой
                await state.set_state(ParsingState.waiting_gid)
                await state.update_data(url=message.text,gid_list=gid_list)
                #сменили этап FSM и записали данные в хранилище FSM дальше вызываем создание новой клавиатуры куда аргументом передаем список листов
                return await message.bot.edit_message_text(chat_id=message.chat.id,message_id=id_msg,
                                                           text="Ты прислал ссылку на гугл таблицу без указания конкретно листа,"
                                            " укажи с кого листа добавляем данные",reply_markup=await get_gid_keyboard(gid_list))
            else:
                return await message.bot.edit_message_text(chat_id=message.chat.id,message_id=id_msg,
                                                           text="Я не смог прочитать листы из твоей таблицы, проверь настройки доступа к ней",
                                        reply_markup=await exit_to_menu_keyboard())
        #вариант событий когда в ссылке был адрес прям листа
        down_data=RequestToGoogle(user_url.url_with_gid,httpsession,sheet_id=None)#для запроса на скачивание нужен url с адресом листа
        # ModifyUrl нам его возвращает уже готовой ссылкой на скачивание
        res = await down_data.get_cvs()#загрузка cvs
        if res is None:#проверка что скачивание удалось
            return await message.bot.edit_message_text(chat_id=message.chat.id,message_id=id_msg,
                                                       text="Ошибка запроса на скачивание данных с гугл таблицы, проверь открыт ли доступ к ней",
                                            reply_markup=await exit_to_menu_keyboard())
        data=ReadCVSToObject(res,month)#мой класс для чтения cvs в список объектов пидантик
        if data.errors:#атрибут ошибки в истину встает когда что-то пошло не так
            return await message.bot.edit_message_text(chat_id=message.chat.id,message_id=id_msg,
                                                       text="Ошибка парсинга гугл таблицы, проверь ее структуру и название столбцов",
                                        reply_markup=await exit_to_menu_keyboard())
        if not await create_schedule_from_list(session,data.list_object,message.from_user.id):
            #круд операция на запись объектов в бд, из объекта класса чтения cvs ,берем атрибут .list_object там список объектов
            #и месяц выбранный пользователем на инлайн клавиатуре
            #если запись удачна круд оперция вернет истина, ниже обрабатываем ложь
            return await message.bot.edit_message_text(chat_id=message.chat.id,message_id=id_msg,
                                                       text="Ошибка записи в БД, проверь возможно уже есть график на этот месяц",
                                        reply_markup=await exit_to_menu_keyboard())
        print(f"{datetime.now()} Хэндлер парсинга графика ппр, данные добавлены")
        return await message.bot.edit_message_text(chat_id=message.chat.id,message_id=id_msg,
                                                   text="Данные добавлены", reply_markup=await exit_to_menu_keyboard())

@router.callback_query(ParsingState.waiting_gid)#в создании клавиатуры выставляем стадию ожидания листа гугл таблицы здесь ловим эту стадию
async def enter_gid(callback:CallbackQuery, session:AsyncSession, state:FSMContext):
    print(f"{datetime.now()} Хэндлер парсинга графика ппр, получен список листов гугл таблицы и выбран пользователем")
    data = await state.get_data()
    month=data.get("date")
    gid_list=data.get("gid_list")
    url=data.get("url")
    gid_user_index=callback.data#в колбэке приходит индекс выбранного листа из списка листов
    user_url=ModifyUrl(url)#снова создаем объект с введеным пользователем адресом
    user_url.create_url_with_gid(gid_list[int(gid_user_index)]['gid'])
    # вызываем метод ручного создания ссылку на таблицу с конретным листом обрщаемся к списку листов выбранным пользователем индексом
    # await callback.message.delete()
    async with aiohttp.ClientSession() as httpsession:
        request = RequestToGoogle(url_user=user_url.url_with_gid,session_obj=httpsession,sheet_id=None)
        # аналогичное скачивание с готовой ссылкой на cvs
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
        print(f"{datetime.now()} Хэндлер парсинга графика ппр, данные добавлены")
        return await callback.message.edit_text("Данные добавлены", reply_markup=await exit_to_menu_keyboard())



