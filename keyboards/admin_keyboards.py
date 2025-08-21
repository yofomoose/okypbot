"""
Клавиатуры для админских функций с улучшенной навигацией по категориям
"""
import logging
from typing import List, Dict, Optional
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

# Группы категорий для удобной навигации
CATEGORY_GROUPS = {
    "🖥️ Оргтехника": [
        "Оргтехника: Не печатает",
        "Оргтехника: Подключение", 
        "Оргтехника: Настройка",
        "Оргтехника: Ремонт",
        "Оргтехника: Замена картриджа"
    ],
    "💻 Компьютеры": [
        "Компьютеры: Не включается",
        "Компьютеры: Тормозит",
        "Компьютеры: BSOD",
        "Компьютеры: Вирусы",
        "Компьютеры: Настройка"
    ],
    "🌐 Сеть": [
        "Сеть: Нет интернета",
        "Сеть: Медленная скорость",
        "Сеть: Wi-Fi проблемы",
        "Сеть: Настройка роутера",
        "Сеть: VPN"
    ],
    "📱 Программы": [
        "ПО: Установка",
        "ПО: Ошибки",
        "ПО: Обновление",
        "ПО: Лицензии",
        "ПО: Настройка"
    ],
    "🔧 1C": [
        "1C: Ошибки базы",
        "1C: Обновление",
        "1C: Резервное копирование",
        "1C: Пользователи",
        "1C: Настройка"
    ],
    "💰 Отдел продаж": [
        "Отдел продаж: Закупка ПО",
        "Отдел продаж: Техника",
        "Отдел продаж: Консультация"
    ],
    "🏗️ Ремонт": [
        "Ремонт: Диагностика",
        "Ремонт: Оборудование у подрядчика Колорит",
        "Ремонт: Замена комплектующих"
    ],
    "❓ Прочее": [
        "Консультация",
        "Прочее",
        "Неопределенная категория"
    ]
}

# Короткие идентификаторы для групп (для callback_data)
GROUP_IDS = {
    "🖥️ Оргтехника": "tech",
    "💻 Компьютеры": "pc", 
    "🌐 Сеть": "net",
    "📱 Программы": "soft",
    "🔧 1C": "1c",
    "💰 Отдел продаж": "sales",
    "🏗️ Ремонт": "repair",
    "❓ Прочее": "other"
}

# Обратный словарь для поиска группы по ID
ID_TO_GROUP = {v: k for k, v in GROUP_IDS.items()}

def update_category_groups_from_ml(ml_service) -> None:
    """Обновляет группы категорий из ML сервиса"""
    global CATEGORY_GROUPS
    
    try:
        # Получаем категории из ML сервиса
        categories = ml_service.get_categories()
        if not categories:
            logger.warning("ML сервис не вернул категории")
            return
        
        # Очищаем старые группы (кроме базовых)
        new_groups = {}
        
        # Автоматически группируем категории по ключевым словам
        for category in categories:
            category_lower = category.lower()
            
            # Определяем группу по ключевым словам
            if any(word in category_lower for word in ['компьютер', 'пк', 'процессор', 'память', 'видеокарта']):
                group = "💻 Компьютеры"
            elif any(word in category_lower for word in ['принтер', 'печать', 'тонер', 'картридж']):
                group = "🖨️ Принтеры"
            elif any(word in category_lower for word in ['монитор', 'экран', 'дисплей']):
                group = "🖥️ Мониторы"
            elif any(word in category_lower for word in ['сеть', 'интернет', 'wi-fi', 'wifi', 'подключение']):
                group = "🌐 Сеть"
            elif any(word in category_lower for word in ['1с', '1c', 'программа', 'софт', 'лицензия']):
                group = "💾 Программы"
            elif any(word in category_lower for word in ['телефон', 'связь', 'звонок']):
                group = "📞 Связь"
            elif any(word in category_lower for word in ['ремонт', 'замена', 'установка']):
                group = "🔧 Ремонт и обслуживание"
            else:
                group = "📋 Прочее"
            
            if group not in new_groups:
                new_groups[group] = []
            new_groups[group].append(category)
        
        # Обновляем глобальную переменную
        CATEGORY_GROUPS.update(new_groups)
        
        # Также обновляем ID для новых групп
        for group_name in new_groups.keys():
            if group_name not in GROUP_IDS:
                # Создаем короткий ID из названия группы
                group_id = group_name.lower().replace(' ', '').replace('🔧', 'repair').replace('📋', 'other').replace('💻', 'pc').replace('🌐', 'net').replace('💾', 'soft').replace('📞', 'comm').replace('🖥️', 'tech').replace('📊', 'dept')[:8]
                GROUP_IDS[group_name] = group_id
                ID_TO_GROUP[group_id] = group_name
        
        total_categories = sum(len(cats) for cats in CATEGORY_GROUPS.values())
        logger.info(f"Обновлены группы категорий, добавлено {total_categories} категорий из LightGBM")
        
    except Exception as e:
        logger.error(f"Ошибка обновления категорий из ML сервиса: {e}")

def get_category_groups_keyboard(classification_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру с группами категорий"""
    keyboard = []
    
    # Добавляем кнопки групп категорий (по 2 в ряд)
    group_buttons = []
    for group_name in CATEGORY_GROUPS.keys():
        group_id = GROUP_IDS.get(group_name, "other")
        group_buttons.append(
            InlineKeyboardButton(
                text=group_name,
                callback_data=f"admin_group_{classification_id}_{group_id}"
            )
        )
        
        # Добавляем по 2 кнопки в ряд
        if len(group_buttons) == 2:
            keyboard.append(group_buttons)
            group_buttons = []
    
    # Добавляем оставшиеся кнопки
    if group_buttons:
        keyboard.append(group_buttons)
    
    # Добавляем кнопку "Назад"
    keyboard.append([
        InlineKeyboardButton(
            text="◀️ Назад", 
            callback_data=f"admin_back_{classification_id}"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_category_subcategories_keyboard(classification_id: int, group_id: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру с подкategoriями для выбранной группы"""
    keyboard = []
    
    # Находим полное название группы по ID
    full_group_name = ID_TO_GROUP.get(group_id)
    
    if not full_group_name or full_group_name not in CATEGORY_GROUPS:
        # Если группа не найдена, возвращаем кнопку "Назад"
        return InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="◀️ Назад к группам", 
                callback_data=f"admin_groups_{classification_id}"
            )
        ]])
    
    # Добавляем кнопки подкategorий
    subcategories = CATEGORY_GROUPS[full_group_name]
    for i, subcategory in enumerate(subcategories):
        # Создаем короткий ID для категории (группа + индекс)
        category_id = f"{group_id}_{i}"
        keyboard.append([
            InlineKeyboardButton(
                text=f"✅ {subcategory}",
                callback_data=f"admin_cat_{classification_id}_{category_id}"
            )
        ])
    
    # Добавляем кнопку "Назад к группам"
    keyboard.append([
        InlineKeyboardButton(
            text="◀️ Назад к группам", 
            callback_data=f"admin_groups_{classification_id}"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_category_by_id(category_id: str) -> str:
    """Получает полное название категории по короткому ID"""
    try:
        parts = category_id.split('_')
        if len(parts) >= 2:
            group_id = parts[0]
            cat_index = int(parts[1])
            
            group_name = ID_TO_GROUP.get(group_id)
            if group_name and group_name in CATEGORY_GROUPS:
                subcategories = CATEGORY_GROUPS[group_name]
                if 0 <= cat_index < len(subcategories):
                    return subcategories[cat_index]
    except (ValueError, IndexError):
        pass
    
    return "Неопределенная категория"

def get_ml_feedback_keyboard(classification_id: int) -> InlineKeyboardMarkup:
    """Создает начальную клавиатуру для отзыва о ML классификации"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Правильно", 
                callback_data=f"admin_correct_{classification_id}"
            ),
            InlineKeyboardButton(
                text="❌ Неправильно", 
                callback_data=f"admin_incorrect_{classification_id}"
            )
        ]
    ])

def merge_categories_with_lgb(lgb_categories: List[str]) -> Dict[str, List[str]]:
    """Объединяет предопределенные группы с категориями из LightGBM модели"""
    merged_groups = CATEGORY_GROUPS.copy()
    
    # Создаем множество всех существующих категорий
    existing_categories = set()
    for categories in merged_groups.values():
        existing_categories.update(categories)
    
    # Добавляем новые категории из LightGBM в соответствующие группы
    for category in lgb_categories:
        if category in existing_categories:
            continue
            
        # Пытаемся определить группу по ключевым словам
        category_lower = category.lower()
        added = False
        
        # Логика автоматического распределения по группам
        if any(word in category_lower for word in ['принтер', 'печать', 'картридж', 'сканер']):
            merged_groups["🖥️ Оргтехника"].append(category)
            added = True
        elif any(word in category_lower for word in ['компьютер', 'пк', 'ноутбук', 'bsod', 'биос']):
            merged_groups["💻 Компьютеры"].append(category)
            added = True
        elif any(word in category_lower for word in ['сеть', 'интернет', 'wi-fi', 'wifi', 'роутер']):
            merged_groups["🌐 Сеть"].append(category)
            added = True
        elif any(word in category_lower for word in ['программ', 'софт', 'приложен', 'по:']):
            merged_groups["📱 Программы"].append(category)
            added = True
        elif any(word in category_lower for word in ['1c', '1с', 'база']):
            merged_groups["🔧 1C"].append(category)
            added = True
        elif any(word in category_lower for word in ['продаж', 'закупк']):
            merged_groups["💰 Отдел продаж"].append(category)
            added = True
        elif any(word in category_lower for word in ['ремонт', 'диагност', 'подрядчик']):
            merged_groups["🏗️ Ремонт"].append(category)
            added = True
        
        # Если не удалось автоматически определить группу, добавляем в "Прочее"
        if not added:
            merged_groups["❓ Прочее"].append(category)
    
    return merged_groups

def update_category_groups_from_ml(ml_service) -> None:
    """Обновляет группы категорий на основе данных из ML сервиса"""
    try:
        if hasattr(ml_service, 'get_categories'):
            lgb_categories = ml_service.get_categories()
            if lgb_categories:
                global CATEGORY_GROUPS
                CATEGORY_GROUPS = merge_categories_with_lgb(lgb_categories)
                logger.info(f"Обновлены группы категорий, добавлено {len(lgb_categories)} категорий из LightGBM")
    except Exception as e:
        logger.error(f"Ошибка обновления групп категорий: {e}")

def get_admin_ml_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для управления ML моделями"""
    buttons = [
        [
            InlineKeyboardButton(text="🤖 bot_model инфо", callback_data="bot_model_info"),
            InlineKeyboardButton(text="🧪 Тест bot_model", callback_data="test_bot_model")
        ],
        [
            InlineKeyboardButton(text="🔄 Сравнить модели", callback_data="model_comparison"),
            InlineKeyboardButton(text="⚡ LightGBM инфо", callback_data="lightgbm_info")
        ],
        [
            InlineKeyboardButton(text="🎛️ Переключить bot_model", callback_data="toggle_bot_model"),
            InlineKeyboardButton(text="📊 Статистика ML", callback_data="ml_stats")
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_model_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора активной модели"""
    buttons = [
        [
            InlineKeyboardButton(text="🤖 bot_model", callback_data="select_bot_model"),
            InlineKeyboardButton(text="⚡ LightGBM", callback_data="select_lightgbm")
        ],
        [
            InlineKeyboardButton(text="🔧 KNN (базовая)", callback_data="select_knn"),
            InlineKeyboardButton(text="🔄 Авто выбор", callback_data="select_auto")
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="admin_ml_back")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
