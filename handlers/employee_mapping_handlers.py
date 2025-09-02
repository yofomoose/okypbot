"""
Команды администратора для настройки сопоставления сотрудников OkDesk и пользователей Telegram
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.employee_mapping import EmployeeMappingService
from keyboards.admin_keyboards import get_admin_menu_keyboard
from config import ADMIN_IDS

router = Router()

# Состояния для FSM
class EmployeeMappingStates(StatesGroup):
    waiting_for_okdesk_id = State()
    waiting_for_telegram_id = State()
    waiting_for_default_id = State()
    waiting_for_removal_id = State()

# Проверка на администратора
def is_admin(user_id):
    return str(user_id) in str(ADMIN_IDS).split(',')

# Команда для настройки сопоставления
@router.message(Command("employee_mapping"))
async def cmd_employee_mapping(message: Message):
    """Команда для настройки сопоставления сотрудников OkDesk и пользователей Telegram"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды")
        return
    
    # Создаем клавиатуру с действиями
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Показать все", callback_data="emp_list")
    builder.button(text="➕ Добавить", callback_data="emp_add")
    builder.button(text="🗑️ Удалить", callback_data="emp_remove")
    builder.button(text="⭐ По умолчанию", callback_data="emp_default")
    builder.adjust(2)
    
    await message.answer(
        "Настройка сопоставления сотрудников OkDesk и пользователей Telegram",
        reply_markup=builder.as_markup()
    )

# Обработчик для показа всех сопоставлений
@router.callback_query(F.data == "emp_list")
async def show_mappings(callback: CallbackQuery):
    """Показать все сопоставления"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав для выполнения этой команды")
        return
    
    # Получаем все сопоставления
    mapping_service = EmployeeMappingService()
    mappings = mapping_service.get_all_mappings()
    default_id = mapping_service.get_default_employee_id()
    
    # Формируем текст с сопоставлениями
    text = "📋 **Текущие сопоставления**:\n\n"
    
    if not mappings:
        text += "Сопоставления отсутствуют\n"
    else:
        for okdesk_id, telegram_id in mappings:
            text += f"OkDesk ID: `{okdesk_id}` → Telegram ID: `{telegram_id}`\n"
    
    text += f"\nID сотрудника по умолчанию: `{default_id or 'Не установлен'}`"
    
    # Создаем клавиатуру с действиями
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Обновить", callback_data="emp_list")
    builder.button(text="⬅️ Назад", callback_data="emp_back")
    builder.adjust(2)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()

# Обработчик для добавления сопоставления
@router.callback_query(F.data == "emp_add")
async def add_mapping_start(callback: CallbackQuery, state: FSMContext):
    """Начать добавление сопоставления"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав для выполнения этой команды")
        return
    
    await state.set_state(EmployeeMappingStates.waiting_for_okdesk_id)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="emp_cancel")
    
    await callback.message.edit_text(
        "Введите ID сотрудника OkDesk:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

# Обработчик для ввода ID сотрудника OkDesk
@router.message(EmployeeMappingStates.waiting_for_okdesk_id)
async def process_okdesk_id(message: Message, state: FSMContext):
    """Обработать ввод ID сотрудника OkDesk"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды")
        return
    
    # Проверяем, что введено число
    okdesk_id = message.text.strip()
    if not okdesk_id.isdigit():
        await message.answer("ID должен быть числом. Пожалуйста, введите корректный ID сотрудника OkDesk:")
        return
    
    # Сохраняем ID сотрудника OkDesk
    await state.update_data(okdesk_id=okdesk_id)
    await state.set_state(EmployeeMappingStates.waiting_for_telegram_id)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="emp_cancel")
    
    await message.answer(
        "Введите ID пользователя Telegram:",
        reply_markup=builder.as_markup()
    )

# Обработчик для ввода ID пользователя Telegram
@router.message(EmployeeMappingStates.waiting_for_telegram_id)
async def process_telegram_id(message: Message, state: FSMContext):
    """Обработать ввод ID пользователя Telegram"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды")
        return
    
    # Проверяем, что введено число
    telegram_id = message.text.strip()
    if not telegram_id.isdigit():
        await message.answer("ID должен быть числом. Пожалуйста, введите корректный ID пользователя Telegram:")
        return
    
    # Получаем данные из состояния
    data = await state.get_data()
    okdesk_id = data.get("okdesk_id")
    
    # Добавляем сопоставление
    mapping_service = EmployeeMappingService()
    if mapping_service.add_mapping(okdesk_id, int(telegram_id)):
        await message.answer(f"✅ Сопоставление успешно добавлено:\nOkDesk ID: {okdesk_id} → Telegram ID: {telegram_id}")
    else:
        await message.answer("❌ Ошибка при добавлении сопоставления")
    
    # Сбрасываем состояние
    await state.clear()
    
    # Возвращаемся в меню
    await cmd_employee_mapping(message)

# Обработчик для удаления сопоставления
@router.callback_query(F.data == "emp_remove")
async def remove_mapping_start(callback: CallbackQuery, state: FSMContext):
    """Начать удаление сопоставления"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав для выполнения этой команды")
        return
    
    await state.set_state(EmployeeMappingStates.waiting_for_removal_id)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="emp_cancel")
    
    await callback.message.edit_text(
        "Введите ID сотрудника OkDesk для удаления сопоставления:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

# Обработчик для ввода ID сотрудника OkDesk для удаления
@router.message(EmployeeMappingStates.waiting_for_removal_id)
async def process_removal_id(message: Message, state: FSMContext):
    """Обработать ввод ID сотрудника OkDesk для удаления"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды")
        return
    
    # Проверяем, что введено число
    okdesk_id = message.text.strip()
    if not okdesk_id.isdigit():
        await message.answer("ID должен быть числом. Пожалуйста, введите корректный ID сотрудника OkDesk:")
        return
    
    # Удаляем сопоставление
    mapping_service = EmployeeMappingService()
    if mapping_service.remove_mapping(okdesk_employee_id=okdesk_id):
        await message.answer(f"✅ Сопоставление для OkDesk ID {okdesk_id} успешно удалено")
    else:
        await message.answer(f"❌ Сопоставление для OkDesk ID {okdesk_id} не найдено или произошла ошибка")
    
    # Сбрасываем состояние
    await state.clear()
    
    # Возвращаемся в меню
    await cmd_employee_mapping(message)

# Обработчик для установки ID сотрудника по умолчанию
@router.callback_query(F.data == "emp_default")
async def set_default_start(callback: CallbackQuery, state: FSMContext):
    """Начать установку ID сотрудника по умолчанию"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав для выполнения этой команды")
        return
    
    await state.set_state(EmployeeMappingStates.waiting_for_default_id)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="emp_cancel")
    
    await callback.message.edit_text(
        "Введите ID сотрудника OkDesk, который будет использоваться по умолчанию:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

# Обработчик для ввода ID сотрудника OkDesk по умолчанию
@router.message(EmployeeMappingStates.waiting_for_default_id)
async def process_default_id(message: Message, state: FSMContext):
    """Обработать ввод ID сотрудника OkDesk по умолчанию"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды")
        return
    
    # Проверяем, что введено число
    okdesk_id = message.text.strip()
    if not okdesk_id.isdigit():
        await message.answer("ID должен быть числом. Пожалуйста, введите корректный ID сотрудника OkDesk:")
        return
    
    # Устанавливаем ID сотрудника по умолчанию
    mapping_service = EmployeeMappingService()
    if mapping_service.set_default_employee_id(okdesk_id):
        await message.answer(f"✅ ID сотрудника по умолчанию установлен: {okdesk_id}")
    else:
        await message.answer("❌ Ошибка при установке ID сотрудника по умолчанию")
    
    # Сбрасываем состояние
    await state.clear()
    
    # Возвращаемся в меню
    await cmd_employee_mapping(message)

# Обработчик для отмены операции
@router.callback_query(F.data == "emp_cancel")
async def cancel_operation(callback: CallbackQuery, state: FSMContext):
    """Отменить текущую операцию"""
    await state.clear()
    await callback.message.edit_text("❌ Операция отменена")
    await callback.answer()
    
    # Возвращаемся в меню через 2 секунды
    import asyncio
    await asyncio.sleep(2)
    await cmd_employee_mapping(callback.message)

# Обработчик для возврата в меню
@router.callback_query(F.data == "emp_back")
async def back_to_menu(callback: CallbackQuery):
    """Вернуться в меню"""
    await cmd_employee_mapping(callback.message)
    await callback.answer()
