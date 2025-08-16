"""
Клавиатуры для процесса регистрации
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_user_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа пользователя"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 Физическое лицо", callback_data="register_individual"),
            InlineKeyboardButton(text="🏢 Юридическое лицо", callback_data="register_legal")
        ]
    ])
    return keyboard

def get_registration_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения регистрации"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_registration"),
            InlineKeyboardButton(text="✏️ Изменить", callback_data="edit_registration")
        ],
        [
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_registration")
        ]
    ])
    return keyboard

def get_phone_request_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для запроса телефона"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📱 Поделиться номером", callback_data="share_phone")
        ],
        [
            InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="enter_phone_manually")
        ]
    ])
    return keyboard
