"""
Главные обработчики команд телеграмм бота
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.models import db
from keyboards.main import get_main_menu, get_issue_actions_keyboard, get_back_to_menu_keyboard
from keyboards.registration import get_user_type_keyboard
from api.okdesk_api import OkdeskAPI
from states.registration import IssueStates, RegistrationStates
from services.issue_monitor import get_monitor

logger = logging.getLogger(__name__)

router = Router()

def check_registration(func):
    """Декоратор для проверки регистрации пользователя"""
    async def wrapper(event, *args, **kwargs):
        user_id = event.from_user.id
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
    await message.answer(
        f"🏢 Добро пожаловать, {user.full_name}!\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu()
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
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
    await message.answer(help_text)

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
    await callback.message.edit_text(
        "🏠 **Главное меню**\n\nВыберите действие:",
        reply_markup=get_main_menu()
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
async def start_create_issue(callback: CallbackQuery, state: FSMContext, **kwargs):
    """Начать создание заявки"""
    await callback.answer()
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
    """Создание заявки"""
    await state.update_data(description=message.text)
    data = await state.get_data()
    
    async with OkdeskAPI() as okdesk:
        try:
            # Добавляем информацию о пользователе в описание
            description = data['description']
            description += f"\n\n---\nСоздано через Telegram бот"
            description += f"\nПользователь ID: {message.from_user.id}"
            if message.from_user.username:
                description += f"\nUsername: @{message.from_user.username}"
            
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
                
            success_message = (
                f"✅ Заявка создана!\n\n"
                f"Номер: #{issue.get('id')}\n"
                f"Название: {issue.get('title', 'Без названия')}\n"
                f"Статус: {issue.get('status', {}).get('name', 'Новая') if isinstance(issue.get('status'), dict) else issue.get('status', 'Новая')}\n"
                f"Описание: {data['description'][:100]}{'...' if len(data['description']) > 100 else ''}\n"
            )
            
            # Добавляем информацию о привязке к контакту
            if user and user.okdesk_contact_id:
                success_message += f"\n👤 Привязана к контакту: ID {user.okdesk_contact_id}\n"
            
            success_message += "\n🔔 Вы будете получать уведомления об изменении статуса заявки"
                
            await message.answer(success_message)
            
        except Exception as e:
            await message.answer(f"❌ Ошибка при создании заявки: {str(e)}")
    
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
