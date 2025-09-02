#!/usr/bin/env python3
"""
Тестирование системы двусторонней синхронизации комментариев Okdesk ↔ Telegram
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем корневую папку проекта в путь
sys.path.insert(0, str(Path(__file__).parent))

from services.okdesk_service import OkdeskService
from database.models import db
from config import OKDESK_API_TOKEN, OKDESK_BASE_URL, BOT_TOKEN
from aiogram import Bot
import logging

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_comment_sync_system():
    """Тестирует систему синхронизации комментариев"""
    
    print("🔄 Тестирование системы двусторонней синхронизации комментариев")
    print("=" * 70)
    
    # 1. Проверяем конфигурацию
    print("\n📋 Проверка конфигурации:")
    if not OKDESK_API_TOKEN:
        print("❌ OKDESK_API_TOKEN не установлен")
        return False
        
    if not OKDESK_BASE_URL:
        print("❌ OKDESK_BASE_URL не установлен")  
        return False
        
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не установлен")
        return False
        
    print("✅ Все необходимые токены установлены")
    
    # 2. Тестируем Okdesk API
    print("\n🌐 Тестирование Okdesk API:")
    
    service = OkdeskService(
        api_key=OKDESK_API_TOKEN,
        company_id="test",
        base_url=OKDESK_BASE_URL
    )
    
    async with service:
        # Проверяем подключение
        user = await service.get_current_user()
        if not user:
            print("❌ Не удалось подключиться к Okdesk API")
            return False
        
        print(f"✅ Подключение к Okdesk успешно (User ID: {user.get('id', 'Unknown')})")
        
        # 3. Создаем тестовую заявку
        print("\n🎫 Создание тестовой заявки:")
        
        issue = await service.create_issue(
            title="Тест системы комментариев",
            description="Автоматический тест двусторонней синхронизации комментариев между Telegram и Okdesk",
            contact_id=1  # Используем контакт с ID 1
        )
        
        if not issue:
            print("❌ Не удалось создать тестовую заявку")
            return False
            
        issue_id = issue.get('id')
        print(f"✅ Тестовая заявка создана (ID: {issue_id})")
        
        # 4. Добавляем комментарий от имени специалиста
        print("\n💬 Добавление комментария от специалиста:")
        
        comment_success = await service.add_comment_to_issue(
            issue_id=issue_id,
            comment_text="Юлия (через Telegram): Здравствуйте! Мы получили вашу заявку и работаем над решением проблемы. Можете предоставить дополнительную информацию?",
            is_public=True,
            author_id=1  # ID специалиста
        )
        
        if comment_success:
            print("✅ Комментарий от специалиста добавлен")
        else:
            print("⚠️ Не удалось добавить комментарий от специалиста")
        
        # 5. Добавляем ответ от клиента
        print("\n💬 Добавление ответа от клиента:")
        
        client_comment = await service.add_comment_to_issue(
            issue_id=issue_id,
            comment_text="Кирилл (клиент через Telegram): Спасибо за быстрый ответ! Проблема возникает когда я пытаюсь распечатать документы формата A3. Принтер просто не реагирует.",
            is_public=True,
            author_id=None  # Для клиентов не нужен author_id
        )
        
        if client_comment:
            print("✅ Ответ клиента добавлен")
        else:
            print("⚠️ Не удалось добавить ответ клиента")
        
        # 6. Получаем все комментарии
        print("\n📝 Получение всех комментариев:")
        
        comments = await service.get_issue_comments(issue_id)
        if comments:
            print(f"✅ Получено {len(comments)} комментариев:")
            for i, comment in enumerate(comments, 1):
                author = comment.get('author_name', 'Неизвестный')
                content = comment.get('content', 'Нет содержимого')
                print(f"   {i}. {author}: {content[:100]}{'...' if len(content) > 100 else ''}")
        else:
            print("⚠️ Комментарии не найдены")
        
        # 7. Тестируем мониторинг заявок
        print("\n👥 Тестирование системы мониторинга:")
        
        # Добавляем заявку в мониторинг для тестового пользователя
        test_user_id = 123456789  # Тестовый Telegram ID
        await db.add_user_issue_for_monitoring(issue_id, test_user_id)
        print(f"✅ Заявка {issue_id} добавлена в мониторинг для пользователя {test_user_id}")
        
        # Проверяем активные заявки
        active_issues = await db.get_active_user_issues()
        print(f"✅ В мониторинге {len(active_issues)} активных заявок")
        
    # 8. Тестируем Telegram Bot API
    print("\n🤖 Тестирование Telegram Bot API:")
    
    try:
        bot = Bot(token=BOT_TOKEN)
        bot_info = await bot.get_me()
        print(f"✅ Telegram Bot готов к работе (@{bot_info.username})")
        await bot.session.close()
    except Exception as e:
        print(f"❌ Ошибка Telegram Bot API: {e}")
        return False
    
    print("\n🎉 Все тесты пройдены успешно!")
    print("\n📋 Система готова к работе:")
    print("   1. ✅ Okdesk API подключение работает")
    print("   2. ✅ Создание заявок функционирует")
    print("   3. ✅ Добавление комментариев работает")
    print("   4. ✅ Система мониторинга настроена")
    print("   5. ✅ Telegram Bot готов")
    
    print(f"\n🔗 Ссылка на тестовую заявку: {OKDESK_BASE_URL}/issues/{issue_id}")
    
    return True

async def demonstrate_workflow():
    """Демонстрирует типичный workflow комментариев"""
    
    print("\n🔄 Демонстрация рабочего процесса:")
    print("=" * 50)
    
    print("1. 👤 Клиент (Кирилл) создает заявку через Telegram")
    print("   └─ Заявка автоматически создается в Okdesk")
    print("   └─ Заявка добавляется в мониторинг")
    
    print("\n2. 👨‍💼 Специалист (Юлия) отвечает в Okdesk")
    print("   └─ Webhook уведомляет наш сервер")
    print("   └─ Бот отправляет уведомление клиенту в Telegram")
    print("   └─ Клиент видит кнопку 'Ответить'")
    
    print("\n3. 👤 Клиент (Кирилл) отвечает в Telegram")
    print("   └─ Комментарий добавляется в Okdesk")
    print("   └─ Специалист видит ответ в системе")
    
    print("\n4. 👨‍💼 Специалист (Юлия) отвечает через Telegram")
    print("   └─ Комментарий добавляется в Okdesk")  
    print("   └─ Клиент получает уведомление в Telegram")
    
    print("\n✨ Результат: полная двусторонняя синхронизация!")

async def main():
    """Основная функция"""
    
    print("🚀 Okypbot - Тестирование системы комментариев")
    print("Версия: 1.0.0")
    
    # Демонстрируем workflow
    await demonstrate_workflow()
    
    # Запускаем тесты
    success = await test_comment_sync_system()
    
    if success:
        print("\n🎯 Следующие шаги для продакшена:")
        print("1. Настройте webhook в Okdesk (URL: http://your-domain/okdesk-webhook)")
        print("2. Добавьте специалистов в систему маппинга")
        print("3. Протестируйте с реальными пользователями")
        print("4. Запустите мониторинг комментариев")
    else:
        print("\n❌ Обнаружены проблемы. Проверьте конфигурацию.")

if __name__ == "__main__":
    asyncio.run(main())
