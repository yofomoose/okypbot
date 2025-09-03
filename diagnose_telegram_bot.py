#!/usr/bin/env python3
"""
Диагностика Telegram бота - проверка webhook, команд и интеграции
"""

import asyncio
import os
import sys
import aiohttp
import json
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.append(str(Path(__file__).parent))

class TelegramBotDiagnostic:
    def __init__(self):
        self.bot_token = os.getenv('BOT_TOKEN')
        self.webhook_url = None
        
    async def check_bot_token(self):
        """Проверка токена бота"""
        print("🔑 Проверка токена бота...")
        
        if not self.bot_token:
            print("❌ BOT_TOKEN не найден в переменных окружения")
            return False
            
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
                async with session.get(url, timeout=10) as resp:
                    data = await resp.json()
                    
                    if data.get('ok'):
                        bot_info = data['result']
                        print(f"✅ Бот найден: {bot_info['first_name']} (@{bot_info['username']})")
                        print(f"   ID: {bot_info['id']}")
                        return True
                    else:
                        print(f"❌ Ошибка API: {data.get('description', 'Неизвестная ошибка')}")
                        return False
                        
        except Exception as e:
            print(f"❌ Ошибка подключения к Telegram API: {e}")
            return False
    
    async def check_webhook_info(self):
        """Проверка настроек webhook"""
        print("\n🌐 Проверка webhook...")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.telegram.org/bot{self.bot_token}/getWebhookInfo"
                async with session.get(url, timeout=10) as resp:
                    data = await resp.json()
                    
                    if data.get('ok'):
                        webhook_info = data['result']
                        
                        if webhook_info.get('url'):
                            self.webhook_url = webhook_info['url']
                            print(f"✅ Webhook установлен: {webhook_info['url']}")
                            print(f"   Последнее обновление: {webhook_info.get('last_error_date', 'N/A')}")
                            
                            if webhook_info.get('last_error_message'):
                                print(f"⚠️ Последняя ошибка: {webhook_info['last_error_message']}")
                                
                            print(f"   Pending updates: {webhook_info.get('pending_update_count', 0)}")
                            return True
                        else:
                            print("❌ Webhook не установлен")
                            print("   Бот работает в режиме polling")
                            return False
                    else:
                        print(f"❌ Ошибка получения webhook info: {data.get('description')}")
                        return False
                        
        except Exception as e:
            print(f"❌ Ошибка проверки webhook: {e}")
            return False
    
    async def test_webhook_endpoint(self):
        """Тестирование webhook endpoint"""
        print("\n🔗 Тестирование webhook endpoint...")
        
        # Тестируем локальные endpoints
        endpoints_to_test = [
            "http://localhost:8000/health",
            "http://localhost:8001/health", 
            "http://localhost:8080/health",
            "http://localhost:8080/okdesk-webhook"
        ]
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            for endpoint in endpoints_to_test:
                try:
                    async with session.get(endpoint) as resp:
                        if resp.status == 200:
                            print(f"✅ {endpoint} - доступен (статус: {resp.status})")
                        else:
                            print(f"⚠️ {endpoint} - статус: {resp.status}")
                except Exception as e:
                    print(f"❌ {endpoint} - недоступен ({e})")
    
    async def check_environment_vars(self):
        """Проверка переменных окружения"""
        print("\n📋 Проверка переменных окружения...")
        
        required_vars = [
            'BOT_TOKEN',
            'OKDESK_API_TOKEN', 
            'OKDESK_BASE_URL',
            'WEBHOOK_ENABLED',
            'WEBHOOK_HOST',
            'WEBHOOK_PORT'
        ]
        
        all_ok = True
        for var in required_vars:
            value = os.getenv(var)
            if value:
                # Скрываем токены для безопасности
                if 'TOKEN' in var:
                    display_value = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else "***"
                else:
                    display_value = value
                print(f"✅ {var}: {display_value}")
            else:
                print(f"❌ {var}: не установлен")
                all_ok = False
                
        return all_ok
    
    async def send_test_command(self):
        """Отправка тестовой команды боту"""
        print("\n🤖 Тестирование команд бота...")
        
        try:
            # Получаем информацию о командах бота
            async with aiohttp.ClientSession() as session:
                url = f"https://api.telegram.org/bot{self.bot_token}/getMyCommands"
                async with session.get(url, timeout=10) as resp:
                    data = await resp.json()
                    
                    if data.get('ok'):
                        commands = data['result']
                        if commands:
                            print("✅ Команды бота настроены:")
                            for cmd in commands:
                                print(f"   /{cmd['command']} - {cmd['description']}")
                        else:
                            print("⚠️ Команды бота не настроены")
                    else:
                        print(f"❌ Ошибка получения команд: {data.get('description')}")
                        
        except Exception as e:
            print(f"❌ Ошибка проверки команд: {e}")
    
    async def comprehensive_check(self):
        """Полная диагностика"""
        print("🔍 Диагностика Telegram бота")
        print("=" * 40)
        
        # Проверяем переменные окружения
        env_ok = await self.check_environment_vars()
        
        # Проверяем токен бота
        if env_ok:
            bot_ok = await self.check_bot_token()
            
            if bot_ok:
                # Проверяем webhook
                await self.check_webhook_info()
                
                # Тестируем endpoints
                await self.test_webhook_endpoint()
                
                # Проверяем команды
                await self.send_test_command()
            
        print("\n" + "=" * 40)
        print("📊 Рекомендации:")
        
        if not env_ok:
            print("❗ Проверьте .env файл и переменные окружения")
            
        if self.webhook_url and 'localhost' in self.webhook_url:
            print("❗ Webhook указывает на localhost - обновите на публичный URL")
            
        print("🔧 Для исправления проблем запустите:")
        print("   ./quick_fix_webhook_port.sh")
        print("   ./diagnose_bot_issues.sh")

async def main():
    """Основная функция"""
    diagnostic = TelegramBotDiagnostic()
    await diagnostic.comprehensive_check()

if __name__ == "__main__":
    asyncio.run(main())
