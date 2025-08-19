"""
Обработчики для взаимодействия с комментариями Okdesk
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.models import db
from services.okdesk_service import get_issue_service
from keyboards.main import get_back_to_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()

class CommentReplyStates(StatesGroup):
    waiting_for_reply = State()

@router.callback_query(F.data.startswith("reply_to_issue_"))
async def start_reply_to_issue(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс ответа на комментарий в заявке"""
    await callback.answer()
    
    try:
        issue_id = int(callback.data.split("_")[-1])
        
        # Проверяем права пользователя
        user = db.get_user(callback.from_user.id)
        if not user or not user.is_registered:
            await callback.message.edit_text(
                "❌ Вы не зарегистрированы в системе.",
                reply_markup=get_back_to_menu_keyboard()
            )
            return
        
        # Сохраняем ID заявки в состоянии
        await state.update_data(issue_id=issue_id)
        await state.set_state(CommentReplyStates.waiting_for_reply)
        
        await callback.message.edit_text(
            f"💬 <b>Ответ на заявку #{issue_id}</b>\n\n"
            f"Напишите ваш ответ в следующем сообщении.\n"
            f"Он будет добавлен как комментарий к заявке в Okdesk.\n\n"
            f"❌ Для отмены отправьте /cancel",
            parse_mode="HTML"
        )
        
    except (ValueError, IndexError):
        await callback.message.edit_text(
            "❌ Ошибка: неверный формат ID заявки.",
            reply_markup=get_back_to_menu_keyboard()
        )

@router.message(CommentReplyStates.waiting_for_reply)
async def process_reply_to_issue(message: Message, state: FSMContext):
    """Обрабатывает ответ пользователя и отправляет в Okdesk"""
    
    # Проверяем на отмену
    if message.text and message.text.lower() in ['/cancel', 'отмена', 'cancel']:
        await state.clear()
        await message.answer(
            "❌ Ответ отменен.",
            reply_markup=get_back_to_menu_keyboard()
        )
        return
    
    data = await state.get_data()
    issue_id = data.get('issue_id')
    
    if not issue_id:
        await state.clear()
        await message.answer(
            "❌ Ошибка: ID заявки не найден.",
            reply_markup=get_back_to_menu_keyboard()
        )
        return
    
    # Получаем текст ответа
    reply_text = message.text or "Отправлен медиафайл"
    
    # Показываем индикатор отправки
    status_message = await message.answer(
        "📤 <b>Отправляем ваш ответ...</b>",
        parse_mode="HTML"
    )
    
    try:
        # Получаем сервис Okdesk
        issue_service = get_issue_service()
        if not issue_service:
            await status_message.edit_text(
                "❌ Сервис Okdesk недоступен. Обратитесь к администратору.",
                reply_markup=get_back_to_menu_keyboard()
            )
            await state.clear()
            return
        
        # Формируем комментарий с информацией об авторе
        user = db.get_user(message.from_user.id)
        author_info = f"👤 {user.full_name}" if user else f"👤 @{message.from_user.username or message.from_user.id}"
        
        comment_text = f"{author_info} (через Telegram):\n\n{reply_text}"
        
        # Получаем ID текущего пользователя API для авторства комментария
        current_user = await issue_service.okdesk_service.get_current_user()
        author_id = current_user.get('id') if current_user else None
        
        # Если не удается получить ID API пользователя, пробуем использовать ID контакта пользователя
        if not author_id:
            user = db.get_user(message.from_user.id)
            if user and user.okdesk_contact_id:
                author_id = user.okdesk_contact_id
                logger.info(f"Используем okdesk_contact_id как author_id: {author_id}")
            else:
                logger.warning("Не удалось получить author_id, отправляем комментарий без него")
        
        # Отправляем комментарий в Okdesk
        success = await issue_service.okdesk_service.add_comment_to_issue(
            issue_id=issue_id,
            comment_text=comment_text,
            is_public=True,
            author_id=author_id
        )
        
        if success:
            await status_message.edit_text(
                f"✅ <b>Ответ отправлен!</b>\n\n"
                f"📝 Ваш комментарий добавлен к заявке #{issue_id}\n"
                f"🔔 Сотрудники поддержки увидят ваш ответ в системе",
                parse_mode="HTML",
                reply_markup=get_back_to_menu_keyboard()
            )
            
            logger.info(f"Пользователь {message.from_user.id} ответил на заявку {issue_id}")
            
        else:
            await status_message.edit_text(
                f"❌ <b>Ошибка отправки ответа</b>\n\n"
                f"Не удалось добавить комментарий к заявке #{issue_id}.\n"
                f"Попробуйте позже или обратитесь к администратору.",
                parse_mode="HTML",
                reply_markup=get_back_to_menu_keyboard()
            )
        
    except Exception as e:
        logger.error(f"Ошибка отправки ответа на заявку {issue_id}: {e}")
        await status_message.edit_text(
            "❌ Произошла ошибка при отправке ответа. Попробуйте позже.",
            reply_markup=get_back_to_menu_keyboard()
        )
    
    finally:
        await state.clear()

@router.callback_query(F.data.startswith("issue_details_"))
async def show_issue_details(callback: CallbackQuery):
    """Показывает детали заявки"""
    await callback.answer()
    
    try:
        issue_id = int(callback.data.split("_")[-1])
        
        # Показываем индикатор загрузки
        await callback.message.edit_text(
            "🔄 <b>Загружаем детали заявки...</b>",
            parse_mode="HTML"
        )
        
        # Получаем сервис Okdesk
        issue_service = get_issue_service()
        if not issue_service:
            await callback.message.edit_text(
                "❌ Сервис Okdesk недоступен.",
                reply_markup=get_back_to_menu_keyboard()
            )
            return
        
        # Получаем детали заявки
        issue_details = await issue_service.okdesk_service.get_issue_details(issue_id)
        
        if not issue_details:
            await callback.message.edit_text(
                f"❌ Заявка #{issue_id} не найдена или недоступна.",
                reply_markup=get_back_to_menu_keyboard()
            )
            return
        
        # Формируем сообщение с деталями
        title = issue_details.get('title', 'Без названия')
        description = issue_details.get('description', 'Без описания')
        status = issue_details.get('status', 'Неизвестно')
        priority = issue_details.get('priority', 'normal')
        created_at = issue_details.get('created_at', '')
        
        # Переводим статус
        status_map = {
            'opened': '🟡 Открыта',
            'in_progress': '🔵 В работе', 
            'closed': '🟢 Закрыта',
            'resolved': '✅ Решена'
        }
        status_text = status_map.get(status, f"❓ {status}")
        
        # Переводим приоритет
        priority_map = {
            'low': '🟢 Низкий',
            'normal': '🟡 Обычный',
            'high': '🟠 Высокий',
            'critical': '🔴 Критический'
        }
        priority_text = priority_map.get(priority, f"❓ {priority}")
        
        # Форматируем время
        time_text = "Неизвестно"
        if created_at:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                time_text = dt.strftime("%d.%m.%Y %H:%M")
            except ValueError:
                time_text = created_at
        
        # Обрезаем длинное описание
        if len(description) > 400:
            description = description[:397] + "..."
        
        details_text = (
            f"📋 <b>Заявка #{issue_id}</b>\n\n"
            f"📝 <b>Название:</b> {title}\n"
            f"📊 <b>Статус:</b> {status_text}\n"
            f"⭐ <b>Приоритет:</b> {priority_text}\n"
            f"📅 <b>Создана:</b> {time_text}\n\n"
            f"📄 <b>Описание:</b>\n<i>{description}</i>"
        )
        
        # Создаем клавиатуру с действиями
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Добавить комментарий", 
                    callback_data=f"reply_to_issue_{issue_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Назад", 
                    callback_data="back_to_menu"
                )
            ]
        ])
        
        await callback.message.edit_text(
            details_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
    except (ValueError, IndexError):
        await callback.message.edit_text(
            "❌ Ошибка: неверный формат ID заявки.",
            reply_markup=get_back_to_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка получения деталей заявки: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке деталей заявки.",
            reply_markup=get_back_to_menu_keyboard()
        )

@router.callback_query(F.data.startswith("close_issue_"))
async def close_issue(callback: CallbackQuery):
    """Закрывает заявку (меняет статус)"""
    await callback.answer()
    
    try:
        issue_id = int(callback.data.split("_")[-1])
        
        # Показываем индикатор
        await callback.message.edit_text(
            "🔄 <b>Закрываем заявку...</b>",
            parse_mode="HTML"
        )
        
        # Получаем сервис Okdesk
        issue_service = get_issue_service()
        if not issue_service:
            await callback.message.edit_text(
                "❌ Сервис Okdesk недоступен.",
                reply_markup=get_back_to_menu_keyboard()
            )
            return
        
        # Закрываем заявку
        success = await issue_service.okdesk_service.update_issue_status(
            issue_id, "closed"
        )
        
        if success:
            # Убираем заявку из мониторинга
            await db.remove_user_issue_from_monitoring(issue_id)
            
            await callback.message.edit_text(
                f"✅ <b>Заявка #{issue_id} закрыта</b>\n\n"
                f"Статус заявки изменен на 'Закрыта'.\n"
                f"Мониторинг комментариев отключен.",
                parse_mode="HTML",
                reply_markup=get_back_to_menu_keyboard()
            )
            
            logger.info(f"Пользователь {callback.from_user.id} закрыл заявку {issue_id}")
            
        else:
            await callback.message.edit_text(
                f"❌ <b>Ошибка закрытия заявки</b>\n\n"
                f"Не удалось изменить статус заявки #{issue_id}.\n"
                f"Возможно, у вас нет прав на это действие.",
                parse_mode="HTML",
                reply_markup=get_back_to_menu_keyboard()
            )
        
    except (ValueError, IndexError):
        await callback.message.edit_text(
            "❌ Ошибка: неверный формат ID заявки.",
            reply_markup=get_back_to_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка закрытия заявки: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при закрытии заявки.",
            reply_markup=get_back_to_menu_keyboard()
        )
