from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types
from utils import get_4_month, MonthSchedule

async def get_date_schedule():
    """Клавиатура с динамичекими кнопками заполняющаяся из списка месяцев"""
    builder = InlineKeyboardBuilder()
    list_month=get_4_month()
    for month in list_month:
        builder.add(types.InlineKeyboardButton(text=month, callback_data=MonthSchedule(month=month).pack()))
    builder.add(types.InlineKeyboardButton(text="Назад в меню",callback_data="main_menu"))
    builder.adjust(2)
    return builder.as_markup()

async def cancel_keyboard():
    """Клавиатура с кнопкой отмена, вызывающая главное меню"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Отмена", callback_data="main_menu"))
    return builder.as_markup()

async def exit_to_menu_keyboard():
    """Клавиатура с кнопкой выйти в меню, вызывающая главное меню"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Выйти в главное меню", callback_data="main_menu"))
    return builder.as_markup()