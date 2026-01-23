from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types


async def registration_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Зарегистрироватся", callback_data='registration'))
    return builder.as_markup()

async def main_menu():
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text='Добавить график', callback_data='parsing'))
    builder.add(types.InlineKeyboardButton(text='Удалить график',callback_data='delete_schudele'))
    builder.add(types.InlineKeyboardButton(text="Просмотреть график", callback_data="view_schudele"))
    builder.adjust(1)
    return builder.as_markup()