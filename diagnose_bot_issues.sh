#!/bin/bash

echo "🔧 Диагностика и исправление проблем с ботом"
echo "==========================================="

# 1. Проверяем порт приложения
echo "🔍 Проверяем на каком порту работает приложение..."
docker exec okypbot_app netstat -tulpn 2>/dev/null || docker exec okypbot_app ss -tulpn

# 2. Проверяем переменные окружения
echo ""
echo "🔍 Проверяем переменные окружения..."
docker exec okypbot_app printenv | grep -E "(WEBHOOK_PORT|BOT_TOKEN)" | head -10

# 3. Проверяем nginx конфигурацию
echo ""
echo "🔍 Проверяем nginx конфигурацию..."
docker exec okypbot_nginx cat /etc/nginx/conf.d/default.conf

# 4. Тестируем webhook напрямую
echo ""
echo "🔍 Тестируем webhook напрямую к приложению..."
docker exec okypbot_app curl -s "http://localhost:8000/health" || echo "❌ Порт 8000 недоступен"
docker exec okypbot_app curl -s "http://localhost:8001/health" || echo "❌ Порт 8001 недоступен"

# 5. Проверяем логи telegram бота
echo ""
echo "📋 Последние логи бота (поиск ошибок)..."
docker logs okypbot_app 2>&1 | grep -E "(ERROR|Exception|Failed|Bot)" | tail -10

# 6. Проверяем webhook URL в Telegram
echo ""
echo "🔍 Проверяем webhook в Telegram..."
docker exec okypbot_app python -c "
import os
import asyncio
import aiohttp

async def check_webhook():
    token = os.getenv('BOT_TOKEN')
    if not token:
        print('❌ BOT_TOKEN не найден')
        return
    
    url = f'https://api.telegram.org/bot{token}/getWebhookInfo'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            print(f'Webhook URL: {data.get(\"result\", {}).get(\"url\", \"Не установлен\")}')
            print(f'Статус: {data.get(\"result\", {}).get(\"has_custom_certificate\", False)}')

asyncio.run(check_webhook())
" 2>/dev/null || echo "❌ Не удалось проверить webhook"

echo ""
echo "✅ Диагностика завершена!"
