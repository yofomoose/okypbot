"""
Обработчики команд администратора для просмотра статистики ML
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.types import Message
from services.ml_stats_service import ml_stats_service
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("mlstats"))
async def show_ml_stats(message: Message):
    """Показывает статистику ML (только для администраторов)"""
    # Здесь можно добавить проверку на права администратора
    user_id = message.from_user.id
    
    try:
        # Получаем общую статистику модели
        model_stats = await ml_stats_service.get_model_accuracy(days=30)
        
        # Получаем статистику пользователя
        user_stats = await ml_stats_service.get_user_stats(user_id)
        
        stats_text = (
            "📊 <b>Статистика ML классификации</b>\n\n"
            "🤖 <b>Модель (за 30 дней):</b>\n"
            f"• Точность: {model_stats['accuracy']:.2%}\n"
            f"• Всего классификаций: {model_stats['total']}\n"
            f"• Правильных: {model_stats['correct']}\n\n"
            "👤 <b>Ваша статистика:</b>\n"
            f"• Всего ваших заявок: {user_stats['total_classifications']}\n"
            f"• Дано оценок: {user_stats['feedback_given']}\n"
            f"• Процент оценок: {user_stats['feedback_rate']:.1%}\n"
        )
        
        if user_stats['user_accuracy'] is not None:
            stats_text += f"• Точность для вас: {user_stats['user_accuracy']:.1%}\n"
        
        # Добавляем топ-3 категории по точности
        category_stats = model_stats.get('category_stats', {})
        if category_stats:
            sorted_cats = sorted(
                category_stats.items(), 
                key=lambda x: x[1]['accuracy'], 
                reverse=True
            )[:3]
            
            stats_text += "\n🎯 <b>Топ-3 категории по точности:</b>\n"
            for i, (cat, stats) in enumerate(sorted_cats, 1):
                stats_text += f"{i}. {cat}: {stats['accuracy']:.1%} ({stats['correct']}/{stats['total']})\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_mlstats")],
            [InlineKeyboardButton(text="📈 Детальная статистика", callback_data="detailed_mlstats")]
        ])
        
        await message.answer(stats_text, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        await message.answer("❌ Ошибка получения статистики ML")

@router.callback_query(F.data == "refresh_mlstats")
async def refresh_ml_stats(callback: CallbackQuery):
    """Обновляет статистику ML"""
    await callback.answer("Обновляю статистику...")
    
    # Повторно вызываем функцию показа статистики
    await show_ml_stats(callback.message)

@router.callback_query(F.data == "detailed_mlstats")
async def show_detailed_stats(callback: CallbackQuery):
    """Показывает детальную статистику"""
    await callback.answer()
    
    try:
        # Получаем статистику за разные периоды
        stats_7d = await ml_stats_service.get_model_accuracy(days=7)
        stats_30d = await ml_stats_service.get_model_accuracy(days=30)
        stats_90d = await ml_stats_service.get_model_accuracy(days=90)
        
        detailed_text = (
            "📈 <b>Детальная статистика ML</b>\n\n"
            "📅 <b>По периодам:</b>\n"
            f"• 7 дней: {stats_7d['accuracy']:.2%} ({stats_7d['correct']}/{stats_7d['total']})\n"
            f"• 30 дней: {stats_30d['accuracy']:.2%} ({stats_30d['correct']}/{stats_30d['total']})\n"
            f"• 90 дней: {stats_90d['accuracy']:.2%} ({stats_90d['correct']}/{stats_90d['total']})\n\n"
        )
        
        # Показываем статистику по всем категориям (топ-10)
        category_stats = stats_30d.get('category_stats', {})
        if category_stats:
            sorted_cats = sorted(
                category_stats.items(), 
                key=lambda x: x[1]['total'], 
                reverse=True
            )[:10]
            
            detailed_text += "📊 <b>Топ-10 категорий по количеству:</b>\n"
            for i, (cat, stats) in enumerate(sorted_cats, 1):
                detailed_text += (
                    f"{i}. <code>{cat[:25]}{'...' if len(cat) > 25 else ''}</code>\n"
                    f"   Точность: {stats['accuracy']:.1%} ({stats['correct']}/{stats['total']})\n"
                )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="refresh_mlstats")]
        ])
        
        await callback.message.edit_text(detailed_text, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка получения детальной статистики: {e}")
        await callback.answer("❌ Ошибка получения статистики")

@router.message(Command("training_data"))
async def show_training_data_info(message: Message):
    """Показывает информацию о данных для обучения"""
    try:
        training_data = await ml_stats_service.get_training_data(limit=100)
        
        if not training_data:
            await message.answer("📭 Нет данных для обучения")
            return
        
        # Анализируем данные
        total_records = len(training_data)
        corrections = sum(1 for record in training_data if record['is_correction'])
        
        # Группируем по категориям
        categories = {}
        for record in training_data:
            cat = record['category']
            if cat not in categories:
                categories[cat] = {'total': 0, 'corrections': 0}
            categories[cat]['total'] += 1
            if record['is_correction']:
                categories[cat]['corrections'] += 1
        
        info_text = (
            "🎓 <b>Данные для обучения</b>\n\n"
            f"📊 Всего записей: {total_records}\n"
            f"🔧 Исправлений: {corrections}\n"
            f"✅ Подтверждений: {total_records - corrections}\n"
            f"📈 Процент исправлений: {corrections / total_records:.1%}\n\n"
        )
        
        # Топ категорий
        sorted_cats = sorted(categories.items(), key=lambda x: x[1]['total'], reverse=True)[:5]
        info_text += "🏆 <b>Топ-5 категорий:</b>\n"
        for cat, stats in sorted_cats:
            info_text += f"• {cat}: {stats['total']} ({stats['corrections']} исправлений)\n"
        
        await message.answer(info_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка получения данных для обучения: {e}")
        await message.answer("❌ Ошибка получения данных для обучения")
