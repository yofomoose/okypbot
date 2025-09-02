"""
Клавиатуры для специалистов
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_specialist_reply_keyboard(issue_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для ответа специалиста на заявку"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💬 Ответить клиенту",
                callback_data=f"reply_to_issue:{issue_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="📋 Открыть заявку",
                url=f"https://your-company.okdesk.ru/issues/{issue_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="✅ Закрыть заявку",
                callback_data=f"close_issue:{issue_id}"
            ),
            InlineKeyboardButton(
                text="🔄 Обновить статус",
                callback_data=f"update_status:{issue_id}"
            )
        ]
    ])

def get_specialist_dashboard() -> InlineKeyboardMarkup:
    """Главное меню специалиста"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔔 Новые заявки", callback_data="new_issues"),
            InlineKeyboardButton(text="📋 Мои заявки", callback_data="my_issues")
        ],
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="stats"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")
        ]
    ])

def get_issue_status_keyboard(issue_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для изменения статуса заявки"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🆕 Новая", 
                callback_data=f"set_status_{issue_id}_new"
            ),
            InlineKeyboardButton(
                text="⚙️ В работе", 
                callback_data=f"set_status_{issue_id}_in_progress"
            )
        ],
        [
            InlineKeyboardButton(
                text="⏳ Ожидание", 
                callback_data=f"set_status_{issue_id}_waiting"
            ),
            InlineKeyboardButton(
                text="✅ Решена", 
                callback_data=f"set_status_{issue_id}_resolved"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔒 Закрыть", 
                callback_data=f"set_status_{issue_id}_closed"
            ),
            InlineKeyboardButton(
                text="🔙 Назад", 
                callback_data=f"issue_details_{issue_id}"
            )
        ]
    ])
