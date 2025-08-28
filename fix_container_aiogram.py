#!/usr/bin/env python3
"""
Скрипт для проверки версии aiogram в контейнере и создания правильной конфигурации
"""

import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_docker_command(command):
    """Выполняет команду в Docker контейнере"""
    try:
        full_command = f'docker exec okypbot_app {command}'
        result = subprocess.run(full_command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        logger.error(f"Ошибка выполнения команды: {e}")
        return False, "", str(e)

def check_aiogram_version_in_container():
    """Проверяет версию aiogram в контейнере"""
    success, stdout, stderr = run_docker_command('python -c "import aiogram; print(aiogram.__version__)"')

    if success:
        version = stdout.strip()
        logger.info(f"✅ Версия aiogram в контейнере: {version}")
        return version
    else:
        logger.error(f"❌ Не удалось проверить версию aiogram: {stderr}")
        return None

def check_aiogram_imports_in_container():
    """Проверяет доступные импорты aiogram в контейнере"""
    imports_to_check = [
        "from aiogram.client.session.aiohttp import AioHTTPSession",
        "from aiogram.client.session import AioHTTPSession",
        "from aiogram import Bot",
    ]

    working_imports = []
    for import_stmt in imports_to_check:
        success, stdout, stderr = run_docker_command(f'python -c "{import_stmt}; print(\\"OK\\")"')
        if success and "OK" in stdout:
            working_imports.append(import_stmt)
            logger.info(f"✅ Рабочий импорт: {import_stmt}")
        else:
            logger.debug(f"❌ Не рабочий импорт: {import_stmt}")

    return working_imports

def create_container_compatible_config():
    """Создает конфигурацию совместимую с контейнером"""

    version = check_aiogram_version_in_container()
    if not version:
        logger.error("❌ Не удалось определить версию aiogram")
        return False

    working_imports = check_aiogram_imports_in_container()

    # Создаем конфигурацию
    config_lines = [
        "    # Инициализация бота и диспетчера (адаптивная версия)",
        "    import aiohttp",
        "    ",
        "    # Проверяем доступность AioHTTPSession",
    ]

    if working_imports:
        # Используем рабочий импорт
        import_line = working_imports[0]
        config_lines.extend([
            f"    try:",
            f"        {import_line}",
            f"        # Создаем сессию с увеличенными таймаутами",
            f"        session = AioHTTPSession(",
            f"            timeout=aiohttp.ClientTimeout(total=30, connect=10, sock_read=10)",
            f"        )",
            f"        bot = Bot(token=BOT_TOKEN, session=session)",
            f"        logger.info(\"✅ Используется aiogram с кастомной сессией\")",
            f"    except (ImportError, AttributeError) as e:",
            f"        logger.warning(f\"⚠️ Ошибка импорта сессии: {{e}}, используем стандартную конфигурацию\")",
            f"        bot = Bot(token=BOT_TOKEN)",
            f"        logger.info(\"✅ Используется стандартная конфигурация бота\")",
        ])
    else:
        # Используем стандартную конфигурацию
        config_lines.extend([
            f"    # AioHTTPSession недоступен, используем стандартную конфигурацию",
            f"    bot = Bot(token=BOT_TOKEN)",
            f"    logger.info(\"✅ Используется стандартная конфигурация бота\")",
        ])

    config_lines.extend([
        "    ",
        "    dp = Dispatcher(storage=MemoryStorage())"
    ])

    # Обновляем main.py
    try:
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # Ищем старую конфигурацию
        old_config_start = "    # Инициализация бота и диспетчера"
        old_config_end = "    dp = Dispatcher(storage=MemoryStorage())"

        start_pos = content.find(old_config_start)
        if start_pos == -1:
            logger.error("❌ Не найден блок конфигурации бота в main.py")
            return False

        # Находим конец блока
        end_pos = content.find(old_config_end, start_pos)
        if end_pos == -1:
            end_pos = start_pos + len(old_config_start)
        else:
            end_pos += len(old_config_end)

        # Заменяем блок
        new_config = "\n".join(config_lines)
        new_content = content[:start_pos] + new_config + content[end_pos:]

        with open('main.py', 'w', encoding='utf-8') as f:
            f.write(new_content)

        logger.info("✅ main.py успешно обновлен для совместимости с контейнером")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка обновления main.py: {e}")
        return False

def main():
    """Основная функция"""
    logger.info("🔍 Проверка конфигурации aiogram в контейнере...")

    # Проверяем, что контейнер запущен
    success, stdout, stderr = run_docker_command('echo "test"')
    if not success:
        logger.error("❌ Контейнер okypbot_app не запущен или недоступен")
        logger.info("📝 Убедитесь, что контейнер запущен: docker-compose up -d")
        return False

    # Создаем совместимую конфигурацию
    if create_container_compatible_config():
        logger.info("✅ Конфигурация успешно адаптирована для контейнера")
        logger.info("📝 Теперь можно перезапустить контейнер для применения изменений")
        return True
    else:
        logger.error("❌ Не удалось адаптировать конфигурацию")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
