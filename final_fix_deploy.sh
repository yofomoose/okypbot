#!/bin/bash

echo "🔧 Финальное исправление конфигурации Docker"
echo "==========================================="

# Останавливаем контейнеры
echo "🛑 Останавливаем все контейнеры..."
docker-compose down

# Заменяем испорченный docker-compose.yml
echo "📝 Заменяем docker-compose.yml на исправленную версию..."
cp docker-compose-fixed.yml docker-compose.yml

# Устанавливаем пароль PostgreSQL если нужно
echo "🔑 Исправляем аутентификацию PostgreSQL..."
if docker ps -a | grep -q "okypbot_postgres"; then
    docker exec okypbot_postgres psql -U postgres -c "ALTER USER postgres PASSWORD 'Cnhjywsq97';" 2>/dev/null || echo "PostgreSQL контейнер не запущен"
fi

# Очищаем старые образы и контейнеры
echo "🧹 Очищаем старые образы..."
docker system prune -f

# Пересобираем с чистого листа
echo "🔨 Пересобираем приложение..."
docker-compose build --no-cache

# Запускаем все сервисы
echo "🚀 Запускаем все сервисы..."
docker-compose --env-file .env.production up -d

# Ждем запуска
echo "⏳ Ждем полного запуска (60 секунд)..."
sleep 60

# Проверяем статус
echo "📊 Статус сервисов:"
docker-compose ps

echo ""
echo "🔍 Проверяем переменные окружения в приложении..."
docker exec okypbot_app printenv | grep -E "(WEBHOOK_PORT|BOT_TOKEN)" | head -5

echo ""
echo "🌐 Тестируем endpoints..."
echo "Тест приложения:"
docker exec okypbot_app curl -s "http://localhost:8001/health" -m 5 && echo "✅ Приложение на 8001" || echo "❌ Приложение недоступно"

echo "Тест nginx:"
curl -s "http://localhost:8080/health" -m 5 && echo "✅ nginx работает" || echo "❌ nginx недоступен"

echo "Тест webhook:"
curl -s "http://localhost:8080/okdesk-webhook" -X POST -H "Content-Type: application/json" -d '{"test": true}' -m 5 && echo "✅ webhook работает" || echo "❌ webhook недоступен"

echo ""
echo "📋 Логи для диагностики:"
echo "=== PostgreSQL ==="
docker logs okypbot_postgres | tail -5

echo "=== Приложение ==="
docker logs okypbot_app | tail -5

echo "=== Nginx ==="
docker logs okypbot_nginx | tail -5

echo ""
echo "✅ Исправление завершено!"
echo "🤖 Попробуйте команду /start в Telegram боте"
echo "🌐 Webhook: http://your-server:8080/okdesk-webhook"
