"""
Скрипт для настройки webhook в okdesk
"""
import asyncio
import sys
import os

# Добавляем корневую папку в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.okdesk_service import OkdeskService
from config import WEBHOOK_URL, OKDESK_WEBHOOK_SECRET

async def setup_webhook():
    """Настройка webhook в okdesk"""
    okdesk_service = OkdeskService()
    
    try:
        # Конфигурация webhook
        webhook_config = {
            'url': WEBHOOK_URL,
            'events': [
                'issue.comment_added',    # Новый комментарий
                'issue.status_changed',   # Изменение статуса
                'issue.assigned',         # Назначение исполнителя
                'issue.created',          # Создание заявки
                'issue.updated'           # Обновление заявки
            ],
            'active': True
        }
        
        # Добавляем секретный ключ если настроен
        if OKDESK_WEBHOOK_SECRET:
            webhook_config['secret'] = OKDESK_WEBHOOK_SECRET
        
        print("🔧 Настройка webhook в okdesk...")
        print(f"📡 URL: {WEBHOOK_URL}")
        print(f"🎯 События: {webhook_config['events']}")
        
        # Создаем webhook через API
        async with okdesk_service.session:
            url = f"{okdesk_service.base_url}/api/v1/webhooks"
            headers = {
                'Authorization': f'Bearer {okdesk_service.api_token}',
                'Content-Type': 'application/json'
            }
            
            async with okdesk_service.session.post(url, json=webhook_config, headers=headers) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    print("✅ Webhook успешно создан!")
                    print(f"🆔 ID: {result.get('id')}")
                    print(f"📋 Статус: {result.get('status', 'неизвестно')}")
                    return result
                else:
                    error_text = await response.text()
                    print(f"❌ Ошибка создания webhook: {response.status} - {error_text}")
                    return None
        
    except Exception as e:
        print(f"❌ Ошибка создания webhook: {e}")
        return None

async def list_webhooks():
    """Просмотр существующих webhooks"""
    okdesk_service = OkdeskService()
    
    try:
        print("📋 Список существующих webhooks...")
        
        async with okdesk_service.session:
            url = f"{okdesk_service.base_url}/api/v1/webhooks"
            headers = {
                'Authorization': f'Bearer {okdesk_service.api_token}',
            }
            
            async with okdesk_service.session.get(url, headers=headers) as response:
                if response.status == 200:
                    webhooks = await response.json()
                    
                    if not webhooks:
                        print("📭 Webhooks не найдены")
                        return
                    
                    for webhook in webhooks:
                        print(f"\n🔗 Webhook ID: {webhook.get('id')}")
                        print(f"   📡 URL: {webhook.get('url')}")
                        print(f"   🎯 События: {webhook.get('events', [])}")
                        print(f"   ✅ Активен: {webhook.get('active', False)}")
                else:
                    error_text = await response.text()
                    print(f"❌ Ошибка получения webhooks: {response.status} - {error_text}")
            
    except Exception as e:
        print(f"❌ Ошибка получения webhooks: {e}")

async def delete_webhook(webhook_id: int):
    """Удаление webhook"""
    okdesk_service = OkdeskService()
    
    try:
        print(f"🗑️ Удаление webhook ID: {webhook_id}...")
        
        async with okdesk_service.session:
            url = f"{okdesk_service.base_url}/api/v1/webhooks/{webhook_id}"
            headers = {
                'Authorization': f'Bearer {okdesk_service.api_token}',
            }
            
            async with okdesk_service.session.delete(url, headers=headers) as response:
                if response.status in [200, 204]:
                    print("✅ Webhook успешно удален!")
                else:
                    error_text = await response.text()
                    print(f"❌ Ошибка удаления webhook: {response.status} - {error_text}")
        
    except Exception as e:
        print(f"❌ Ошибка удаления webhook: {e}")

async def test_webhook():
    """Тестирование webhook"""
    print("🧪 Тестирование webhook...")
    print(f"📡 URL: {WEBHOOK_URL}")
    
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            # Проверяем доступность эндпоинта
            async with session.get(f"{WEBHOOK_URL.replace('/okdesk-webhook', '/health')}") as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ Webhook сервер доступен!")
                    print(f"📊 Статус: {result.get('status')}")
                    print(f"🏷️ Сервис: {result.get('service')}")
                else:
                    print(f"❌ Webhook сервер недоступен: {response.status}")
                    
    except Exception as e:
        print(f"❌ Ошибка тестирования webhook: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Управление webhooks okdesk')
    parser.add_argument('action', choices=['setup', 'list', 'delete', 'test'], 
                       help='Действие: setup, list, delete, test')
    parser.add_argument('--id', type=int, help='ID webhook для удаления')
    
    args = parser.parse_args()
    
    if args.action == 'setup':
        asyncio.run(setup_webhook())
    elif args.action == 'list':
        asyncio.run(list_webhooks())
    elif args.action == 'delete':
        if not args.id:
            print("❌ Для удаления укажите ID webhook: --id 123")
        else:
            asyncio.run(delete_webhook(args.id))
    elif args.action == 'test':
        asyncio.run(test_webhook())
