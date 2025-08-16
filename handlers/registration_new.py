"""
Обработчики для процесса регистрации пользователей
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.models import db
from states.registration import RegistrationStates
from keyboards.registration import (
    get_user_type_keyboard, 
    get_registration_confirmation_keyboard,
    get_phone_request_keyboard
)
from keyboards.main import get_main_menu
from utils.validators import (
    validate_phone, 
    format_phone, 
    validate_inn, 
    validate_full_name, 
    format_full_name,
    get_user_type_text,
    parse_full_name
)
from utils.user_helpers import check_user_exists_by_phone, get_user_by_phone
from api.okdesk_api import OkdeskAPI

router = Router()

@router.message(Command("register"))
async def cmd_register(message: Message, state: FSMContext):
    """Команда начала регистрации"""
    user_id = message.from_user.id
    
    # Проверяем, не зарегистрирован ли уже пользователь
    if db.is_user_registered(user_id):
        user = db.get_user(user_id)
        await message.answer(
            f"✅ Вы уже зарегистрированы!\n\n"
            f"👤 ФИО: {user.full_name}\n"
            f"📱 Телефон: {user.phone}\n"
            f"👔 Тип: {get_user_type_text(user.user_type)}\n"
            f"{f'🏢 Должность: {user.position}' if user.position else ''}\n"
            f"{f'🏛️ ИНН компании: {user.company_inn}' if user.company_inn else ''}"
        )
        return
    
    await message.answer(
        "🔐 **Регистрация в системе Okdesk**\n\n"
        "Для работы с ботом необходимо пройти регистрацию.\n"
        "Выберите тип пользователя:",
        reply_markup=get_user_type_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_user_type)

@router.callback_query(F.data.in_(["register_individual", "register_legal"]))
async def process_user_type(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа пользователя"""
    await callback.answer()
    
    user_type = "individual" if callback.data == "register_individual" else "legal"
    await state.update_data(user_type=user_type)
    
    type_text = get_user_type_text(user_type)
    
    await callback.message.edit_text(
        f"Выбран тип: {type_text}\n\n"
        "📝 Введите ваше ФИО (Фамилия Имя Отчество):"
    )
    await state.set_state(RegistrationStates.waiting_for_full_name)

@router.message(RegistrationStates.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext):
    """Обработка ввода ФИО"""
    full_name = message.text.strip()
    
    if not validate_full_name(full_name):
        await message.answer(
            "❌ Некорректное ФИО!\n\n"
            "Пожалуйста, введите корректное ФИО (минимум Фамилия и Имя).\n"
            "Используйте только буквы, пробелы и дефисы."
        )
        return
    
    formatted_name = format_full_name(full_name)
    await state.update_data(full_name=formatted_name)
    
    await message.answer(
        f"✅ ФИО: {formatted_name}\n\n"
        "📱 Теперь поделитесь вашим номером телефона для связи:",
        reply_markup=get_phone_request_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_phone)

@router.callback_query(F.data == "enter_phone_manually")
async def request_manual_phone(callback: CallbackQuery, state: FSMContext):
    """Запрос ввода телефона вручную"""
    await callback.answer()
    
    await callback.message.edit_text(
        "📱 Введите ваш номер телефона в формате:\n"
        "+7XXXXXXXXXX или 8XXXXXXXXXX"
    )
    await state.set_state(RegistrationStates.waiting_for_phone)

@router.message(RegistrationStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    """Обработка номера телефона"""
    phone = ""
    
    # Проверяем, если это контакт или текст
    if message.contact and message.contact.phone_number:
        phone = message.contact.phone_number
    elif message.text:
        phone = message.text.strip()
    else:
        await message.answer(
            "❌ Некорректный формат!\n\n"
            "Пожалуйста, поделитесь контактом или введите номер телефона."
        )
        return
    
    if not validate_phone(phone):
        await message.answer(
            "❌ Некорректный номер телефона!\n\n"
            "Пожалуйста, введите корректный российский номер телефона.\n"
            "Примеры: +79123456789, 89123456789"
        )
        return
    
    formatted_phone = format_phone(phone)
    
    # Проверяем, не зарегистрирован ли этот номер у другого пользователя
    if check_user_exists_by_phone(formatted_phone):
        existing_user = get_user_by_phone(formatted_phone)
        if existing_user.telegram_id != message.from_user.id:
            await message.answer(
                "❌ Этот номер телефона уже зарегистрирован другим пользователем!\n\n"
                "Пожалуйста, используйте другой номер телефона."
            )
            return
    
    await state.update_data(phone=formatted_phone)
    
    data = await state.get_data()
    user_type = data.get('user_type')
    
    if user_type == "legal":
        await message.answer(
            f"✅ Телефон: {formatted_phone}\n\n"
            "💼 Введите вашу должность в компании:",
            reply_markup=None
        )
        await state.set_state(RegistrationStates.waiting_for_position)
    else:
        await show_registration_confirmation(message, state)

@router.message(RegistrationStates.waiting_for_position)
async def process_position(message: Message, state: FSMContext):
    """Обработка ввода должности"""
    position = message.text.strip()
    
    if len(position) < 2:
        await message.answer("❌ Слишком короткое название должности. Введите корректную должность:")
        return
    
    await state.update_data(position=position)
    
    await message.answer(
        f"✅ Должность: {position}\n\n"
        "🏛️ Введите ИНН вашей компании (10 или 12 цифр):"
    )
    await state.set_state(RegistrationStates.waiting_for_company_inn)

@router.message(RegistrationStates.waiting_for_company_inn)
async def process_company_inn(message: Message, state: FSMContext):
    """Обработка ввода ИНН компании"""
    inn = message.text.strip()
    
    if not validate_inn(inn):
        await message.answer(
            "❌ Некорректный ИНН!\n\n"
            "ИНН должен содержать 10 или 12 цифр.\n"
            "Введите корректный ИНН компании:"
        )
        return
    
    # Очищаем ИНН от лишних символов
    clean_inn = ''.join(filter(str.isdigit, inn))
    await state.update_data(company_inn=clean_inn)
    
    await show_registration_confirmation(message, state)

async def show_registration_confirmation(message: Message, state: FSMContext):
    """Показать подтверждение регистрации"""
    data = await state.get_data()
    
    confirmation_text = (
        "📋 **Подтверждение регистрации**\n\n"
        f"👤 ФИО: {data['full_name']}\n"
        f"📱 Телефон: {data['phone']}\n"
        f"👔 Тип: {get_user_type_text(data['user_type'])}\n"
    )
    
    if data['user_type'] == "legal":
        confirmation_text += (
            f"🏢 Должность: {data.get('position', 'Не указана')}\n"
            f"🏛️ ИНН компании: {data.get('company_inn', 'Не указан')}\n"
        )
    
    confirmation_text += "\n✅ Все данные указаны верно?"
    
    await message.answer(
        confirmation_text,
        reply_markup=get_registration_confirmation_keyboard()
    )

@router.callback_query(F.data == "confirm_registration")
async def confirm_registration(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и завершение регистрации"""
    await callback.answer()
    
    data = await state.get_data()
    user_id = callback.from_user.id
    
    try:
        # Создаем пользователя в локальной БД
        user = db.create_user(
            telegram_id=user_id,
            full_name=data['full_name'],
            phone=data['phone'],
            user_type=data['user_type'],
            position=data.get('position'),
            company_inn=data.get('company_inn')
        )
        
        # Создаем контакт в Okdesk
        okdesk = OkdeskAPI()
        
        try:
            # Парсим ФИО на компоненты
            try:
                last_name, first_name, patronymic = parse_full_name(data['full_name'])
            except ValueError as e:
                raise Exception(f"Ошибка парсинга ФИО: {str(e)}")
            
            contact_data = {
                'phone': data['phone']
            }
            
            # Добавляем отчество если есть
            if patronymic:
                contact_data['patronymic'] = patronymic
            
            # Добавляем должность для юридических лиц
            if data['user_type'] == "legal" and data.get('position'):
                contact_data['position'] = data['position']
            
            company_id = None
            
            # Только для юридических лиц работаем с компаниями
            if data['user_type'] == "legal" and data.get('company_inn'):
                try:
                    # Сначала ищем компанию по ИНН
                    companies = await okdesk.search_company(data['company_inn'])
                    
                    if companies:
                        # Если компания найдена, используем её ID
                        company_id = companies[0]['id']
                        # НЕ привязываем контакт к компании автоматически
                        # так как может не быть прав доступа
                    else:
                        # Пытаемся создать новую компанию
                        try:
                            company_data = {
                                'name': f"Компания (ИНН: {data['company_inn']})",
                                'inn_company': data['company_inn']
                            }
                            company = await okdesk.create_company(**company_data)
                            company_id = company['id']
                        except Exception as company_error:
                            print(f"Не удалось создать компанию: {company_error}")
                            # Продолжаем без компании
                    
                except Exception as e:
                    print(f"Ошибка при работе с компанией: {e}")
                    # Продолжаем создание контакта без компании
            
            # Сначала проверим, не существует ли уже контакт с таким телефоном
            existing_contacts = await okdesk.search_contact(phone=data['phone'])
            
            if existing_contacts:
                # Контакт уже существует, используем его
                contact = existing_contacts[0]
                print(f"Найден существующий контакт: {contact.get('id')}")
            else:
                # Создаем новый контакт БЕЗ привязки к компании
                contact = await okdesk.create_contact(first_name, last_name, **contact_data)
            
            # Обновляем пользователя с ID из Okdesk
            db.mark_user_registered(
                user_id,
                okdesk_contact_id=contact.get('id'),
                okdesk_company_id=company_id
            )
            
            await callback.message.edit_text(
                "🎉 **Регистрация завершена успешно!**\n\n"
                "✅ Вы успешно зарегистрированы в системе Okdesk.\n"
                "🚀 Теперь вы можете пользоваться всеми функциями бота!\n\n"
                "Используйте команду /menu для доступа к основному меню.",
                reply_markup=get_main_menu()
            )
            
        except Exception as e:
            print(f"Ошибка при регистрации в Okdesk: {str(e)}")
            await callback.message.edit_text(
                f"❌ Ошибка при регистрации: {str(e)}\n\n"
                "Попробуйте еще раз позже или обратитесь к администратору."
            )
            
        finally:
            # Всегда закрываем сессию
            await okdesk.close()
            
    except Exception as e:
        print(f"Ошибка при создании пользователя: {str(e)}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при регистрации.\n\n"
            "Попробуйте еще раз позже или обратитесь к администратору."
        )
    
    await state.clear()

@router.callback_query(F.data == "edit_registration")
async def edit_registration(callback: CallbackQuery, state: FSMContext):
    """Редактирование данных регистрации"""
    await callback.answer()
    
    await callback.message.edit_text(
        "🔐 **Регистрация в системе Okdesk**\n\n"
        "Для работы с ботом необходимо пройти регистрацию.\n"
        "Выберите тип пользователя:",
        reply_markup=get_user_type_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_user_type)

# Обработчик для пользователей, которые не прошли регистрацию
async def handle_unregistered_user(message: Message):
    """Обработка команд от незарегистрированных пользователей"""
    await message.answer(
        "🔐 **Доступ ограничен**\n\n"
        "Для использования бота необходимо пройти регистрацию.\n"
        "Нажмите /register для начала регистрации."
    )
