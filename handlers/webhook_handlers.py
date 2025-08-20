"""
Обработчики webhook событий от клиентов и специалистов
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.okdesk_service import OkdeskService
from keyboards.main import get_main_menu, get_client_issue_menu
from keyboards.specialist import get_specialist_reply_keyboard, get_issue_status_keyboard
import logging

logger = logging.getLogger(__name__)

webhook_router = Router()

class ReplyStates(StatesGroup):
    waiting_for_reply = State()
    waiting_for_specialist_reply = State()

# Обработчики для клиентов
@webhook_router.callback_query(F.data.startswith("client_reply_"))
async def handle_client_reply(callback: CallbackQuery, state: FSMContext):
    """Обработка ответа клиента на заявку"""
    try:
        issue_id = int(callback.data.split("_")[-1])
        
        await callback.message.answer(
            f"💬 Напишите ваш ответ по заявке #{issue_id}:",
            reply_markup=None
        )
        
        await state.set_state(ReplyStates.waiting_for_reply)
        await state.update_data(issue_id=issue_id)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка обработки ответа клиента: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

@webhook_router.message(ReplyStates.waiting_for_reply)
async def process_client_reply(message: Message, state: FSMContext):
    """Обработка текста ответа от клиента"""
    try:
        data = await state.get_data()
        issue_id = data.get('issue_id')
        
        if not issue_id:
            await message.answer("❌ Ошибка: ID заявки не найден")
            await state.clear()
            return
        
        # Отправляем комментарий в Okdesk
        okdesk_service = OkdeskService()
        success = await okdesk_service.add_comment_to_issue(
            issue_id=issue_id,
            comment_text=message.text,
            is_public=True,
            author_type="contact"
        )
        
        if success:
            await message.answer(
                f"✅ Ваш ответ по заявке #{issue_id} отправлен!\n\n"
                f"Специалист получит уведомление и скоро ответит.",
                reply_markup=get_main_menu()
            )
        else:
            await message.answer(
                f"❌ Не удалось отправить ответ по заявке #{issue_id}.\n"
                f"Попробуйте позже или обратитесь в поддержку.",
                reply_markup=get_main_menu()
            )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка отправки ответа клиента: {e}")
        await message.answer(
            "❌ Произошла ошибка при отправке ответа",
            reply_markup=get_main_menu()
        )
        await state.clear()

@webhook_router.callback_query(F.data.startswith("issue_details_"))
async def handle_issue_details(callback: CallbackQuery):
    """Показать детали заявки"""
    try:
        issue_id = int(callback.data.split("_")[-1])
        
        okdesk_service = OkdeskService()
        issue = await okdesk_service.get_issue(issue_id)
        
        if not issue:
            await callback.answer("❌ Заявка не найдена", show_alert=True)
            return
        
        # Формируем детальную информацию
        status = issue.get('status', {}).get('name', 'Неизвестно')
        priority = issue.get('priority', {}).get('name', 'Обычная')
        assignee = issue.get('assignee', {}).get('name', 'Не назначен')
        created_at = issue.get('created_at', 'Неизвестно')
        description = issue.get('description', 'Нет описания')[:200]
        
        if len(issue.get('description', '')) > 200:
            description += "..."
        
        details_text = (
            f"📋 **Детали заявки #{issue_id}**\n\n"
            f"📊 **Статус:** {status}\n"
            f"⚡ **Приоритет:** {priority}\n"
            f"👨‍💼 **Исполнитель:** {assignee}\n"
            f"📅 **Создана:** {created_at}\n\n"
            f"📝 **Описание:**\n{description}"
        )
        
        await callback.message.answer(
            details_text,
            reply_markup=get_client_issue_menu(issue_id),
            parse_mode="Markdown"
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка получения деталей заявки: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

@webhook_router.callback_query(F.data.startswith("close_issue_"))
async def handle_close_issue(callback: CallbackQuery):
    """Закрытие заявки клиентом"""
    try:
        issue_id = int(callback.data.split("_")[-1])
        
        okdesk_service = OkdeskService()
        success = await okdesk_service.update_issue_status(issue_id, "closed")
        
        if success:
            await callback.message.answer(
                f"✅ Заявка #{issue_id} закрыта!\n\n"
                f"Спасибо за использование нашего сервиса. "
                f"Если у вас возникнут новые вопросы, создайте новую заявку.",
                reply_markup=get_main_menu()
            )
        else:
            await callback.answer("❌ Не удалось закрыть заявку", show_alert=True)
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка закрытия заявки: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

# Обработчики для специалистов
@webhook_router.callback_query(F.data.startswith("specialist_reply_"))
async def handle_specialist_reply(callback: CallbackQuery, state: FSMContext):
    """Обработка ответа специалиста на заявку"""
    try:
        issue_id = int(callback.data.split("_")[-1])
        
        await callback.message.answer(
            f"💬 Напишите ваш ответ по заявке #{issue_id}:\n\n"
            f"💡 *Сообщение будет отправлено клиенту*",
            reply_markup=None,
            parse_mode="Markdown"
        )
        
        await state.set_state(ReplyStates.waiting_for_specialist_reply)
        await state.update_data(issue_id=issue_id)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка обработки ответа специалиста: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

@webhook_router.message(ReplyStates.waiting_for_specialist_reply)
async def process_specialist_reply(message: Message, state: FSMContext):
    """Обработка текста ответа от специалиста"""
    try:
        data = await state.get_data()
        issue_id = data.get('issue_id')
        
        if not issue_id:
            await message.answer("❌ Ошибка: ID заявки не найден")
            await state.clear()
            return
        
        # Отправляем комментарий в Okdesk
        okdesk_service = OkdeskService()
        success = await okdesk_service.add_comment_to_issue(
            issue_id=issue_id,
            comment_text=message.text,
            is_public=True,
            author_type="employee"
        )
        
        if success:
            await message.answer(
                f"✅ Ваш ответ по заявке #{issue_id} отправлен!\n\n"
                f"Клиент получит уведомление.",
                reply_markup=get_specialist_reply_keyboard(issue_id)
            )
        else:
            await message.answer(
                f"❌ Не удалось отправить ответ по заявке #{issue_id}.\n"
                f"Попробуйте позже.",
                reply_markup=get_specialist_reply_keyboard(issue_id)
            )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка отправки ответа специалиста: {e}")
        await message.answer("❌ Произошла ошибка при отправке ответа")
        await state.clear()

@webhook_router.callback_query(F.data.startswith("resolve_issue_"))
async def handle_resolve_issue(callback: CallbackQuery):
    """Решение заявки специалистом"""
    try:
        issue_id = int(callback.data.split("_")[-1])
        
        okdesk_service = OkdeskService()
        success = await okdesk_service.update_issue_status(issue_id, "resolved")
        
        if success:
            await callback.message.answer(
                f"✅ Заявка #{issue_id} помечена как решенная!\n\n"
                f"Клиент получит уведомление об изменении статуса."
            )
        else:
            await callback.answer("❌ Не удалось изменить статус заявки", show_alert=True)
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка решения заявки: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

@webhook_router.callback_query(F.data.startswith("change_status_"))
async def handle_change_status_menu(callback: CallbackQuery):
    """Показать меню изменения статуса"""
    try:
        issue_id = int(callback.data.split("_")[-1])
        
        await callback.message.answer(
            f"🔄 Выберите новый статус для заявки #{issue_id}:",
            reply_markup=get_issue_status_keyboard(issue_id)
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка показа меню статуса: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

@webhook_router.callback_query(F.data.startswith("set_status_"))
async def handle_set_status(callback: CallbackQuery):
    """Установка нового статуса заявки"""
    try:
        parts = callback.data.split("_")
        issue_id = int(parts[2])
        new_status = parts[3]
        
        # Маппинг статусов
        status_mapping = {
            "new": "new",
            "in": "in_progress", 
            "waiting": "waiting",
            "resolved": "resolved",
            "closed": "closed"
        }
        
        okdesk_status = status_mapping.get(new_status, new_status)
        
        okdesk_service = OkdeskService()
        success = await okdesk_service.update_issue_status(issue_id, okdesk_status)
        
        if success:
            status_names = {
                "new": "Новая",
                "in": "В работе",
                "waiting": "Ожидание",
                "resolved": "Решена",
                "closed": "Закрыта"
            }
            
            status_name = status_names.get(new_status, new_status)
            
            await callback.message.answer(
                f"✅ Статус заявки #{issue_id} изменен на: {status_name}\n\n"
                f"Клиент получит уведомление об изменении."
            )
        else:
            await callback.answer("❌ Не удалось изменить статус заявки", show_alert=True)
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка установки статуса: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)
