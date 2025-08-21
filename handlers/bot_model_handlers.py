"""
Обработчики для bot_model ML функций
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from keyboards.admin_keyboards import get_admin_ml_keyboard, get_model_selection_keyboard
from services.ml_service import ml_service

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("bot_model"))
async def cmd_bot_model_info(message: Message):
    """Информация о bot_model"""
    user_id = message.from_user.id
    
    try:
        # Получаем статистику ML сервиса
        stats = ml_service.get_statistics()
        
        # Получаем информацию о bot_model
        classifier_stats = stats.get('classifier', {})
        bot_model_info = classifier_stats.get('bot_model', {})
        
        text = "🤖 **Информация о bot_model**\n\n"
        
        if bot_model_info.get('model_loaded', False):
            text += "✅ **Статус**: Модель загружена и активна\n\n"
            text += f"📊 **Характеристики модели**:\n"
            text += f"• Тип: {bot_model_info.get('model_type', 'Неизвестно')}\n"
            text += f"• Категорий: {bot_model_info.get('categories_count', 0)}\n"
            text += f"• Признаков: {bot_model_info.get('feature_count', 0)}\n"
            text += f"• Обучающих примеров: {bot_model_info.get('training_samples', 0)}\n"
            text += f"• Поддержка вероятностей: {'Да' if bot_model_info.get('supports_probability') else 'Нет'}\n\n"
            
            # Показываем примеры категорий
            example_categories = bot_model_info.get('example_categories', [])
            if example_categories:
                text += f"📋 **Примеры категорий** (показано {len(example_categories)} из {bot_model_info.get('categories_count', 0)}):\n"
                for i, category in enumerate(example_categories[:10], 1):
                    text += f"{i}. {category}\n"
                if bot_model_info.get('categories_count', 0) > 10:
                    text += f"... и ещё {bot_model_info.get('categories_count', 0) - 10} категорий\n"
        else:
            text += "❌ **Статус**: Модель не загружена\n\n"
            text += "⚠️ Возможные причины:\n"
            text += "• Отсутствуют файлы модели в папке bot_model/\n"
            text += "• Ошибка при загрузке векторизатора\n"
            text += "• Неверная структура файлов модели\n"
        
        # Показываем активную модель
        active_model = classifier_stats.get('active_model', 'Unknown')
        text += f"\n🎯 **Активная модель**: {active_model}\n"
        
        await message.answer(text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка в bot_model info: {e}")
        await message.answer("❌ Ошибка получения информации о bot_model")

@router.message(Command("test_bot_model"))
async def cmd_test_bot_model(message: Message):
    """Тестирование bot_model на примере"""
    user_id = message.from_user.id
    
    try:
        # Тестовые тексты
        test_texts = [
            "Компьютер не включается, горит красная лампочка",
            "Не могу войти в 1С, требует пароль",
            "Принтер печатает полосами, нужна диагностика",
            "Настройка Wi-Fi точки доступа в офисе",
            "Установка антивируса на рабочие станции"
        ]
        
        text = "🧪 **Тестирование bot_model**\n\n"
        
        for i, test_text in enumerate(test_texts, 1):
            try:
                # Классифицируем тестовый текст
                result = await ml_service.classify_issue(test_text, user_id)
                
                category = result.get('category', 'Неизвестно')
                confidence = result.get('confidence', 0.0)
                
                text += f"**Тест {i}**:\n"
                text += f"📝 Текст: _{test_text}_\n"
                text += f"🎯 Категория: **{category}**\n"
                text += f"📊 Уверенность: {confidence:.1%}\n\n"
                
            except Exception as e:
                text += f"**Тест {i}**: Ошибка - {str(e)}\n\n"
        
        await message.answer(text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка в test_bot_model: {e}")
        await message.answer("❌ Ошибка тестирования bot_model")

@router.callback_query(F.data == "toggle_bot_model")
async def toggle_bot_model(callback: CallbackQuery):
    """Переключение использования bot_model"""
    try:
        # Переключаем флаг использования bot_model
        current_state = ml_service.classifier.use_bot_model
        ml_service.classifier.use_bot_model = not current_state
        
        new_state = "включена" if ml_service.classifier.use_bot_model else "отключена"
        
        await callback.message.edit_text(
            f"🤖 bot_model {new_state}",
            reply_markup=get_admin_ml_keyboard()
        )
        
        await callback.answer(f"bot_model {new_state}")
        
    except Exception as e:
        logger.error(f"Ошибка переключения bot_model: {e}")
        await callback.answer("❌ Ошибка переключения")

@router.callback_query(F.data == "model_comparison")
async def model_comparison(callback: CallbackQuery):
    """Сравнение результатов разных моделей"""
    try:
        test_text = "Принтер Canon не печатает, мигает красная лампочка ошибки"
        
        # Получаем результаты от разных моделей
        results = {}
        
        # Тестируем bot_model
        if ml_service.classifier.bot_model_adapter and ml_service.classifier.bot_model_adapter.is_available():
            try:
                from ml.text_vectorizer import text_vectorizer
                vector = text_vectorizer.vectorize(test_text)
                features = vector.reshape(1, -1)
                category, confidence = ml_service.classifier.bot_model_adapter.predict(features)
                results['bot_model'] = (category, confidence)
            except Exception as e:
                results['bot_model'] = (f"Ошибка: {e}", 0.0)
        
        # Тестируем LightGBM
        if (ml_service.classifier.lgb_adapter and 
            hasattr(ml_service.classifier.lgb_adapter, 'model') and 
            ml_service.classifier.lgb_adapter.model):
            try:
                lgb_result = ml_service.classifier.lgb_adapter.predict(test_text)
                if lgb_result:
                    results['lightgbm'] = lgb_result
                else:
                    results['lightgbm'] = ("Нет результата", 0.0)
            except Exception as e:
                results['lightgbm'] = (f"Ошибка: {e}", 0.0)
        
        # Общий результат
        overall_result = await ml_service.classify_issue(test_text, callback.from_user.id)
        results['overall'] = (overall_result.get('category', 'Неизвестно'), overall_result.get('confidence', 0.0))
        
        # Формируем ответ
        text = "🔄 **Сравнение моделей**\n\n"
        text += f"📝 **Тестовый текст**:\n_{test_text}_\n\n"
        
        for model_name, (category, confidence) in results.items():
            model_display = {
                'bot_model': '🤖 bot_model',
                'lightgbm': '⚡ LightGBM',
                'overall': '🎯 Итоговый результат'
            }.get(model_name, model_name)
            
            text += f"**{model_display}**:\n"
            text += f"Категория: {category}\n"
            text += f"Уверенность: {confidence:.1%}\n\n"
        
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=get_admin_ml_keyboard())
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка сравнения моделей: {e}")
        await callback.answer("❌ Ошибка сравнения моделей")
