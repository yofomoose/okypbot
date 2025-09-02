"""
Okdesk CRM Telegram Bot
Бот для интеграции с системой управления заявками Okdesk
"""

import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, WEBHOOK_ENABLED, WEBHOOK_HOST, WEBHOOK_PORT
from handlers import setup_routers
from services.issue_monitor import IssueStatusMonitor, set_monitor

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_webhook_server():
    """Запуск webhook сервера"""
    try:
        import uvicorn
        from services.webhook_server import app as webhook_app
        
        config = uvicorn.Config(
            webhook_app, 
            host=WEBHOOK_HOST, 
            port=WEBHOOK_PORT,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    except ImportError:
        logger.error("FastAPI/uvicorn не установлены. Установите: pip install fastapi uvicorn")
        raise

async def main():
    """Главная функция запуска бота 123"""
    # Инициализация БД
    try:
        # Импортируем модели перед инициализацией БД
        from ml.models.tables import User, Classification, TrainingExample
        from ml.models.stats import UsageStats, ModelStats
        from ml.models.feedback import UserFeedback
        
        from config.db_config import init_database
        init_database()
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.warning(f"Не удалось инициализировать БД: {e}")
    
    # Инициализация бота и диспетчера - ПРОСТАЯ ВЕРСИЯ БЕЗ AioHTTPSession
    logger.info("Инициализация бота...")
    bot = Bot(token=BOT_TOKEN)
    logger.info("✅ Бот инициализирован успешно")

    dp = Dispatcher(storage=MemoryStorage())
    
    # Инициализация ML сервиса
    try:
        from services.ml_service import ml_service
        await ml_service.initialize()
        logger.info("ML сервис инициализирован")
    except ImportError:
        logger.warning("ML библиотеки не установлены, ML функции недоступны")
    except Exception as e:
        logger.error(f"Ошибка инициализации ML сервиса: {e}")
    
    # Инициализация мониторинга статусов заявок
    monitor = IssueStatusMonitor(bot)
    set_monitor(monitor)  # Устанавливаем глобальный экземпляр
    
    # Инициализация Okdesk сервиса
    try:
        from services.okdesk_service import initialize_issue_service
        from config import OKDESK_API_TOKEN, OKDESK_BASE_URL
        
        # Инициализируем issue service с реальными токенами
        await initialize_issue_service(
            api_key=OKDESK_API_TOKEN,
            company_id="",  # Можно оставить пустым, если не используется
            base_url=OKDESK_BASE_URL
        )
        logger.info("Okdesk сервис инициализирован")
    except ImportError:
        logger.warning("Модуль okdesk_service недоступен")
    except Exception as e:
        logger.error(f"Ошибка инициализации Okdesk сервиса: {e}")

    # Инициализация мониторинга комментариев (ПОСЛЕ Okdesk сервиса)
    comment_monitor = None
    try:
        from services.comment_monitor_service import initialize_comment_monitor
        from services.okdesk_service import get_issue_service
        from database.models import db
        
        issue_service = get_issue_service()
        if issue_service:
            comment_monitor = initialize_comment_monitor(
                okdesk_service=issue_service.okdesk_service,
                bot=bot, 
                database_service=db
            )
            logger.info("Мониторинг комментариев инициализирован")
        else:
            logger.warning("Okdesk сервис недоступен, мониторинг комментариев отключен")
    except Exception as e:
        logger.error(f"Ошибка инициализации мониторинга комментариев: {e}")
    
    # Инициализация админ сервиса
    try:
        from services.admin_service import AdminNotificationService, set_admin_service
        admin_service = AdminNotificationService(bot)
        set_admin_service(admin_service)
        logger.info("Админ сервис инициализирован")
    except Exception as e:
        logger.error(f"Ошибка инициализации админ сервиса: {e}")
    
    # Инициализация сервиса обучения
    try:
        from services.ml_training_service import MLTrainingService, set_training_service
        training_service = MLTrainingService()
        set_training_service(training_service)
        logger.info("Сервис обучения ML инициализирован")
    except Exception as e:
        logger.error(f"Ошибка инициализации сервиса обучения: {e}")
    
    # Подключение всех роутеров из модуля handlers
    try:
        setup_routers(dp)
        logger.info("Все обработчики успешно подключены")
    except Exception as e:
        logger.error(f"Ошибка при подключении обработчиков: {e}")
    
    logger.info("Бот запущен")
    
    try:
        # Создаем задачи
        tasks = []
        
        # Основной polling бота
        bot_task = asyncio.create_task(dp.start_polling(bot))
        tasks.append(bot_task)
        
        # Webhook сервер (если включен)
        if WEBHOOK_ENABLED:
            try:
                webhook_task = asyncio.create_task(run_webhook_server())
                tasks.append(webhook_task)
                logger.info(f"Webhook сервер запущен на {WEBHOOK_HOST}:{WEBHOOK_PORT}")
            except Exception as e:
                logger.error(f"Ошибка запуска webhook сервера: {e}")
                logger.info("Продолжаем без webhook сервера")
        
        if not WEBHOOK_ENABLED:
            # Fallback: старый мониторинг (если webhook отключен)
            monitor_task = asyncio.create_task(monitor.start_monitoring())
            tasks.append(monitor_task)
            logger.info("Используется polling мониторинг (webhook отключен)")
            
            # Мониторинг комментариев (если инициализирован)
            if comment_monitor:
                comment_monitor_task = asyncio.create_task(comment_monitor.start_monitoring())
                tasks.append(comment_monitor_task)
                logger.info("Запущен мониторинг комментариев")
        
        # Ждем завершения любой из задач
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        
        # Отменяем оставшиеся задачи
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
                
    except Exception as e:
        logger.error(f"Ошибка при работе бота: {e}")
    finally:
        # Остановка всех задач мониторинга
        for task in tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
