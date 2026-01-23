from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types
from utils import get_4_month, MonthSchedule


async def registration_keyboard():
    """Кнопка регистрации"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Зарегистрироватся", callback_data='registration'))
    return builder.as_markup()

async def main_menu():
    """Набор кнопок главного меню"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text='Добавить график', callback_data='parsing'))
    builder.add(types.InlineKeyboardButton(text='Удалить график',callback_data='delete_schudele'))
    builder.add(types.InlineKeyboardButton(text="Просмотреть график", callback_data="view_schudele"))
    builder.adjust(1)
    return builder.as_markup()

