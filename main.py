"""
Okdesk CRM Telegram Bot
Бот для интеграции с системой управления заявками Okdesk
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers.main import router as main_router
from handlers.registration import router as registration_router
from services.issue_monitor import IssueStatusMonitor, set_monitor

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Главная функция запуска бота"""
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Инициализация мониторинга статусов заявок
    monitor = IssueStatusMonitor(bot)
    set_monitor(monitor)  # Устанавливаем глобальный экземпляр
    
    # Подключение роутеров с обработчиками
    dp.include_router(registration_router)  # Сначала регистрация
    dp.include_router(main_router)  # Потом основные функции
    
    logger.info("Бот запущен")
    
    try:
        # Запуск мониторинга в фоновом режиме
        monitor_task = asyncio.create_task(monitor.start_monitoring())
        
        # Запуск polling
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при работе бота: {e}")
    finally:
        # Остановка мониторинга
        if 'monitor_task' in locals():
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
        
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
