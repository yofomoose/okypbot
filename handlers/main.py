"""
Главные обработчики команд телеграмм бота
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from database.models import db
from keyboards.main import get_main_menu, get_issue_actions_keyboard, get_back_to_menu_keyboard, get_user_role
from keyboards.registration import get_user_type_keyboard
from api.okdesk_api import OkdeskAPI
from states.registration import IssueStates, RegistrationStates
from services.issue_monitor import get_monitor
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

router = Router()

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь админом"""
    return user_id in ADMIN_IDS

def check_registration(func):
    """Декоратор для проверки регистрации пользователя (админы пропускаются)"""
    async def wrapper(event, *args, **kwargs):
        user_id = event.from_user.id
        
        # Админы проходят без проверки регистрации
        if is_admin(user_id):
            return await func(event, *args, **kwargs)
        
        if not db.is_user_registered(user_id):
            if isinstance(event, Message):
                await event.answer(
                    "🔐 Для работы с ботом необходимо пройти регистрацию!\n\n"
                    "Используйте команду /register",
                    reply_markup=get_user_type_keyboard()
                )
            elif isinstance(event, CallbackQuery):
                await event.answer("Необходима регистрация!", show_alert=True)
            return
        return await func(event, *args, **kwargs)
    return wrapper

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    
    # Админы проходят сразу в главное меню
    if is_admin(user_id):
        user_role = get_user_role(user_id)
        await message.answer(
            f"🔧 Добро пожаловать, администратор!\n\n"
            f"👤 Ваш ID: {user_id}\n"
            f"🤖 У вас есть доступ к функциям управления ML системой.\n\n"
            "Выберите действие:",
            reply_markup=get_main_menu(user_role)
        )
        return
    
    if not db.is_user_registered(user_id):
        await message.answer(
            "🏢 Добро пожаловать в бот Okdesk CRM!\n\n"
            "Я помогу вам работать с заявками и клиентами в системе Okdesk.\n\n"
            "🔐 Для начала работы необходимо пройти регистрацию:",
            reply_markup=get_user_type_keyboard()
        )
        # Устанавливаем состояние ожидания выбора типа пользователя
        await state.set_state(RegistrationStates.waiting_for_user_type)
        return
    
    user = db.get_user(user_id)
    user_role = get_user_role(user_id)
    await message.answer(
        f"🏢 Добро пожаловать, {user.full_name}!\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu(user_role)
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    user_id = message.from_user.id
    
    help_text = """
🔹 /start - Главное меню
🔹 /help - Справка
🔹 /register - Регистрация в системе
🔹 /profile - Ваш профиль
🔹 /issues - Мои заявки
🔹 /create_issue - Создать заявку
🔹 /companies - Компании
🔹 /contacts - Контакты

📋 Функции бота:
• Просмотр и управление заявками
• Создание новых заявок
• Поиск компаний и контактов
• Обновление статусов заявок
• Добавление комментариев
    """
    
    # Добавляем админские команды для админов
    if is_admin(user_id):
        help_text += """
        
🔧 Команды администратора:
🔹 /admin - Панель администратора
🔹 /stats - Статистика ML классификации
        """
    
    await message.answer(help_text)

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Панель администратора"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    admin_text = f"""
🔧 <b>Панель администратора</b>

👤 Ваш ID: <code>{user_id}</code>
✅ Права администратора подтверждены

📊 Доступные функции:
• Получение уведомлений о классификации заявок
• Подтверждение правильности ML классификации  
• Исправление неправильной классификации
• Обучение модели на основе обратной связи
• Обновление категорий заявок в CRM

🤖 Команды для управления ML:
• /bot_model - Информация о bot_model
• /test_bot_model - Тестирование bot_model
• /ml_admin - Панель управления ML

ℹ️ Уведомления приходят автоматически при создании заявок.
    """
    
    # Создаем кнопки для быстрого доступа
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🤖 bot_model", callback_data="bot_model_info"),
            InlineKeyboardButton(text="📊 ML Статистика", callback_data="ml_stats")
        ],
        [
            InlineKeyboardButton(text="🎛️ Управление ML", callback_data="ml_admin_panel")
        ]
    ])
    
    await message.answer(admin_text, parse_mode="HTML", reply_markup=keyboard)

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Статистика ML классификации для админов"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    try:
        from services.ml_stats_service import MLStatsService
        ml_stats = MLStatsService()
        
        stats = await ml_stats.get_classification_stats()
        
        if stats:
            stats_text = f"""
📊 <b>Статистика ML классификации</b>

📈 Общие показатели:
• Всего классификаций: {stats.get('total_classifications', 0)}
• Правильных: {stats.get('correct_classifications', 0)}
• Неправильных: {stats.get('incorrect_classifications', 0)}
• Точность: {stats.get('accuracy', 0):.1%}

🤖 Обратная связь:
• Подтверждений админов: {stats.get('admin_confirmations', 0)}
• Исправлений: {stats.get('admin_corrections', 0)}
• Пользовательская обратная связь: {stats.get('user_feedback', 0)}

📅 За последние 24 часа:
• Новых классификаций: {stats.get('recent_classifications', 0)}
• Средняя уверенность: {stats.get('avg_confidence', 0):.1%}
            """
        else:
            stats_text = "📊 Статистика пока не доступна"
            
        await message.answer(stats_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        await message.answer("❌ Ошибка получения статистики")

@router.message(Command("profile"))
@check_registration
async def cmd_profile(message: Message, **kwargs):
    """Показать профиль пользователя"""
    user = db.get_user(message.from_user.id)
    
    profile_text = (
        f"👤 **Ваш профиль**\n\n"
        f"📛 ФИО: {user.full_name}\n"
        f"📱 Телефон: {user.phone}\n"
        f"👔 Тип: {'🏢 Юридическое лицо' if user.user_type == 'legal' else '👤 Физическое лицо'}\n"
    )
    
    if user.user_type == "legal":
        profile_text += (
            f"🏢 Должность: {user.position or 'Не указана'}\n"
            f"🏛️ ИНН компании: {user.company_inn or 'Не указан'}\n"
        )
    
    profile_text += (
        f"📅 Дата регистрации: {user.registration_date[:10] if user.registration_date else 'Неизвестно'}\n"
        f"🆔 Okdesk Contact ID: {user.okdesk_contact_id or 'Не создан'}\n"
    )
    
    if user.okdesk_company_id:
        profile_text += f"🏢 Okdesk Company ID: {user.okdesk_company_id}\n"
    
    await message.answer(profile_text)

@router.callback_query(F.data == "menu")
async def show_main_menu(callback: CallbackQuery):
    """Показать главное меню"""
    await callback.answer()
    user_role = get_user_role(callback.from_user.id)
    await callback.message.edit_text(
        "🏠 **Главное меню**\n\nВыберите действие:",
        reply_markup=get_main_menu(user_role)
    )

@router.callback_query(F.data == "issues")
@check_registration
async def show_issues(callback: CallbackQuery, **kwargs):
    """Показать список заявок"""
    await callback.answer()
    
    # Здесь будет логика получения заявок из Okdesk API
    okdesk = OkdeskAPI()
    try:
        issues = await okdesk.get_issues()
        
        if not issues:
            await callback.message.edit_text(
                "📋 У вас нет активных заявок",
                reply_markup=get_back_to_menu_keyboard()
            )
            return
            
        text = "📋 Ваши заявки:\n\n"
        for issue in issues[:10]:  # Показываем первые 10
            text += f"#{issue.get('id')} - {issue.get('title', 'Без названия')}\n"
            text += f"Статус: {issue.get('status', 'Неизвестно')}\n\n"
            
        await callback.message.edit_text(text, reply_markup=get_back_to_menu_keyboard())
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при получении заявок: {str(e)}",
            reply_markup=get_back_to_menu_keyboard()
        )
    finally:
        await okdesk.close()

@router.callback_query(F.data == "create_issue")
@check_registration
async def handle_create_issue_button(callback: CallbackQuery, state: FSMContext, **kwargs):
    """Обработчик кнопки создания заявки с ML классификацией"""
    await callback.answer()
    
    # Импортируем обработчик из issue_handlers
    try:
        from handlers.issue_handlers import start_issue_creation
        await start_issue_creation(callback.message, state)
    except ImportError:
        # Fallback к старой логике если issue_handlers недоступен
        await callback.message.edit_text("📝 Введите название заявки:")
        await state.set_state(IssueStates.waiting_for_title)

@router.message(IssueStates.waiting_for_title)
async def process_issue_title(message: Message, state: FSMContext):
    """Обработка названия заявки"""
    await state.update_data(title=message.text)
    await message.answer("📝 Теперь введите описание заявки:")
    await state.set_state(IssueStates.waiting_for_description)

@router.message(IssueStates.waiting_for_description)
async def process_issue_description(message: Message, state: FSMContext):
    """Создание заявки с ML классификацией"""
    await state.update_data(description=message.text)
    data = await state.get_data()
    
    # Показываем процесс обработки
    processing_msg = await message.answer("🤖 Анализирую заявку и создаю...")
    
    # ML классификация - используем напрямую TextClassifier
    try:
        from ml.classifier import TextClassifier
        
        # Создаем классификатор
        classifier = TextClassifier()
        
        # Классифицируем заявку
        full_text = f"{data['title']} {data['description']}"
        ml_category, ml_confidence = await classifier.classify(full_text)
        
        logger.info(f"ML классификация: {ml_category} (уверенность: {ml_confidence:.2f})")
        
    except ImportError:
        logger.info("ML модуль недоступен, пропускаем классификацию")
        ml_category = None
        ml_confidence = 0.0
    except Exception as e:
        logger.error(f"Ошибка ML классификации: {e}")
        ml_category = None
        ml_confidence = 0.0
    
    async with OkdeskAPI() as okdesk:
        try:
            # Добавляем информацию о пользователе в описание
            description = data['description']
            description += f"\n\n---\nСоздано через Telegram бот"
            description += f"\nПользователь ID: {message.from_user.id}"
            if message.from_user.username:
                description += f"\nUsername: @{message.from_user.username}"
            
            # Добавляем ML информацию если доступна
            # Добавляем ML результаты в описание
            if ml_category:
                description += f"\n\n🤖 ML Классификация: {ml_category}"
                if ml_confidence > 0:
                    description += f" (уверенность: {ml_confidence:.2f})"
            
            # Получаем информацию о зарегистрированном пользователе
            user = db.get_user(message.from_user.id)
            
            # Подготавливаем параметры для создания заявки
            issue_params = {}
            if user and user.okdesk_contact_id:
                issue_params['contact_id'] = user.okdesk_contact_id
                logger.info(f"Привязываем заявку к контакту ID: {user.okdesk_contact_id}")
            
            issue = await okdesk.create_issue(
                title=data['title'],
                description=description,
                **issue_params
            )
            
            logger.info(f"Заявка создана: {issue}")
            
            # Попробуем получить созданную заявку, чтобы проверить привязку
            try:
                created_issue = await okdesk.get_issue(issue.get('id'))
                logger.info(f"Данные созданной заявки: contact_id={created_issue.get('contact_id')}, contact_name={created_issue.get('contact', {}).get('name') if created_issue.get('contact') else 'None'}")
            except Exception as e:
                logger.error(f"Ошибка при получении данных заявки: {e}")
            
            # Добавляем заявку в мониторинг изменений статуса
            monitor = get_monitor()
            if monitor and issue.get('id'):
                status_name = issue.get('status', {}).get('name', 'Новая') if isinstance(issue.get('status'), dict) else issue.get('status', 'Новая')
                monitor.add_issue_to_tracking(
                    issue_id=issue.get('id'),
                    user_id=message.from_user.id,
                    initial_status=status_name
                )
            
            # Формируем сообщение с результатом
            success_message = (
                f"✅ Заявка создана!\n\n"
                f"Номер: #{issue.get('id')}\n"
                f"Название: {issue.get('title', 'Без названия')}\n"
                f"Статус: {issue.get('status', {}).get('name', 'Новая') if isinstance(issue.get('status'), dict) else issue.get('status', 'Новая')}\n"
                f"Описание: {data['description'][:100]}{'...' if len(data['description']) > 100 else ''}\n"
            )
            
            # Добавляем ML информацию в ответ
            if ml_category and ml_confidence > 0.3:
                success_message += f"\n🤖 Категория: {ml_category}"
                if ml_confidence >= 0.8:
                    success_message += " ✅"
                elif ml_confidence >= 0.6:
                    success_message += " ⚠️"
                else:
                    success_message += " ❓"
            
            # Добавляем информацию о привязке к контакту
            if user and user.okdesk_contact_id:
                success_message += f"\n👤 Привязана к контакту: ID {user.okdesk_contact_id}\n"
            
            success_message += "\n🔔 Вы будете получать уведомления об изменении статуса заявки"
                
            await processing_msg.edit_text(success_message)
            
        except Exception as e:
            await processing_msg.edit_text(f"❌ Ошибка при создании заявки: {str(e)}")
    
    await state.clear()

@router.callback_query(F.data == "companies")
@check_registration
async def show_companies(callback: CallbackQuery, **kwargs):
    """Показать список компаний"""
    await callback.answer()
    
    okdesk = OkdeskAPI()
    try:
        companies = await okdesk.get_companies()
        
        if not companies:
            await callback.message.edit_text("🏢 Компании не найдены")
            return
            
        text = "🏢 Компании:\n\n"
        for company in companies[:10]:
            text += f"• {company.get('name', 'Без названия')}\n"
            
        await callback.message.edit_text(text)
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка при получении компаний: {str(e)}")
    finally:
        await okdesk.close()

@router.callback_query(F.data == "contacts")
@check_registration
async def show_contacts(callback: CallbackQuery, **kwargs):
    """Показать список контактов"""
    await callback.answer()
    
    okdesk = OkdeskAPI()
    try:
        contacts = await okdesk.get_contacts()
        
        if not contacts:
            await callback.message.edit_text("👥 Контакты не найдены")
            return
            
        text = "👥 Контакты:\n\n"
        for contact in contacts[:10]:
            name = contact.get('name', 'Без имени')
            email = contact.get('email', '')
            text += f"• {name}"
            if email:
                text += f" ({email})"
            text += "\n"
            
        await callback.message.edit_text(text)
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка при получении контактов: {str(e)}")
    finally:
        await okdesk.close()

@router.callback_query(F.data == "ml_classify")
@check_registration
async def start_ml_classification(callback: CallbackQuery, state: FSMContext, **kwargs):
    """Запуск ML классификации"""
    await callback.answer()
    
    try:
        from services.ml_service import ml_service
        
        # Проверяем статус ML сервиса
        stats = ml_service.get_statistics()
        service_status = stats.get('service_status', 'inactive')
        
        if service_status != 'active':
            await callback.message.edit_text(
                "🤖 <b>ML Классификатор</b>\n\n"
                "⚠️ Сервис машинного обучения недоступен.\n"
                "Возможные причины:\n"
                "• Не установлены ML библиотеки\n"
                "• Ошибка инициализации модели\n\n"
                "Обратитесь к администратору.",
                parse_mode="HTML",
                reply_markup=get_back_to_menu_keyboard()
            )
            return
        
        # Показываем информацию о классификаторе
        classifier_info = stats.get('classifier', {})
        categories_count = classifier_info.get('categories_count', 0)
        is_trained = classifier_info.get('is_trained', False)
        
        response = (
            "🤖 <b>ML Классификатор заявок</b>\n\n"
            f"📊 Статус: {'🟢 Активен' if is_trained else '🔴 Не обучен'}\n"
            f"📋 Категорий: {categories_count}\n\n"
            "💡 Отправьте текст заявки, и я определю её категорию с указанием уверенности.\n\n"
            "<i>Это поможет правильно классифицировать заявку перед отправкой в Okdesk.</i>"
        )
        
        await callback.message.edit_text(
            response,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📝 Классифицировать текст", 
                        callback_data="start_classification"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 Статистика ML", 
                        callback_data="ml_stats"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🏠 В меню", 
                        callback_data="menu"
                    )
                ]
            ])
        )
        
    except ImportError:
        await callback.message.edit_text(
            "🤖 <b>ML Классификатор</b>\n\n"
            "❌ ML модуль не установлен.\n"
            "Для использования классификатора установите зависимости:\n"
            "<code>pip install scikit-learn numpy joblib</code>",
            parse_mode="HTML",
            reply_markup=get_back_to_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка запуска ML классификации: {e}")
        await callback.message.edit_text(
            "❌ Ошибка запуска классификатора",
            reply_markup=get_back_to_menu_keyboard()
        )

@router.callback_query(F.data == "start_classification")
async def redirect_to_classification(callback: CallbackQuery, state: FSMContext):
    """Перенаправление на классификацию"""
    await callback.answer()
    
    # Импортируем и вызываем обработчик из ml_handlers
    try:
        from handlers.ml_handlers import cmd_classify
        # Создаем фейковое сообщение для вызова команды
        fake_message = type('obj', (object,), {
            'answer': callback.message.edit_text,
            'from_user': callback.from_user
        })()
        
        await cmd_classify(fake_message, state)
    except Exception as e:
        logger.error(f"Ошибка перенаправления на классификацию: {e}")
        await callback.message.edit_text(
            "❌ Ошибка запуска классификации",
            reply_markup=get_back_to_menu_keyboard()
        )

@router.callback_query(F.data == "quick_issue_info") 
async def handle_quick_issue_info(callback: CallbackQuery):
    """Показывает информацию о быстром создании заявки"""
    await callback.answer()
    
    info_text = (
        "⚡ <b>Быстрое создание заявки</b>\n\n"
        "Используйте команду:\n"
        "<code>/quick_issue Описание проблемы</code>\n\n"
        "Примеры:\n"
        "• <code>/quick_issue Принтер не печатает документы</code>\n"
        "• <code>/quick_issue Компьютер завис, нужна помощь</code>\n"
        "• <code>/quick_issue Проблемы с интернетом в офисе</code>\n\n"
        "🤖 Заявка будет автоматически классифицирована с помощью ИИ!"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎫 Создать заявку (подробно)", callback_data="create_issue")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="menu")]
    ])
    
    await callback.message.edit_text(
        info_text,
        parse_mode="HTML", 
        reply_markup=keyboard
    )

# Добавляем команду быстрого создания заявки
@router.message(Command("quick_issue"))
@check_registration
async def cmd_quick_issue(message: Message, **kwargs):
    """Быстрое создание заявки через команду"""
    # Импортируем обработчик из issue_handlers
    try:
        from handlers.issue_handlers import cmd_quick_issue as quick_issue_handler
        await quick_issue_handler(message)
    except ImportError:
        await message.answer(
            "❌ Модуль создания заявок недоступен.\n"
            "Используйте /create_issue для создания заявки через меню."
        )
