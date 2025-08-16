"""
Основные клавиатуры для телеграмм бота
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu() -> InlineKeyboardMarkup:
    """Главное меню бота"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Мои заявки", callback_data="issues"),
            InlineKeyboardButton(text="➕ Создать заявку", callback_data="create_issue")
        ],
        [
            InlineKeyboardButton(text="👥 Контакты", callback_data="contacts")
        ]
    ])
    return keyboard

def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой возврата в меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔙 Назад в меню", callback_data="menu")
        ]
    ])
    return keyboard

def get_issue_actions_keyboard(issue_id: int) -> InlineKeyboardMarkup:
    """Клавиатура действий с заявкой"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 Комментарий", callback_data=f"add_comment_{issue_id}"),
            InlineKeyboardButton(text="🔄 Статус", callback_data=f"change_status_{issue_id}")
        ],
        [
            InlineKeyboardButton(text="👤 Ответственный", callback_data=f"assign_{issue_id}"),
            InlineKeyboardButton(text="ℹ️ Подробно", callback_data=f"details_{issue_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="issues")
        ]
    ])
    return keyboard

def get_issue_statuses_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора статуса заявки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🆕 Новая", callback_data="status_new"),
            InlineKeyboardButton(text="🔄 В работе", callback_data="status_in_progress")
        ],
        [
            InlineKeyboardButton(text="⏸️ Приостановлена", callback_data="status_paused"),
            InlineKeyboardButton(text="✅ Решена", callback_data="status_resolved")
        ],
        [
            InlineKeyboardButton(text="❌ Закрыта", callback_data="status_closed"),
            InlineKeyboardButton(text="🔙 Назад", callback_data="back")
        ]
    ])
    return keyboard

def get_search_menu() -> InlineKeyboardMarkup:
    """Меню поиска"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 Заявки", callback_data="search_issues"),
            InlineKeyboardButton(text="🔍 Компании", callback_data="search_companies")
        ],
        [
            InlineKeyboardButton(text="🔍 Контакты", callback_data="search_contacts"),
            InlineKeyboardButton(text="🔍 Оборудование", callback_data="search_equipment")
        ],
        [
            InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
        ]
    ])
    return keyboard

def get_pagination_keyboard(page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
    """Клавиатура пагинации"""
    buttons = []
    
    # Предыдущая страница
    if page > 1:
        buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"{prefix}_page_{page-1}"))
    
    # Текущая страница
    buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="current_page"))
    
    # Следующая страница
    if page < total_pages:
        buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"{prefix}_page_{page+1}"))
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        buttons,
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ])
    return keyboard

def get_yes_no_keyboard(action: str, item_id: int = None) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия"""
    callback_yes = f"confirm_{action}"
    callback_no = f"cancel_{action}"
    
    if item_id:
        callback_yes += f"_{item_id}"
        callback_no += f"_{item_id}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=callback_yes),
            InlineKeyboardButton(text="❌ Нет", callback_data=callback_no)
        ]
    ])
    return keyboard
