"""
Обработчики для создания заявок с ML классификацией
"""

import logging
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from services.okdesk_service import get_issue_service
from database.models import db
from keyboards.main import get_back_to_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()

class IssueCreationStates(StatesGroup):
    waiting_for_description = State()
    confirming_issue = State()

@router.message(Command("create_issue"))
async def start_issue_creation(message: Message, state: FSMContext):
    """Начинает процесс создания заявки"""
    
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer(
            "❌ Вы не зарегистрированы в системе.\n"
            "Используйте /start для регистрации.",
            reply_markup=get_back_to_menu_keyboard()
        )
        return
    
    if not user.is_registered:
        await message.answer(
            "❌ Ваша регистрация еще не завершена.\n"
            "Пожалуйста, дождитесь подтверждения или обратитесь к администратору.",
            reply_markup=get_back_to_menu_keyboard()
        )
        return
    
    await message.answer(
        "🎫 <b>Создание новой заявки</b>\n\n"
        "📝 Опишите вашу проблему одним сообщением.\n"
        "📎 Вы можете приложить фото или видео (необязательно).\n\n"
        "💡 <i>Примеры:</i>\n"
        "• Принтер HP не печатает документы, горит красная лампочка\n"
        "• Компьютер зависает при открытии Excel, появляется синий экран\n"
        "• Не работает интернет в переговорной комнате на 3 этаже",
        parse_mode="HTML",
        reply_markup=get_back_to_menu_keyboard()
    )
    
    await state.set_state(IssueCreationStates.waiting_for_description)

# Альтернативный способ начать создание заявки через callback
async def start_issue_creation_callback(message: Message, state: FSMContext):
    """Начинает процесс создания заявки через callback"""
    
    user = db.get_user(message.chat.id if hasattr(message, 'chat') else message.from_user.id)
    if not user or not user.is_registered:
        await message.edit_text(
            "❌ Вы не зарегистрированы в системе или регистрация не завершена.",
            reply_markup=get_back_to_menu_keyboard()
        )
        return
    
    await message.edit_text(
        "🎫 <b>Создание новой заявки</b>\n\n"
        "📝 Опишите вашу проблему одним сообщением.\n"
        "📎 Вы можете приложить фото или видео (необязательно).\n\n"
        "💡 <i>Примеры:</i>\n"
        "• Принтер HP не печатает документы, горит красная лампочка\n"
        "• Компьютер зависает при открытии Excel, появляется синий экран\n"
        "• Не работает интернет в переговорной комнате на 3 этаже",
        parse_mode="HTML",
        reply_markup=get_back_to_menu_keyboard()
    )
    
    await state.set_state(IssueCreationStates.waiting_for_description)

@router.message(IssueCreationStates.waiting_for_description)
async def process_issue_description(message: Message, state: FSMContext):
    """Обрабатывает описание заявки с медиафайлами"""
    
    # Получаем описание из текста сообщения
    description = ""
    media_files = []
    
    if message.text:
        description = message.text.strip()
    elif message.caption:
        description = message.caption.strip()
    
    if len(description) < 10:
        await message.answer(
            "❌ Описание слишком короткое. Минимум 10 символов.\n"
            "Попробуйте подробнее описать проблему:"
        )
        return
    
    if len(description) > 2000:
        await message.answer(
            "❌ Описание слишком длинное. Максимум 2000 символов.\n"
            "Попробуйте сократить:"
        )
        return
    
    # Проверяем наличие медиафайлов
    if message.photo:
        media_files.append({
            "type": "photo",
            "file_id": message.photo[-1].file_id,  # Берем фото наибольшего размера
            "caption": "Фото к заявке"
        })
    elif message.video:
        media_files.append({
            "type": "video", 
            "file_id": message.video.file_id,
            "caption": "Видео к заявке"
        })
    elif message.document:
        # Проверяем, что это изображение или видео
        if message.document.mime_type and (
            message.document.mime_type.startswith("image/") or 
            message.document.mime_type.startswith("video/")
        ):
            media_files.append({
                "type": "document",
                "file_id": message.document.file_id,
                "caption": f"Файл: {message.document.file_name or 'Без названия'}"
            })
    
    # Генерируем заголовок на основе первых слов описания
    words = description.split()
    title = " ".join(words[:8])  # Берем первые 8 слов
    if len(title) > 50:
        title = title[:47] + "..."
    
    # Сохраняем данные
    await state.update_data(
        title=title,
        description=description,
        media_files=media_files
    )
    
    # Показываем предварительный просмотр с ML классификацией
    processing_msg = await message.answer("🤖 Анализирую заявку...")
    
    # Получаем ML классификацию
    try:
        from services.ml_service import ml_service
        
        # Классифицируем описание
        result = await ml_service.classify_issue(description, user_id=message.from_user.id)
        category = result.get('category', 'Другое')
        confidence = result.get('confidence', 0.0)
        
        await state.update_data(
            ml_category=category,
            ml_confidence=confidence,
            classification_result=result  # Сохраняем полный результат
        )
        
        await processing_msg.delete()
        
        # Формируем текст предварительного просмотра
        preview_text = (
            "📋 <b>Предварительный просмотр заявки</b>\n\n"
            f"📝 <b>Описание:</b>\n{description}\n\n"
            f"🤖 <b>ML Классификация:</b>\n"
            f"📂 Категория: {category}\n"
            f"🎯 Уверенность: {confidence:.2f}\n"
        )
        
        if media_files:
            preview_text += f"\n📎 <b>Прикреплено файлов:</b> {len(media_files)}\n"
            for media in media_files:
                preview_text += f"• {media['caption']}\n"
        
        preview_text += "\n✅ Создать заявку?"
        
    except Exception as e:
        logger.error(f"Ошибка ML классификации: {e}")
        await processing_msg.delete()
        
        # Без ML классификации
        await state.update_data(
            ml_category="Не определена",
            ml_confidence=0.0
        )
        
        preview_text = (
            "📋 <b>Предварительный просмотр заявки</b>\n\n"
            f"📝 <b>Описание:</b>\n{description}\n\n"
            "⚠️ ML классификация недоступна\n"
        )
        
        if media_files:
            preview_text += f"\n📎 <b>Прикреплено файлов:</b> {len(media_files)}\n"
            for media in media_files:
                preview_text += f"• {media['caption']}\n"
        
        preview_text += "\n✅ Создать заявку?"
    
    # Клавиатура подтверждения
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Создать заявку", callback_data="confirm_create_issue"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_create_issue")
        ],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="menu")]
    ])
    
    await message.answer(preview_text, parse_mode="HTML", reply_markup=keyboard)
    await state.set_state(IssueCreationStates.confirming_issue)

@router.callback_query(F.data == "confirm_create_issue", IssueCreationStates.confirming_issue)
async def confirm_issue_creation(callback: CallbackQuery, state: FSMContext):
    """Подтверждает создание заявки с медиафайлами"""
    
    await callback.answer()
    
    data = await state.get_data()
    title = data.get('title')
    description = data.get('description')
    media_files = data.get('media_files', [])
    ml_category = data.get('ml_category')
    ml_confidence = data.get('ml_confidence', 0.0)
    
    user = db.get_user(callback.from_user.id)
    if not user or not user.is_registered:
        await callback.message.edit_text(
            "❌ Ошибка: пользователь не найден или не зарегистрирован.",
            reply_markup=get_back_to_menu_keyboard()
        )
        await state.clear()
        return
    
    # Показываем индикатор создания
    await callback.message.edit_text(
        "🔄 <b>Создаем заявку...</b>\n\n"
        "📤 Отправка в Okdesk...\n"
        "📎 Загрузка медиафайлов...",
        parse_mode="HTML"
    )
    
    try:
        # Получаем сервис заявок
        issue_service = get_issue_service()
        if not issue_service:
            await callback.message.edit_text(
                "❌ Сервис заявок недоступен. Обратитесь к администратору.",
                reply_markup=get_back_to_menu_keyboard()
            )
            await state.clear()
            return
        
        # Создаем заявку через Okdesk API
        result = await issue_service.create_issue_with_classification(
            title=title,
            description=description,
            contact_id=user.okdesk_contact_id,  # Используем реальный contact_id пользователя
            company_id=user.okdesk_company_id,  # Используем реальный company_id пользователя
            user_id=callback.from_user.id
        )
        
        if result:
            # Извлекаем данные из результата
            issue_data = result.get('issue', {})
            classification_data = result.get('classification', {})
            ml_comment_added = result.get('ml_comment_added', False)
            
            issue_id = issue_data.get('id')
            if not issue_id:
                logger.error(f"Не найден ID заявки в результате: {result}")
                await callback.message.edit_text(
                    "❌ Ошибка получения ID заявки. Попробуйте позже.",
                    reply_markup=get_back_to_menu_keyboard()
                )
                await state.clear()
                return
            
            # Получаем данные классификации
            ml_category = classification_data.get('category', 'Не определена')
            ml_confidence = classification_data.get('confidence', 0.0)
            classification_id = classification_data.get('classification_id')
            
            # Проверяем, что ML комментарий был добавлен
            if not ml_comment_added and ml_category != "Не определена":
                # Добавляем ML комментарий, если он не был добавлен автоматически
                from datetime import datetime
                ml_comment = (
                    f"🤖 <b>Автоматическая классификация</b>\n"
                    f"📂 Категория: {ml_category}\n"
                    f"🎯 Уверенность: {ml_confidence:.2f}\n"
                    f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                )
                await issue_service.okdesk_service.add_comment_to_issue(issue_id, ml_comment)
            
            # Загружаем медиафайлы как комментарии
            if media_files:
                media_comment = f"📎 <b>Прикрепленные файлы от пользователя</b>\n"
                for i, media in enumerate(media_files, 1):
                    media_comment += f"{i}. {media['caption']}\n"
                
                await issue_service.okdesk_service.add_comment_to_issue(issue_id, media_comment)
            
            # Создаем клавиатуру для обратной связи (если есть ID классификации)
            keyboard = None
            if classification_id:
                from handlers.feedback_handlers import create_feedback_keyboard
                keyboard = create_feedback_keyboard(classification_id)
            
            success_text = (
                f"✅ <b>Заявка создана успешно!</b>\n\n"
                f"🎫 <b>ID заявки:</b> #{issue_id}\n"
                f"📝 <b>Описание:</b> {description[:100]}{'...' if len(description) > 100 else ''}\n"
            )
            
            if media_files:
                success_text += f"📎 <b>Файлов:</b> {len(media_files)}\n"
            
            success_text += f"\n📧 Вы получите уведомления об изменениях статуса заявки."
            
            # Добавляем заявку в мониторинг комментариев
            try:
                await db.add_user_issue_for_monitoring(issue_id, callback.from_user.id)
                logger.info(f"Заявка {issue_id} добавлена в мониторинг для пользователя {callback.from_user.id}")
            except Exception as e:
                logger.error(f"Ошибка добавления заявки в мониторинг: {e}")
            
            # Создаем простую клавиатуру без ML обратной связи
            main_buttons = [
                [InlineKeyboardButton(text="🎫 Создать еще заявку", callback_data="create_issue")],
                [InlineKeyboardButton(text="🔙 В главное меню", callback_data="menu")]
            ]
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=main_buttons)
            
            # Отправляем уведомление пользователю
            await callback.message.edit_text(
                success_text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            
            # Отправляем уведомление админам о классификации
            if classification_id and ml_category and ml_category != "Не определена":
                try:
                    from services.admin_service import get_admin_service
                    admin_service = get_admin_service()
                    
                    if admin_service:
                        await admin_service.notify_classification(
                            issue_id=issue_id,
                            title=title,
                            description=description,
                            predicted_category=ml_category,
                            confidence=ml_confidence,
                            classification_id=classification_id,
                            user_id=callback.from_user.id
                        )
                        logger.info(f"Уведомление о классификации отправлено админам для заявки {issue_id}")
                    else:
                        logger.warning("Сервис админов не инициализирован")
                        
                except Exception as e:
                    logger.error(f"Ошибка отправки уведомления админам: {e}")
        else:
            await callback.message.edit_text(
                "❌ Не удалось создать заявку. Попробуйте позже или обратитесь к администратору.",
                reply_markup=get_back_to_menu_keyboard()
            )
        
    except Exception as e:
        logger.error(f"Ошибка создания заявки: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка при создании заявки: {str(e)}",
            reply_markup=get_back_to_menu_keyboard()
        )
    
    await state.clear()

@router.callback_query(F.data == "cancel_create_issue")
async def cancel_issue_creation(callback: CallbackQuery, state: FSMContext):
    """Отмена создания заявки"""
    await callback.answer()
    await callback.message.edit_text(
        "❌ Создание заявки отменено.",
        reply_markup=get_back_to_menu_keyboard()
    )
    await state.clear()

@router.message(Command("quick_issue"))
async def cmd_quick_issue(message: Message):
    """Быстрое создание заявки через команду"""
    
    user = db.get_user(message.from_user.id)
    if not user or not user.is_registered:
        await message.answer(
            "❌ Вы не зарегистрированы в системе или регистрация не завершена.\n"
            "Используйте /start для регистрации."
        )
        return
    
    # Получаем описание из команды
    command_parts = message.text.split(' ', 1)
    if len(command_parts) < 2:
        await message.answer(
            "⚡ <b>Быстрое создание заявки</b>\n\n"
            "Используйте команду:\n"
            "<code>/quick_issue Описание проблемы</code>\n\n"
            "💡 <i>Пример:</i>\n"
            "<code>/quick_issue Принтер не печатает документы</code>",
            parse_mode="HTML"
        )
        return
    
    description = command_parts[1].strip()
    
    if len(description) < 10:
        await message.answer(
            "❌ Описание слишком короткое. Минимум 10 символов.\n"
            "Попробуйте: <code>/quick_issue Более подробное описание проблемы</code>",
            parse_mode="HTML"
        )
        return
    
    # Показываем процесс
    processing_msg = await message.answer("🤖 Создаю заявку с ML классификацией...")
    
    try:
        # Получаем сервис заявок
        issue_service = get_issue_service()
        if not issue_service:
            await processing_msg.edit_text("❌ Сервис заявок недоступен. Обратитесь к администратору.")
            return
        
        # Генерируем краткий заголовок, отличающийся от описания
        words = description.split()
        if len(words) <= 4:
            # Если описание очень короткое, используем его полностью
            title = description.strip()
        else:
            # Создаем краткий заголовок из первых 3-4 слов без многоточия
            # чтобы избежать дублирования с описанием
            title = " ".join(words[:4])
            if len(title) > 40:
                title = title[:37] + "..."
        
        # Создаем заявку
        issue_id = await issue_service.create_issue_with_classification(
            title=title,
            description=description,
            contact_id=user.okdesk_contact_id,  # Используем реальный contact_id пользователя
            company_id=user.okdesk_company_id,  # Используем реальный company_id пользователя
            user_id=message.from_user.id
        )
        
        if issue_id:
            # ML классификация
            try:
                from services.ml_service import ml_service
                result = await ml_service.classify_issue(description, user_id=message.from_user.id)
                category = result.get('category', 'Другое')
                confidence = result.get('confidence', 0.0)
                
                # Добавляем ML комментарий
                from datetime import datetime
                ml_comment = (
                    f"🤖 <b>Быстрая автоматическая классификация</b>\n"
                    f"📂 Категория: {category}\n"
                    f"🎯 Уверенность: {confidence:.2f}\n"
                    f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                )
                await issue_service.okdesk_service.add_comment_to_issue(issue_id, ml_comment)
                
                success_text = (
                    f"⚡ <b>Заявка создана успешно!</b>\n\n"
                    f"🎫 <b>ID заявки:</b> #{issue_id}\n"
                    f"🤖 <b>Категория:</b> {category}\n"
                    f"📝 <b>Описание:</b> {description[:100]}{'...' if len(description) > 100 else ''}"
                )
                
            except Exception as e:
                logger.error(f"Ошибка ML в быстрой заявке: {e}")
                success_text = (
                    f"⚡ <b>Заявка создана!</b>\n\n"
                    f"🎫 <b>ID заявки:</b> #{issue_id}\n"
                    f"📝 <b>Описание:</b> {description[:100]}{'...' if len(description) > 100 else ''}\n"
                    f"⚠️ ML классификация недоступна"
                )
            
            # Добавляем заявку в мониторинг комментариев
            try:
                await db.add_user_issue_for_monitoring(issue_id, message.from_user.id)
                logger.info(f"Быстрая заявка {issue_id} добавлена в мониторинг для пользователя {message.from_user.id}")
            except Exception as e:
                logger.error(f"Ошибка добавления быстрой заявки в мониторинг: {e}")
            
            await processing_msg.edit_text(success_text, parse_mode="HTML")
        else:
            await processing_msg.edit_text("❌ Не удалось создать заявку. Попробуйте позже.")
            
    except Exception as e:
        logger.error(f"Ошибка быстрого создания заявки: {e}")
        await processing_msg.edit_text(f"❌ Ошибка: {str(e)}")

# Экспортируем функцию для использования в main.py
start_issue_creation = start_issue_creation_callback
