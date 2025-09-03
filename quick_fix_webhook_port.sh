#!/bin/bash

echo "⚡ Быстрое исправление порта webhook и обновление"
echo "============================================="

# Останавливаем текущие контейнеры
echo "🛑 Останавливаем контейнеры..."
docker-compose down

# Проверяем переменные окружения
echo "🔍 Проверяем текущие переменные окружения..."
echo "В .env.production:"
grep WEBHOOK_PORT .env.production

echo ""
echo "В docker-compose.yml:"
grep WEBHOOK_PORT docker-compose.yml

# Принудительно устанавливаем переменную окружения
echo ""
echo "🔧 Устанавливаем переменную окружения..."
export WEBHOOK_PORT=8001

# Запускаем с форсированными переменными окружения
echo "🚀 Перезапускаем с правильными настройками..."
WEBHOOK_PORT=8001 docker-compose --env-file .env.production up -d --force-recreate

echo "⏳ Ждем запуска (30 секунд)..."
sleep 30

# Проверяем переменные окружения в контейнере
echo "🔍 Проверяем переменные в запущенном контейнере..."
docker exec okypbot_app printenv | grep WEBHOOK

# Проверяем на каком порту слушает приложение
echo ""
echo "🔍 Проверяем активные порты в контейнере..."
docker exec okypbot_app netstat -tulpn 2>/dev/null | grep :800 || docker exec okypbot_app ss -tulpn | grep :800

# Тестируем оба порта
echo ""
echo "🔍 Тестируем доступность портов..."
docker exec okypbot_app curl -s "http://localhost:8000/health" -m 5 && echo "✅ Порт 8000 работает" || echo "❌ Порт 8000 недоступен"
docker exec okypbot_app curl -s "http://localhost:8001/health" -m 5 && echo "✅ Порт 8001 работает" || echo "❌ Порт 8001 недоступен"

# Проверяем через nginx
echo ""
echo "🌐 Тестируем через nginx..."
curl -s "http://localhost:8080/health" -m 5 && echo "✅ nginx → приложение работает" || echo "❌ nginx → приложение недоступно"

# Показываем логи для диагностики
echo ""
echo "📋 Последние логи приложения..."
docker logs okypbot_app | tail -10

echo ""
echo "📊 Статус контейнеров:"
docker-compose ps

echo ""
echo "✅ Исправление завершено!"
echo "🤖 Попробуйте команду /start в Telegram боте"
echo "🌐 Webhook должен быть доступен на: http://your-server:8080/okdesk-webhook"
