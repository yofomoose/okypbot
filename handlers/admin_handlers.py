"""
Обработчики для администраторов ML системы
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_IDS
from keyboards.admin_keyboards import (
    get_ml_feedback_keyboard,
    get_category_groups_keyboard, 
    get_category_subcategories_keyboard,
    update_category_groups_from_ml,
    get_admin_ml_keyboard,
    get_model_selection_keyboard
)

logger = logging.getLogger(__name__)

router = Router()

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь админом"""
    return user_id in ADMIN_IDS

@router.callback_query(F.data.startswith("admin_correct_"))
async def admin_confirm_correct(callback: CallbackQuery):
    """Админ подтверждает правильность классификации"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
        
    try:
        classification_id = int(callback.data.split("_")[2])
        
        # Сохраняем положительную обратную связь в БД
        from services.ml_stats_service import MLStatsService
        ml_stats = MLStatsService()
        
        success = await ml_stats.save_feedback(
            classification_id=classification_id,
            user_id=callback.from_user.id,
            is_correct=True,
            feedback_type="admin_confirmation"
        )
        
        if success:
            # Обновляем сообщение
            updated_text = callback.message.text + f"\n\n✅ <b>Подтверждено админом</b> @{callback.from_user.username or callback.from_user.id}"
            
            # Убираем кнопки подтверждения, оставляем только ссылку на заявку
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="📋 Открыть заявку в Okdesk", 
                    url=callback.message.reply_markup.inline_keyboard[1][0].url
                )]
            ])
            
            await callback.message.edit_text(
                updated_text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            
            await callback.answer("✅ Классификация подтверждена. Модель обучается на этом примере.")
            
            # Запускаем обучение модели на положительном примере
            try:
                from services.ml_training_service import get_training_service
                training_service = get_training_service()
                if training_service:
                    await training_service.train_on_feedback(classification_id, is_correct=True)
            except Exception as e:
                logger.error(f"Ошибка обучения модели: {e}")
                
        else:
            await callback.answer("❌ Ошибка сохранения обратной связи", show_alert=True)
            
    except Exception as e:
        logger.error(f"Ошибка обработки подтверждения: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

@router.callback_query(F.data.startswith("admin_incorrect_"))
async def admin_mark_incorrect(callback: CallbackQuery):
    """Админ отмечает неправильность классификации"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
        
    try:
        classification_id = int(callback.data.split("_")[2])
        
        # Получаем данные классификации из БД
        from services.ml_stats_service import MLStatsService
        ml_stats = MLStatsService()
        
        classification_data = await ml_stats.get_classification(classification_id)
        if not classification_data:
            await callback.answer("❌ Классификация не найдена", show_alert=True)
            return
        
        # Обновляем категории из ML сервиса
        try:
            from services.ml_service import ml_service
            update_category_groups_from_ml(ml_service)
        except Exception as e:
            logger.warning(f"Не удалось обновить категории: {e}")
        
        # Показываем интерфейс выбора правильной категории
        await show_category_groups(callback, classification_id, classification_data)
        
    except Exception as e:
        logger.error(f"Ошибка обработки отклонения: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

async def show_category_groups(callback: CallbackQuery, classification_id: int, classification_data: dict):
    """Показывает интерфейс выбора группы категорий"""
    
    text = (
        f"❌ <b>Неправильная классификация</b>\n\n"
        f"📝 <b>Текст:</b> <i>{classification_data['text'][:100]}{'...' if len(classification_data['text']) > 100 else ''}</i>\n"
        f"🤖 <b>Предсказание:</b> {classification_data['predicted_category']}\n"
        f"📊 <b>Уверенность:</b> {classification_data['confidence']:.2%}\n\n"
        f"🎯 <b>Выберите правильную группу категорий:</b>"
    )
    
    keyboard = get_category_groups_keyboard(classification_id)
    
    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    await callback.answer("Выберите группу категорий")

@router.callback_query(F.data.startswith("admin_group_"))
async def admin_select_group(callback: CallbackQuery):
    """Админ выбирает группу категорий"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
        
    try:
        parts = callback.data.split("_")
        classification_id = int(parts[2])
        group_name = parts[3]
        
        # Получаем данные классификации
        from services.ml_stats_service import MLStatsService
        ml_stats = MLStatsService()
        
        classification_data = await ml_stats.get_classification(classification_id)
        if not classification_data:
            await callback.answer("❌ Классификация не найдена", show_alert=True)
            return
        
        # Показываем подкатегории выбранной группы
        await show_category_subcategories(callback, classification_id, group_name, classification_data)
        
    except Exception as e:
        logger.error(f"Ошибка выбора группы: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

async def show_category_subcategories(callback: CallbackQuery, classification_id: int, group_name: str, classification_data: dict):
    """Показывает подкатегории выбранной группы"""
    
    text = (
        f"❌ <b>Выбор правильной категории</b>\n\n"
        f"📝 <b>Текст:</b> <i>{classification_data['text'][:100]}{'...' if len(classification_data['text']) > 100 else ''}</i>\n"
        f"🤖 <b>Неправильно:</b> {classification_data['predicted_category']}\n\n"
        f"🎯 <b>Выберите правильную категорию:</b>"
    )
    
    keyboard = get_category_subcategories_keyboard(classification_id, group_name)
    
    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    await callback.answer(f"Категории группы {group_name}")

@router.callback_query(F.data.startswith("admin_groups_"))
async def admin_back_to_groups(callback: CallbackQuery):
    """Возврат к выбору групп категорий"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
        
    try:
        classification_id = int(callback.data.split("_")[2])
        
        # Получаем данные классификации
        from services.ml_stats_service import MLStatsService
        ml_stats = MLStatsService()
        
        classification_data = await ml_stats.get_classification(classification_id)
        if not classification_data:
            await callback.answer("❌ Классификация не найдена", show_alert=True)
            return
        
        await show_category_groups(callback, classification_id, classification_data)
        
    except Exception as e:
        logger.error(f"Ошибка возврата к группам: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

@router.callback_query(F.data.startswith("admin_cat_"))
async def admin_select_category(callback: CallbackQuery):
    """Админ выбирает правильную категорию из подкатегорий"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
        
    try:
        parts = callback.data.split("_")
        if len(parts) < 4:
            await callback.answer("❌ Неверный формат данных", show_alert=True)
            return
            
        classification_id = int(parts[2])
        category_id = "_".join(parts[3:])  # Может содержать подчеркивания
        
        # Получаем полное название категории по ID
        from keyboards.admin_keyboards import get_category_by_id
        category_name = get_category_by_id(category_id)
        
        # Сохраняем исправленную классификацию
        from services.ml_stats_service import MLStatsService
        ml_stats = MLStatsService()
        
        success = await ml_stats.save_feedback(
            classification_id=classification_id,
            user_id=callback.from_user.id,
            is_correct=False,
            correct_category=category_name,
            feedback_type="admin_correction"
        )
        
        if success:
            # Получаем данные заявки для обучения модели
            classification_data = await ml_stats.get_classification(classification_id)
            
            if classification_data and classification_data.get('text'):
                # Добавляем пример для обучения
                try:
                    from services.ml_training_service import MLTrainingService
                    training_service = MLTrainingService()
                    await training_service.add_training_example(
                        text=classification_data['text'],
                        category=category_name,
                        user_id=callback.from_user.id,
                        metadata={
                            'classification_id': classification_id,
                            'old_category': classification_data.get('predicted_category'),
                            'correction_type': 'admin_feedback'
                        }
                    )
                except Exception as e:
                    logger.error(f"Ошибка добавления примера для обучения: {e}")
            
            # Обновляем категорию в Okdesk если есть issue_id
            issue_id = classification_data.get('issue_id') if classification_data else None
            if issue_id:
                try:
                    from services.okdesk_service import get_issue_service
                    issue_service = get_issue_service()
                    if issue_service:
                        await update_okdesk_category(issue_service, issue_id, category_name)
                        
                        # Уведомляем других админов
                        from services.admin_service import get_admin_service
                        admin_service = get_admin_service()
                        if admin_service:
                            old_category = classification_data.get('predicted_category', 'Неизвестно')
                            await admin_service.notify_category_updated(
                                issue_id, old_category, category_name, callback.from_user.id
                            )
                        
                except Exception as e:
                    logger.error(f"Ошибка обновления категории в Okdesk: {e}")
            
            # Подтверждение успешного сохранения
            success_text = (
                f"✅ <b>Категория исправлена!</b>\n\n"
                f"🎯 <b>Новая категория:</b> {category_name}\n"
                f"📊 <b>Данные сохранены для обучения модели</b>"
            )
            
            if issue_id:
                success_text += f"\n🔗 <b>Заявка Okdesk #{issue_id} обновлена</b>"
            
            await callback.message.edit_text(
                success_text,
                parse_mode="HTML"
            )
            await callback.answer("✅ Категория успешно исправлена!")
            
        else:
            await callback.answer("❌ Ошибка сохранения", show_alert=True)
            
    except Exception as e:
        logger.error(f"Ошибка выбора категории: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

@router.callback_query(F.data.startswith("admin_cancel_"))
async def admin_cancel_selection(callback: CallbackQuery):
    """Отмена выбора категории"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    await callback.message.edit_text(
        "❌ Выбор категории отменен",
        parse_mode="HTML"
    )
    await callback.answer("Операция отменена")

async def update_okdesk_category(issue_service, issue_id: int, category: str):
    """Обновляет категорию заявки в Okdesk через комментарий"""
    try:
        comment_text = (
            f"🔄 <b>Категория заявки обновлена администратором</b>\n\n"
            f"🎯 <b>Новая категория:</b> {category}\n"
            f"🤖 Обновлено системой ML классификации"
        )
        
        await issue_service.okdesk_service.add_comment_to_issue(
            issue_id, comment_text, is_public=False
        )
        
        logger.info(f"Комментарий с новой категорией добавлен к заявке {issue_id}")
        
    except Exception as e:
        logger.error(f"Ошибка добавления комментария с категорией: {e}")
        raise

# Новые обработчики для bot_model
@router.callback_query(F.data == "ml_admin_panel")
async def ml_admin_panel(callback: CallbackQuery):
    """Панель управления ML моделями"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    try:
        from services.ml_service import ml_service
        stats = ml_service.get_statistics()
        classifier_stats = stats.get('classifier', {})
        
        text = "🎛️ **Панель управления ML**\n\n"
        text += f"🤖 **Активная модель**: {classifier_stats.get('active_model', 'Unknown')}\n"
        
        # Статус моделей
        if classifier_stats.get('has_bot_model', False):
            text += "✅ bot_model: Загружена\n"
        else:
            text += "❌ bot_model: Не загружена\n"
            
        if classifier_stats.get('has_lgb_model', False):
            text += "✅ LightGBM: Загружена\n"
        else:
            text += "❌ LightGBM: Не загружена\n"
        
        text += f"\n📊 **Статистика**:\n"
        text += f"• Размер кеша: {classifier_stats.get('cache_size', 0)}\n"
        text += f"• Исправлений: {classifier_stats.get('user_corrections', 0)}\n"
        
        await callback.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_admin_ml_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в ml_admin_panel: {e}")
        await callback.answer("❌ Ошибка получения данных")

@router.callback_query(F.data == "bot_model_info")
async def bot_model_info_callback(callback: CallbackQuery):
    """Информация о bot_model через callback"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    try:
        from handlers.bot_model_handlers import cmd_bot_model_info
        # Создаем объект Message из callback для совместимости
        await cmd_bot_model_info(callback.message)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в bot_model_info_callback: {e}")
        await callback.answer("❌ Ошибка получения информации")

@router.callback_query(F.data == "test_bot_model")
async def test_bot_model_callback(callback: CallbackQuery):
    """Тестирование bot_model через callback"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    try:
        from handlers.bot_model_handlers import cmd_test_bot_model
        # Создаем объект Message из callback для совместимости
        await cmd_test_bot_model(callback.message)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в test_bot_model_callback: {e}")
        await callback.answer("❌ Ошибка тестирования")
