#!/usr/bin/env python3
"""
Диагностический скрипт для проверки настроек Okdesk API
"""

import asyncio
import os
import sys
from pathlib import Path

# Добавляем корневую папку проекта в путь
sys.path.insert(0, str(Path(__file__).parent))

from services.okdesk_service import OkdeskService
from config import OKDESK_API_TOKEN, OKDESK_BASE_URL, OKDESK_AUTHOR_ID
import logging

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def diagnose_okdesk_connection():
    """Диагностика подключения к Okdesk API"""
    
    print("🔍 Диагностика подключения к Okdesk API")
    print("=" * 50)
    
    # Проверяем переменные окружения
    print("\n📋 Проверка конфигурации:")
    print(f"OKDESK_API_TOKEN: {'✅ установлен' if OKDESK_API_TOKEN else '❌ не установлен'}")
    print(f"OKDESK_BASE_URL: {OKDESK_BASE_URL if OKDESK_BASE_URL else '❌ не установлен'}")
    print(f"OKDESK_AUTHOR_ID: {OKDESK_AUTHOR_ID if OKDESK_AUTHOR_ID else '❌ не установлен'}")
    
    if not OKDESK_API_TOKEN:
        print("\n❌ ОШИБКА: OKDESK_API_TOKEN не установлен в переменных окружения")
        print("Добавьте в .env файл: OKDESK_API_TOKEN=ваш_токен")
        return False
        
    if not OKDESK_BASE_URL:
        print("\n❌ ОШИБКА: OKDESK_BASE_URL не установлен в переменных окружения")
        print("Добавьте в .env файл: OKDESK_BASE_URL=https://your-company.okdesk.ru")
        return False
    
    # Проверяем формат URL
    if not OKDESK_BASE_URL.startswith('http'):
        print(f"\n⚠️ ПРЕДУПРЕЖДЕНИЕ: base_url должен начинаться с http:// или https://")
        print(f"Текущий: {OKDESK_BASE_URL}")
    
    # Тестируем подключение
    print(f"\n🌐 Тестирование подключения к {OKDESK_BASE_URL}")
    
    try:
        service = OkdeskService(
            api_key=OKDESK_API_TOKEN,
            company_id="test",
            base_url=OKDESK_BASE_URL
        )
        
        async with service:
            # Попробуем получить информацию о пользователе
            print("👤 Попытка получить информацию о текущем пользователе...")
            user = await service.get_current_user()
            
            if user:
                print("✅ Успешно получена информация о пользователе:")
                print(f"   ID: {user.get('id', 'Не указан')}")
                print(f"   Имя: {user.get('name', 'Не указано')}")
                print(f"   Email: {user.get('email', 'Не указан')}")
                return True
            else:
                print("❌ Не удалось получить информацию о пользователе")
                print("\nВозможные причины:")
                print("1. Неправильный API токен")
                print("2. Неправильный base_url")
                print("3. API токен не имеет необходимых прав")
                print("4. Проблемы с сетевым подключением")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False

async def test_basic_endpoints():
    """Тестирование базовых endpoints"""
    
    print("\n🔗 Тестирование базовых endpoints:")
    
    service = OkdeskService(
        api_key=OKDESK_API_TOKEN,
        company_id="test", 
        base_url=OKDESK_BASE_URL
    )
    
    endpoints_to_test = [
        "/api/v1/employees",
        "/api/v1/users",
        "/api/v1/companies",
        "/api/v1/issues",
        "/api/v1/contacts"
    ]
    
    async with service:
        for endpoint in endpoints_to_test:
            try:
                url = f"{OKDESK_BASE_URL}{endpoint}"
                params = {'api_token': OKDESK_API_TOKEN}
                
                async with service.session.get(url, params=params) as response:
                    status = response.status
                    if status == 200:
                        print(f"   ✅ {endpoint} - статус {status}")
                    elif status == 401:
                        print(f"   🔐 {endpoint} - статус {status} (проблема авторизации)")
                    elif status == 403:
                        print(f"   🚫 {endpoint} - статус {status} (нет доступа)")
                    elif status == 404:
                        print(f"   ❓ {endpoint} - статус {status} (не найден)")
                    else:
                        print(f"   ⚠️ {endpoint} - статус {status}")
                        
            except Exception as e:
                print(f"   ❌ {endpoint} - ошибка: {e}")

def check_environment_file():
    """Проверяем наличие и содержимое .env файла"""
    
    print("\n📄 Проверка .env файла:")
    
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ Файл .env не найден в корневой папке проекта")
        print("\nСоздайте файл .env со следующим содержимым:")
        print("BOT_TOKEN=ваш_токен_бота")
        print("OKDESK_API_TOKEN=ваш_api_токен")
        print("OKDESK_BASE_URL=https://your-company.okdesk.ru")
        print("OKDESK_AUTHOR_ID=1")
        return False
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print("✅ Файл .env найден")
        
        required_vars = ['BOT_TOKEN', 'OKDESK_API_TOKEN', 'OKDESK_BASE_URL']
        missing_vars = []
        
        for var in required_vars:
            if var not in content:
                missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️ Отсутствуют обязательные переменные: {', '.join(missing_vars)}")
            return False
        else:
            print("✅ Все обязательные переменные присутствуют")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка чтения .env файла: {e}")
        return False

async def main():
    """Основная функция диагностики"""
    
    print("🚀 Okypbot - Диагностика Okdesk API")
    print("Версия: 1.0.0")
    print("=" * 50)
    
    # Проверяем .env файл
    env_ok = check_environment_file()
    
    if not env_ok:
        print("\n❌ Сначала исправьте проблемы с .env файлом")
        return
    
    # Диагностируем подключение
    connection_ok = await diagnose_okdesk_connection()
    
    if connection_ok:
        # Тестируем endpoints
        await test_basic_endpoints()
        print("\n✅ Диагностика завершена успешно!")
    else:
        print("\n❌ Обнаружены проблемы с подключением к Okdesk API")
        print("\nРекомендуемые действия:")
        print("1. Проверьте правильность OKDESK_BASE_URL")
        print("2. Убедитесь что API токен активен и имеет права")
        print("3. Проверьте сетевое подключение")
        print("4. Обратитесь к администратору Okdesk")

if __name__ == "__main__":
    asyncio.run(main())
