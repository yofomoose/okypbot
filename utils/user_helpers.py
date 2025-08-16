"""
Утилиты для работы с пользователями
"""
from database.models import db

def check_user_exists_by_phone(phone: str) -> bool:
    """Проверить, существует ли пользователь с данным телефоном"""
    all_users = db.get_all_users()
    for user in all_users:
        if user.phone == phone:
            return True
    return False

def get_user_by_phone(phone: str):
    """Получить пользователя по номеру телефона"""
    all_users = db.get_all_users()
    for user in all_users:
        if user.phone == phone:
            return user
    return None

def format_user_info(user) -> str:
    """Форматировать информацию о пользователе для отображения"""
    info = (
        f"👤 **Информация о пользователе**\n\n"
        f"📛 ФИО: {user.full_name}\n"
        f"📱 Телефон: {user.phone}\n"
        f"👔 Тип: {'🏢 Юридическое лицо' if user.user_type == 'legal' else '👤 Физическое лицо'}\n"
    )
    
    if user.user_type == "legal":
        info += (
            f"🏢 Должность: {user.position or 'Не указана'}\n"
            f"🏛️ ИНН компании: {user.company_inn or 'Не указан'}\n"
        )
    
    info += (
        f"📅 Дата регистрации: {user.registration_date[:10] if user.registration_date else 'Неизвестно'}\n"
        f"✅ Статус: {'Зарегистрирован' if user.is_registered else 'Не завершена регистрация'}\n"
    )
    
    if user.okdesk_contact_id:
        info += f"🆔 Okdesk Contact ID: {user.okdesk_contact_id}\n"
    
    if user.okdesk_company_id:
        info += f"🏢 Okdesk Company ID: {user.okdesk_company_id}\n"
    
    return info
