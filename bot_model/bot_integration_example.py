# Пример интеграции с Telegram ботом
# Файл: bot_handler.py

import asyncio
import numpy as np
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Импортируем нашу систему (убедитесь что файлы в той же папке)
try:
    from efficient_bot_model import EfficientBotModel, BotIntegration
except ImportError:
    print("❌ Не найден файл efficient_bot_model.py")
    print("Убедитесь что все файлы находятся в одной папке")
    exit(1)

# Инициализация модели
print("🤖 Инициализация модели...")
model = EfficientBotModel("bot_model")
model.load_model()
bot_integration = BotIntegration(model)
print("✅ Модель готова к работе!")

# ID админов (замените на реальные)
ADMIN_IDS = [12345678, 87654321]  # Ваши Telegram ID

# Здесь должен быть ваш векторизатор текста
def vectorize_text(text: str) -> np.ndarray:
    '''
    КРИТИЧЕСКИ ВАЖНО: Замените на ваш метод векторизации!
    Должен возвращать numpy array размерности 384
    '''
    # ПРИМЕРЫ ЗАМЕНЫ:
    # return tfidf_vectorizer.transform([text]).toarray()[0]
    # return bert_model.encode(text)
    # return word2vec_model.get_sentence_vector(text)
    
    # ВРЕМЕННАЯ ЗАГЛУШКА (ОБЯЗАТЕЛЬНО ЗАМЕНИТЕ!)
    print(f"⚠️ ИСПОЛЬЗУЕТСЯ ЗАГЛУШКА! Замените vectorize_text() на реальную векторизацию")
    return np.random.random(384)

async def handle_user_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''Обработка заявки пользователя'''
    
    user_id = str(update.effective_user.id)
    text = update.message.text
    
    try:
        # Векторизуем текст
        features = vectorize_text(text)
        
        # Получаем предсказание
        result = await bot_integration.process_user_request(user_id, text, features)
        
        # Отправляем ответ пользователю
        if result['needs_review']:
            response = f"📝 Ваша заявка получена!\n"
            response += f"🤖 Предварительная категория: **{result['category']}**\n"
            response += f"⏳ Заявка отправлена на проверку администратору"
            
            # Отправляем админу на проверку
            await send_to_admin_review(context, user_id, text, result)
            
        else:
            response = f"✅ Ваша заявка обработана!\n"
            response += f"📂 Категория: **{result['category']}**\n"
            response += f"🎯 Уверенность: {result['confidence']:.1%}"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке заявки. Попробуйте позже."
        )
        print(f"Ошибка обработки: {e}")

async def send_to_admin_review(context, user_id: str, text: str, prediction_result: dict):
    '''Отправка заявки админу на проверку'''
    
    admin_message = f'''🔍 **ЗАЯВКА ТРЕБУЕТ ПРОВЕРКИ**

👤 Пользователь: `{user_id}`
📝 Текст заявки:
_{text}_

🤖 Предсказание: **{prediction_result['category']}**
📊 Уверенность: {prediction_result['confidence']:.1%}

❓ Правильно ли определена категория?
Ответьте: `/correct {user_id} {prediction_result['category']}` - если верно
Или: `/fix {user_id} "{prediction_result['category']}" "ПРАВИЛЬНАЯ_КАТЕГОРИЯ"` - если неверно
'''
    
    # Отправляем всем админам
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id, 
                text=admin_message, 
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"Не удалось отправить админу {admin_id}: {e}")

async def handle_admin_correction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''Обработка исправления от админа'''
    
    # Проверяем права админа
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Недостаточно прав")
        return
    
    try:
        args = context.args
        if len(args) < 3:
            await update.message.reply_text(
                "❌ Неверный формат. Используйте:\n"
                "`/fix USER_ID \"PREDICTED_CATEGORY\" \"CORRECT_CATEGORY\"`",
                parse_mode='Markdown'
            )
            return
        
        user_id = args[0]
        predicted_category = args[1].strip('"')
        correct_category = args[2].strip('"')
        
        # В реальном боте здесь нужно получить исходный текст из базы
        # Для примера используем заглушку
        original_text = "Пример текста заявки"  # TODO: Получить из БД
        
        features = vectorize_text(original_text)
        
        # Добавляем исправление в модель
        await bot_integration.admin_correction(
            user_id=user_id,
            original_text=original_text,
            features=features,
            predicted_category=predicted_category,
            correct_category=correct_category
        )
        
        await update.message.reply_text(
            f"✅ Исправление добавлено:\n"
            f"{predicted_category} → **{correct_category}**\n"
            f"Модель будет обновлена автоматически.",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''Команда /stats для просмотра статистики'''
    
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Недостаточно прав")
        return
    
    try:
        stats = model.get_feedback_stats()
        
        stats_text = f'''📊 **СТАТИСТИКА МОДЕЛИ**

📝 Всего обратной связи: {stats['total_feedback']}
⏳ Ожидает обновления: {stats['pending_corrections']}

📋 **Топ категории исправлений:**
'''
        
        # ИСПРАВЛЕННАЯ обработка статистики
        if 'category_distribution' in stats and stats['category_distribution']:
            items = list(stats['category_distribution'].items())[:10]
            for cat, count in items:
                stats_text += f"• {cat}: {count}\n"
        else:
            stats_text += "Пока нет данных\n"
        
        if len(stats.get('category_distribution', {})) > 10:
            remaining = len(stats['category_distribution']) - 10
            stats_text += f"... и ещё {remaining} категорий\n"
        
        stats_text += f"\n🔄 **Последние обновления:** {len(stats.get('recent_updates', []))}"
        
        await update.message.reply_text(stats_text, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка получения статистики: {e}")

# Команды бота
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''Команда /start'''
    await update.message.reply_text(
        "👋 Привет! Отправьте мне вашу заявку, и я определю её категорию.\n"
        "Просто напишите ваш вопрос или описание проблемы."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''Команда /help'''
    help_text = '''🤖 **ПОМОЩЬ**

**Для пользователей:**
• Просто отправьте вашу заявку текстом
• Бот автоматически определит категорию

**Для админов:**
• `/stats` - статистика модели
• `/fix USER_ID "PREDICTED" "CORRECT"` - исправить категорию
'''
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

def main():
    '''Запуск бота'''
    
    # ВАЖНО: Замените на ваш реальный токен!
    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ УСТАНОВИТЕ РЕАЛЬНЫЙ ТОКЕН БОТА!")
        print("1. Напишите @BotFather в Telegram")
        print("2. Создайте бота командой /newbot")
        print("3. Скопируйте токен и замените BOT_TOKEN")
        return
    
    print("🚀 Запуск Telegram бота...")
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("fix", handle_admin_correction))
    
    # Обработчик всех текстовых сообщений
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_request)
    )
    
    print("✅ Бот запущен и готов к работе!")
    print("📋 Доступные команды:")
    print("  /start - приветствие")
    print("  /help - помощь")
    print("  /stats - статистика (админы)")
    print("  /fix - исправить категорию (админы)")
    print("\n⚠️ НЕ ЗАБУДЬТЕ ЗАМЕНИТЬ vectorize_text() на реальную векторизацию!")
    
    # Запускаем polling
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
