from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types

from utils import get_3_days


async def registration_keyboard():
    """Кнопка регистрации"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Зарегистрироватся", callback_data='registration'))
    return builder.as_markup()

async def main_menu():
    """Набор кнопок главного меню"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text='Добавить график', callback_data='parsing'))
    builder.add(types.InlineKeyboardButton(text='Удалить график',callback_data='delete_schedule'))
    builder.add(types.InlineKeyboardButton(text="Просмотреть график", callback_data="view_schedule"))
    builder.add(types.InlineKeyboardButton(text="Сбросить привязку чата для оповещений", callback_data="reset_chat_id"))
    builder.add(types.InlineKeyboardButton(text="Возможные для ППР дни", callback_data="get_days_ppr"))
    builder.adjust(1)
    return builder.as_markup()

async def month_user_keyboard(res):
    """Набор кнопок с месяцами которые есть в БД у юзера"""
    builder = InlineKeyboardBuilder()
    for month in res:
        builder.add(types.InlineKeyboardButton(text=month, callback_data=month))
    builder.add(types.InlineKeyboardButton(text="Выйти в главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

async def first_3_day_keyboard(month):
    builder = InlineKeyboardBuilder()
    list_days= await get_3_days(month)
    for day in list_days:
        builder.add(types.InlineKeyboardButton(text=day, callback_data=day))
    builder.add(types.InlineKeyboardButton(text="Выйти в главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()