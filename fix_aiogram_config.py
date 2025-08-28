#!/usr/bin/env python3
"""
Скрипт для проверки версии aiogram и создания правильной конфигурации бота
"""

import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_aiogram_version():
    """Проверяет версию aiogram"""
    try:
        import aiogram
        version = aiogram.__version__
        logger.info(f"✅ aiogram версия: {version}")

        # Определяем версию
        major_version = int(version.split('.')[0])
        return major_version, version
    except ImportError:
        logger.error("❌ aiogram не установлен")
        return None, None

def create_bot_config(major_version):
    """Создает правильную конфигурацию бота для данной версии aiogram"""

    if major_version == 3:
        # Для aiogram 3.x
        config_content = '''    # Инициализация бота и диспетчера для aiogram 3.x
    from aiogram.client.session.aiohttp import AioHTTPSession
    import aiohttp

    # Создаем сессию с увеличенными таймаутами
    session = AioHTTPSession(
        timeout=aiohttp.ClientTimeout(total=30, connect=10, sock_read=10)
    )

    bot = Bot(token=BOT_TOKEN, session=session)
    dp = Dispatcher(storage=MemoryStorage())'''

    elif major_version == 2:
        # Для aiogram 2.x
        config_content = '''    # Инициализация бота и диспетчера для aiogram 2.x
    bot = Bot(token=BOT_TOKEN, timeout=30)
    dp = Dispatcher(bot, storage=MemoryStorage())'''

    else:
        # Для других версий
        config_content = '''    # Инициализация бота и диспетчера (универсальная версия)
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())'''

    return config_content

def update_main_py():
    """Обновляет main.py с правильной конфигурацией"""

    major_version, version = check_aiogram_version()
    if not major_version:
        return False

    config_content = create_bot_config(major_version)

    # Читаем текущий main.py
    try:
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        logger.error("❌ Файл main.py не найден")
        return False

    # Ищем и заменяем блок инициализации бота
    old_config = '''    # Инициализация бота и диспетчера
    from aiogram.client.session.aiohttp import AioHTTPSession

    # Создаем сессию с увеличенными таймаутами
    session = AioHTTPSession(
        timeout=aiohttp.ClientTimeout(total=30, connect=10, sock_read=10)
    )

    bot = Bot(token=BOT_TOKEN, session=session)
    dp = Dispatcher(storage=MemoryStorage())'''

    if old_config in content:
        new_content = content.replace(old_config, config_content)
        logger.info(f"🔧 Обновляем конфигурацию для aiogram {version}")

        # Записываем обновленный файл
        with open('main.py', 'w', encoding='utf-8') as f:
            f.write(new_content)

        logger.info("✅ main.py успешно обновлен")
        return True
    else:
        logger.warning("⚠️ Блок конфигурации бота не найден в main.py")
        return False

def main():
    """Основная функция"""
    logger.info("🔍 Проверка версии aiogram и исправление конфигурации...")

    # Проверяем версию
    major_version, version = check_aiogram_version()
    if not major_version:
        logger.error("❌ Невозможно продолжить без aiogram")
        return False

    # Обновляем конфигурацию
    if update_main_py():
        logger.info("✅ Конфигурация успешно обновлена")
        logger.info(f"📋 Используется aiogram {version}")
        return True
    else:
        logger.error("❌ Не удалось обновить конфигурацию")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
