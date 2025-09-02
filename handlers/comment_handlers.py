"""
Обработчики для взаимодействия с комментариями Okdesk
"""

import logging
from typing import Optional
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
    waiting_for_client_reply = State()
    waiting_for_specialist_reply = State()

@router.callback_query(F.data.startswith("client_reply:"))
async def start_client_reply(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс ответа клиента на заявку"""
    await callback.answer()
    
    try:
        issue_id = int(callback.data.split(":")[-1])
        
        # Проверяем права пользователя
        user = db.get_user(callback.from_user.id)
        if not user or not user.is_registered:
            await callback.message.edit_text(
                "❌ Вы не зарегистрированы в системе.",
                reply_markup=get_back_to_menu_keyboard()
            )
            return
        
        # Сохраняем ID заявки в состоянии
        await state.update_data(issue_id=issue_id, reply_type="client")
        await state.set_state(CommentReplyStates.waiting_for_client_reply)
        
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

@router.callback_query(F.data.startswith("reply_to_issue:"))
async def start_specialist_reply(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс ответа специалиста на заявку"""
    await callback.answer()
    
    try:
        issue_id = int(callback.data.split(":")[-1])
        
        # Проверяем права пользователя (только админы и специалисты)
        user = db.get_user(callback.from_user.id)
        if not user or not user.is_registered:
            await callback.message.edit_text(
                "❌ Вы не зарегистрированы в системе.",
                reply_markup=get_back_to_menu_keyboard()
            )
            return
        
        # Здесь можно добавить проверку на роль специалиста
        # if user.role != 'specialist' and callback.from_user.id not in ADMIN_IDS:
        #     await callback.message.edit_text("❌ У вас нет прав для ответа на заявки.")
        #     return
        
        # Сохраняем ID заявки в состоянии
        await state.update_data(issue_id=issue_id, reply_type="specialist")
        await state.set_state(CommentReplyStates.waiting_for_specialist_reply)
        
        await callback.message.edit_text(
            f"💼 <b>Ответ специалиста на заявку #{issue_id}</b>\n\n"
            f"Напишите ваш ответ клиенту.\n"
            f"Комментарий будет добавлен в Okdesk и отправлен клиенту в Telegram.\n\n"
            f"❌ Для отмены отправьте /cancel",
            parse_mode="HTML"
        )
        
    except (ValueError, IndexError):
        await callback.message.edit_text(
            "❌ Ошибка: неверный формат ID заявки.",
            reply_markup=get_back_to_menu_keyboard()
        )
        await callback.message.edit_text(
            "❌ Ошибка: неверный формат ID заявки.",
            reply_markup=get_back_to_menu_keyboard()
        )

@router.message(CommentReplyStates.waiting_for_client_reply)
async def process_client_reply(message: Message, state: FSMContext):
    """Обрабатывает ответ клиента и отправляет в Okdesk"""
    
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
        
        # Формируем комментарий с информацией об авторе (клиент)
        user = db.get_user(message.from_user.id)
        author_info = f"👤 {user.full_name}" if user else f"👤 @{message.from_user.username or message.from_user.id}"
        
        comment_text = f"{author_info} (клиент через Telegram):\n\n{reply_text}"
        
        # Отправляем комментарий в Okdesk
        success = await issue_service.okdesk_service.add_comment_to_issue(
            issue_id=issue_id,
            comment_text=comment_text,
            is_public=True,
            author_id=None  # Для клиентов author_id не нужен
        )
        
        if success:
            await status_message.edit_text(
                f"✅ <b>Ответ отправлен!</b>\n\n"
                f"📝 Ваш комментарий добавлен к заявке #{issue_id}\n"
                f"🔔 Сотрудники поддержки увидят ваш ответ в системе",
                parse_mode="HTML",
                reply_markup=get_back_to_menu_keyboard()
            )
            
            logger.info(f"Клиент {message.from_user.id} ответил на заявку {issue_id}")
            
        else:
            await status_message.edit_text(
                f"❌ <b>Ошибка отправки ответа</b>\n\n"
                f"Не удалось добавить комментарий к заявке #{issue_id}.\n"
                f"Попробуйте позже или обратитесь к администратору.",
                parse_mode="HTML",
                reply_markup=get_back_to_menu_keyboard()
            )
        
    except Exception as e:
        logger.error(f"Ошибка отправки ответа клиента на заявку {issue_id}: {e}")
        await status_message.edit_text(
            "❌ Произошла ошибка при отправке ответа. Попробуйте позже.",
            reply_markup=get_back_to_menu_keyboard()
        )
    
    await state.clear()

@router.message(CommentReplyStates.waiting_for_specialist_reply)
async def process_specialist_reply(message: Message, state: FSMContext):
    """Обрабатывает ответ специалиста и отправляет в Okdesk + уведомляет клиента"""
    
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
        "📤 <b>Отправляем ответ клиенту...</b>",
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
        
        # Формируем комментарий с информацией об авторе (специалист)
        user = db.get_user(message.from_user.id)
        specialist_name = user.full_name if user else message.from_user.first_name or "Специалист"
        
        comment_text = f"{specialist_name} (через Telegram):\n\n{reply_text}"
        
        # Получаем ID специалиста для авторства комментария
        current_user = await issue_service.okdesk_service.get_current_user()
        author_id = current_user.get('id') if current_user else 1  # Fallback на admin
        
        # Отправляем комментарий в Okdesk
        success = await issue_service.okdesk_service.add_comment_to_issue(
            issue_id=issue_id,
            comment_text=comment_text,
            is_public=True,
            author_id=author_id
        )
        
        if success:
            # Ищем клиента для уведомления
            client_telegram_id = await get_client_telegram_id_by_issue(issue_id)
            
            if client_telegram_id:
                # Отправляем уведомление клиенту
                from keyboards.main import get_issue_reply_keyboard
                keyboard = get_issue_reply_keyboard(issue_id)
                
                try:
                    await message.bot.send_message(
                        chat_id=client_telegram_id,
                        text=(
                            f"💬 **Новое сообщение по заявке #{issue_id}**\n\n"
                            f"👨‍💼 **{specialist_name}:** {reply_text}\n\n"
                            f"💡 *Нажмите \"Ответить\" для отправки ответа*"
                        ),
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                    logger.info(f"Уведомление отправлено клиенту {client_telegram_id}")
                except Exception as e:
                    logger.error(f"Ошибка отправки уведомления клиенту: {e}")
            
            await status_message.edit_text(
                f"✅ <b>Ответ отправлен!</b>\n\n"
                f"📝 Комментарий добавлен к заявке #{issue_id}\n"
                f"🔔 Клиент получит уведомление в Telegram",
                parse_mode="HTML",
                reply_markup=get_back_to_menu_keyboard()
            )
            
            logger.info(f"Специалист {message.from_user.id} ответил на заявку {issue_id}")
            
        else:
            await status_message.edit_text(
                f"❌ <b>Ошибка отправки ответа</b>\n\n"
                f"Не удалось добавить комментарий к заявке #{issue_id}.\n"
                f"Попробуйте позже или обратитесь к администратору.",
                parse_mode="HTML",
                reply_markup=get_back_to_menu_keyboard()
            )
        
    except Exception as e:
        logger.error(f"Ошибка отправки ответа специалиста на заявку {issue_id}: {e}")
        await status_message.edit_text(
            "❌ Произошла ошибка при отправке ответа. Попробуйте позже.",
            reply_markup=get_back_to_menu_keyboard()
        )
    
    await state.clear()

# Вспомогательные функции
async def get_client_telegram_id_by_issue(issue_id: int) -> Optional[int]:
    """Получает Telegram ID клиента по ID заявки"""
    try:
        # Здесь нужно реализовать поиск клиента в базе данных
        # по связке с заявкой в Okdesk
        # Пока возвращаем None, функцию нужно доработать
        
        # Можно найти в базе данных по связке issue_id -> contact_id -> telegram_id
        # Или искать в логах создания заявок
        
        logger.warning(f"Поиск клиента для заявки {issue_id} не реализован")
        return None
        
    except Exception as e:
        logger.error(f"Ошибка поиска клиента для заявки {issue_id}: {e}")
        return None

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
