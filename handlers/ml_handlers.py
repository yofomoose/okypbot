"""
Обработчики команд для ML функционала
"""

import logging
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from services.ml_service import ml_service
from database.models import get_user, update_user
from keyboards.main import get_back_to_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()

class MLStates(StatesGroup):
    waiting_for_issue_text = State()
    waiting_for_feedback = State()
    waiting_for_correct_category = State()

@router.message(Command("classify"))
async def cmd_classify(message: Message, state: FSMContext):
    """Команда для классификации заявки"""
    await message.answer(
        "🤖 <b>Классификация заявки</b>\n\n"
        "Отправьте текст заявки, и я определю её категорию:\n\n"
        "💡 <i>Чем подробнее описание, тем точнее классификация</i>",
        parse_mode="HTML",
        reply_markup=get_back_to_menu_keyboard()
    )
    await state.set_state(MLStates.waiting_for_issue_text)

@router.message(MLStates.waiting_for_issue_text)
async def process_issue_classification(message: Message, state: FSMContext):
    """Обработка текста заявки для классификации"""
    if not message.text or len(message.text.strip()) < 10:
        await message.answer(
            "❌ Текст заявки слишком короткий.\n"
            "Минимум 10 символов для качественной классификации.",
            reply_markup=get_back_to_menu_keyboard()
        )
        return
    
    # Показываем процесс
    processing_msg = await message.answer("🔄 Анализирую заявку...")
    
    try:
        # Классифицируем через ML сервис
        result = await ml_service.classify_issue(
            issue_text=message.text,
            user_id=message.from_user.id
        )
        
        if result['success']:
            category = result['category']
            confidence = result['confidence']
            recommendations = result.get('recommendations', [])
            
            # Формируем ответ
            response = f"🤖 <b>Результат классификации:</b>\n\n"
            response += f"📋 <b>Категория:</b> {category}\n"
            response += f"📊 <b>Уверенность:</b> {confidence:.1%}\n\n"
            
            # Добавляем индикатор уверенности
            if confidence >= 0.8:
                response += "✅ <b>Высокая уверенность</b>\n"
            elif confidence >= 0.6:
                response += "⚠️ <b>Средняя уверенность</b>\n"
            else:
                response += "❓ <b>Низкая уверенность</b>\n"
            
            # Добавляем рекомендации
            if recommendations:
                response += "\n💡 <b>Рекомендации:</b>\n"
                for rec in recommendations[:3]:  # Показываем не более 3
                    response += f"• {rec}\n"
            
            # Кнопки для обратной связи
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Верно",
                        callback_data=f"ml_feedback_correct_{confidence:.2f}"
                    ),
                    InlineKeyboardButton(
                        text="❌ Неверно",
                        callback_data="ml_feedback_wrong"
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
                        callback_data="back_to_menu"
                    )
                ]
            ])
            
            await processing_msg.edit_text(response, parse_mode="HTML", reply_markup=keyboard)
            
            # Сохраняем данные для возможной обратной связи
            await state.update_data(
                classified_text=message.text,
                predicted_category=category,
                confidence=confidence
            )
            await state.set_state(MLStates.waiting_for_feedback)
            
        else:
            error = result.get('error', 'Неизвестная ошибка')
            await processing_msg.edit_text(
                f"❌ Ошибка классификации: {error}",
                reply_markup=get_back_to_menu_keyboard()
            )
            await state.clear()
    
    except Exception as e:
        logger.error(f"Ошибка обработки классификации: {e}")
        await processing_msg.edit_text(
            "❌ Произошла ошибка при анализе заявки.",
            reply_markup=get_back_to_menu_keyboard()
        )
        await state.clear()

@router.callback_query(F.data.startswith("ml_feedback_correct"))
async def process_correct_feedback(callback: CallbackQuery, state: FSMContext):
    """Обработка подтверждения правильной классификации"""
    await callback.answer("✅ Спасибо за подтверждение!")
    
    data = await state.get_data()
    text = data.get('classified_text')
    category = data.get('predicted_category')
    
    if text and category:
        # Добавляем в обучающую выборку
        await ml_service.add_feedback(text, category, callback.from_user.id)
    
    await callback.message.edit_text(
        "✅ <b>Спасибо за обратную связь!</b>\n\n"
        "Ваше подтверждение поможет улучшить точность классификации.",
        parse_mode="HTML",
        reply_markup=get_back_to_menu_keyboard()
    )
    await state.clear()

@router.callback_query(F.data == "ml_feedback_wrong")
async def process_wrong_feedback(callback: CallbackQuery, state: FSMContext):
    """Обработка неправильной классификации"""
    await callback.answer()
    
    # Получаем доступные категории
    categories = ml_service.get_categories()
    
    # Создаем клавиатуру с категориями
    keyboard_rows = []
    for i in range(0, len(categories), 2):
        row = []
        for j in range(2):
            if i + j < len(categories):
                category = categories[i + j]
                row.append(InlineKeyboardButton(
                    text=category,
                    callback_data=f"ml_correct_cat_{i + j}"
                ))
        keyboard_rows.append(row)
    
    # Добавляем кнопку отмены
    keyboard_rows.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="ml_feedback_cancel")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    
    await callback.message.edit_text(
        "❓ <b>Выберите правильную категорию:</b>\n\n"
        "Это поможет улучшить качество классификации в будущем.",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
    # Сохраняем категории в состоянии
    await state.update_data(categories=categories)
    await state.set_state(MLStates.waiting_for_correct_category)

@router.callback_query(F.data.startswith("ml_correct_cat_"))
async def process_correct_category(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора правильной категории"""
    try:
        # Извлекаем индекс категории
        category_index = int(callback.data.split("_")[-1])
        
        data = await state.get_data()
        categories = data.get('categories', [])
        text = data.get('classified_text')
        
        if category_index < len(categories):
            correct_category = categories[category_index]
            
            if text:
                # Добавляем правильный пример в обучающую выборку
                success = await ml_service.add_feedback(text, correct_category, callback.from_user.id)
                
                if success:
                    await callback.answer("✅ Обратная связь добавлена!")
                    await callback.message.edit_text(
                        f"✅ <b>Спасибо за обратную связь!</b>\n\n"
                        f"Правильная категория: <b>{correct_category}</b>\n\n"
                        f"Эта информация поможет улучшить классификацию.",
                        parse_mode="HTML",
                        reply_markup=get_back_to_menu_keyboard()
                    )
                else:
                    await callback.answer("❌ Ошибка сохранения")
            else:
                await callback.answer("❌ Данные не найдены")
        else:
            await callback.answer("❌ Неверная категория")
    
    except Exception as e:
        logger.error(f"Ошибка обработки правильной категории: {e}")
        await callback.answer("❌ Произошла ошибка")
    
    await state.clear()

@router.callback_query(F.data == "ml_feedback_cancel")
async def cancel_feedback(callback: CallbackQuery, state: FSMContext):
    """Отмена обратной связи"""
    await callback.answer()
    await callback.message.edit_text(
        "❌ Обратная связь отменена.",
        reply_markup=get_back_to_menu_keyboard()
    )
    await state.clear()

@router.callback_query(F.data == "ml_stats")
async def show_ml_stats(callback: CallbackQuery):
    """Показ статистики ML"""
    await callback.answer()
    
    try:
        stats = ml_service.get_statistics()
        
        response = "📊 <b>Статистика машинного обучения</b>\n\n"
        
        # Статус сервиса
        service_status = stats.get('service_status', 'unknown')
        status_emoji = "🟢" if service_status == 'active' else "🔴"
        response += f"{status_emoji} <b>Статус:</b> {service_status}\n\n"
        
        # Информация о классификаторе
        classifier_info = stats.get('classifier', {})
        response += f"🤖 <b>Классификатор:</b>\n"
        response += f"• Обучен: {'✅' if classifier_info.get('is_trained') else '❌'}\n"
        response += f"• Категорий: {classifier_info.get('categories_count', 0)}\n"
        response += f"• ML доступен: {'✅' if classifier_info.get('ml_available') else '❌'}\n\n"
        
        # Статистика использования
        history_info = stats.get('history', {})
        if history_info:
            response += f"📈 <b>Использование:</b>\n"
            response += f"• Всего классификаций: {history_info.get('total_classifications', 0)}\n"
            response += f"• Средняя уверенность: {history_info.get('average_confidence', 0):.1%}\n\n"
            
            # Распределение по категориям
            distribution = history_info.get('category_distribution', {})
            if distribution:
                response += "📋 <b>Популярные категории:</b>\n"
                sorted_cats = sorted(distribution.items(), key=lambda x: x[1], reverse=True)
                for cat, count in sorted_cats[:5]:
                    response += f"• {cat}: {count}\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 В меню", callback_data="back_to_menu")]
        ])
        
        await callback.message.edit_text(response, parse_mode="HTML", reply_markup=keyboard)
    
    except Exception as e:
        logger.error(f"Ошибка получения статистики ML: {e}")
        await callback.message.edit_text(
            "❌ Ошибка получения статистики ML",
            reply_markup=get_back_to_menu_keyboard()
        )
