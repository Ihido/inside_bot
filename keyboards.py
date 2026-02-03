from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📸 Отправить фото")],
            [KeyboardButton(text="🎥 Отправить видео")],
            [KeyboardButton(text="📝 Отправить текст")],
            [KeyboardButton(text="📊 Мои отправки")],
            [KeyboardButton(text="ℹ️ О проекте")]
        ],
        resize_keyboard=True
    )

def get_confirmation_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да, отправить"), KeyboardButton(text="❌ Нет, отменить")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🚫 Отменить отправку")]],
        resize_keyboard=True
    )