"""
Обработчики для сбора обратной связи по ML классификации
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


from services.ml_stats_service import ml_stats_service
import logging

logger = logging.getLogger(__name__)
router = Router()

class FeedbackStates(StatesGroup):
    waiting_for_category_correction = State()
    waiting_for_comment = State()

@router.callback_query(F.data.startswith("feedback_"))
async def handle_classification_feedback(callback: CallbackQuery, state: FSMContext):
    """Обработка обратной связи по классификации"""
    await callback.answer()
    
    data_parts = callback.data.split("_")
    if len(data_parts) < 3:
        await callback.message.edit_text("❌ Ошибка в данных обратной связи")
        return
    
    action = data_parts[1]  # correct/incorrect
    classification_id = int(data_parts[2])
    
    user_id = callback.from_user.id
    
    if action == "correct":
        # Пользователь подтвердил правильность классификации
        success = await ml_stats_service.save_user_feedback(
            classification_id=classification_id,
            user_id=user_id,
            telegram_user_id=user_id,
            is_correct=True
        )
        
        if success:
            await callback.message.edit_text(
                "✅ <b>Спасибо за обратную связь!</b>\n\n"
                "Вы подтвердили, что классификация была правильной.\n"
                "Это поможет улучшить точность модели.",
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text("❌ Ошибка сохранения обратной связи")
    
    elif action == "incorrect":
        # Пользователь указал на неправильную классификацию
        await state.update_data(classification_id=classification_id)
        await state.set_state(FeedbackStates.waiting_for_category_correction)
        
        await callback.message.edit_text(
            "🔧 <b>Исправление классификации</b>\n\n"
            "Пожалуйста, укажите правильную категорию для вашей заявки.\n"
            "Напишите название категории:",
            parse_mode="HTML"
        )

@router.message(FeedbackStates.waiting_for_category_correction)
async def receive_category_correction(message, state: FSMContext):
    """Получение правильной категории от пользователя"""
    data = await state.get_data()
    classification_id = data.get('classification_id')
    
    suggested_category = message.text.strip()
    
    # Сохраняем исправление
    success = await ml_stats_service.save_user_feedback(
        classification_id=classification_id,
        user_id=message.from_user.id,
        telegram_user_id=message.from_user.id,
        is_correct=False,
        suggested_category=suggested_category
    )
    
    if success:
        # Предлагаем добавить комментарий
        await state.update_data(suggested_category=suggested_category)
        await state.set_state(FeedbackStates.waiting_for_comment)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Пропустить комментарий", callback_data=f"skip_comment_{classification_id}")]
        ])
        
        await message.answer(
            f"✅ <b>Категория исправлена на:</b> {suggested_category}\n\n"
            "📝 Хотите добавить комментарий для улучшения классификации?\n"
            "Опишите, что помогло бы правильно определить категорию:",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await message.answer("❌ Ошибка сохранения исправления")
        await state.clear()

@router.message(FeedbackStates.waiting_for_comment)
async def receive_feedback_comment(message, state: FSMContext):
    """Получение комментария от пользователя"""
    data = await state.get_data()
    classification_id = data.get('classification_id')
    suggested_category = data.get('suggested_category')
    
    comment = message.text.strip()
    
    # Обновляем обратную связь с комментарием
    success = await ml_stats_service.save_user_feedback(
        classification_id=classification_id,
        user_id=message.from_user.id,
        telegram_user_id=message.from_user.id,
        is_correct=False,
        suggested_category=suggested_category,
        comment=comment
    )
    
    if success:
        await message.answer(
            "✅ <b>Спасибо за подробную обратную связь!</b>\n\n"
            "Ваши исправления и комментарии помогут улучшить точность модели классификации.\n\n"
            "🎯 <b>Что было сохранено:</b>\n"
            f"• Правильная категория: {suggested_category}\n"
            f"• Комментарий: {comment[:100]}{'...' if len(comment) > 100 else ''}",
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Ошибка сохранения комментария")
    
    await state.clear()

@router.callback_query(F.data.startswith("skip_comment_"))
async def skip_comment(callback: CallbackQuery, state: FSMContext):
    """Пропуск комментария"""
    await callback.answer()
    
    await callback.message.edit_text(
        "✅ <b>Обратная связь сохранена!</b>\n\n"
        "Спасибо за исправление категории. "
        "Это поможет улучшить точность модели.",
        parse_mode="HTML"
    )
    
    await state.clear()

def create_feedback_keyboard(classification_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру для сбора обратной связи"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Правильно", 
                callback_data=f"feedback_correct_{classification_id}"
            ),
            InlineKeyboardButton(
                text="❌ Неправильно", 
                callback_data=f"feedback_incorrect_{classification_id}"
            )
        ]
    ])
