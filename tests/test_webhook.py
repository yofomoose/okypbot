#!/usr/bin/env python3
"""
Скрипт для тестирования webhook сервера
с официальной структурой данных Okdesk
"""

import asyncio
import aiohttp
import json

# Тестовые данные согласно официальной документации Okdesk
test_webhook_data = {
    "new_comment": {
        "event": {
            "event_type": "new_comment",
            "author": {
                "type": "contact",
                "id": 123,
                "first_name": "Иван",
                "last_name": "Иванов",
                "name": "Иван Иванов"
            },
            "comment": {
                "id": 456,
                "content": "Добрый день! У меня проблема с доступом к системе. Не могу войти в личный кабинет.",
                "is_public": True,
                "created_at": "2024-12-19T10:30:00Z"
            }
        },
        "issue": {
            "id": 789,
            "title": "Проблема с доступом к системе",
            "status": {
                "id": 1,
                "name": "Новая",
                "code": "new"
            },
            "contact": {
                "id": 123,
                "phone": "+7 (900) 123-45-67",
                "email": "ivan@example.com"
            }
        }
    },
    
    "status_changed": {
        "event": {
            "event_type": "status_changed",
            "old_status": {
                "id": 1,
                "name": "Новая",
                "code": "new"
            },
            "new_status": {
                "id": 2,
                "name": "В работе",
                "code": "in_progress"
            }
        },
        "issue": {
            "id": 789,
            "title": "Проблема с доступом к системе"
        }
    },
    
    "assignee_changed": {
        "event": {
            "event_type": "assignee_changed",
            "new_assignee": {
                "id": 555,
                "first_name": "Петр",
                "last_name": "Сидоров",
                "name": "Петр Сидоров",
                "email": "petr.sidorov@company.com"
            }
        },
        "issue": {
            "id": 789,
            "title": "Проблема с доступом к системе"
        }
    }
}

async def test_webhook(webhook_url: str, event_type: str):
    """Тестирование конкретного типа события"""
    if event_type not in test_webhook_data:
        print(f"❌ Неизвестный тип события: {event_type}")
        return False
    
    data = test_webhook_data[event_type]
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                'Content-Type': 'application/json',
                'X-Okdesk-Signature': 'test_signature'  # Для тестирования
            }
            
            print(f"📤 Отправка webhook '{event_type}' на {webhook_url}")
            print(f"📋 Данные: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            async with session.post(
                webhook_url,
                json=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    print(f"✅ Webhook '{event_type}' успешно обработан")
                    print(f"📥 Ответ: {response_text}")
                    return True
                else:
                    print(f"❌ Ошибка {response.status}: {response_text}")
                    return False
                    
    except aiohttp.ClientError as e:
        print(f"❌ Ошибка соединения: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

async def test_all_webhooks(webhook_url: str):
    """Тестирование всех типов событий"""
    print("🧪 Начинаем тестирование webhook сервера")
    print(f"🔗 URL: {webhook_url}")
    print("=" * 50)
    
    results = {}
    
    for event_type in test_webhook_data.keys():
        print(f"\n🔍 Тестирование события: {event_type}")
        print("-" * 30)
        
        result = await test_webhook(webhook_url, event_type)
        results[event_type] = result
        
        await asyncio.sleep(1)  # Пауза между тестами
    
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    
    all_passed = True
    for event_type, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {event_type}: {status}")
        if not success:
            all_passed = False
    
    print(f"\n🎯 Общий результат: {'✅ ВСЕ ТЕСТЫ ПРОШЛИ' if all_passed else '❌ ЕСТЬ ОШИБКИ'}")

async def test_server_health(base_url: str):
    """Проверка работоспособности сервера"""
    health_url = f"{base_url}/health"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(health_url) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Сервер работает: {data}")
                    return True
                else:
                    print(f"❌ Сервер недоступен: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Ошибка подключения к серверу: {e}")
        return False

async def main():
    """Основная функция"""
    # Настройки
    base_url = "http://localhost:8001"  # Порт webhook сервера
    webhook_url = f"{base_url}/okdesk-webhook"
    
    print("🚀 Тестирование Okdesk Webhook Handler")
    print("=" * 60)
    
    # Проверяем работоспособность сервера
    print("1️⃣ Проверка работоспособности сервера...")
    if not await test_server_health(base_url):
        print("❌ Сервер недоступен. Убедитесь, что webhook сервер запущен.")
        return
    
    print("\n2️⃣ Тестирование webhook endpoints...")
    await test_all_webhooks(webhook_url)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
