#!/bin/bash

echo "🚀 Финальный деплой с исправлением всех проблем"
echo "=============================================="

# 1. Останавливаем все контейнеры
echo "🛑 Останавливаем все контейнеры..."
docker-compose down
docker stop $(docker ps -aq) 2>/dev/null || true
docker system prune -f

# 2. Удаляем проблемные volumes если есть
echo "🧹 Очищаем проблемные volumes..."
docker volume prune -f

# 3. Принудительно устанавливаем переменные окружения
echo "📝 Устанавливаем переменные окружения..."
export WEBHOOK_PORT=8001
export WEBHOOK_HOST=0.0.0.0
export WEBHOOK_ENABLED=true

# 4. Создаем правильный .env файл для Docker
echo "📋 Создаем правильный .env файл..."
cat > .env << 'EOF'
# Telegram Bot Token
BOT_TOKEN=8461903171:AAFKNyFL5LcqFIHSaGePJZ-vCCNQU3kRIqA

# Okdesk API Token
OKDESK_API_TOKEN=4cf96e5bb33f06481e4aff5ff0a2aa740ce8490a

# Базовый URL вашего аккаунта Okdesk
OKDESK_BASE_URL=https://yapomogu55.okdesk.ru

# ID автора для комментариев
OKDESK_AUTHOR_ID=1

# PostgreSQL Configuration для Docker
DB_HOST=postgres
DB_PORT=5432
DB_NAME=okypbot
DB_USER=postgres
DB_PASSWORD=Cnhjywsq97

# Webhook настройки - ФИКСИРОВАННО
WEBHOOK_ENABLED=true
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8001

# Администраторы
ADMIN_IDS=413129274,398258337

# Debug
DEBUG=false
EOF

# 5. Пересобираем образ без кэша
echo "🔨 Пересобираем образ..."
docker-compose build --no-cache --pull

# 6. Запускаем с принудительными переменными
echo "🚀 Запускаем с правильными настройками..."
WEBHOOK_PORT=8001 WEBHOOK_HOST=0.0.0.0 WEBHOOK_ENABLED=true docker-compose up -d --force-recreate

# 7. Ждем полного запуска
echo "⏳ Ждем полного запуска (45 секунд)..."
sleep 45

# 8. Проверяем результат
echo "📊 Проверяем статус..."
docker-compose ps

echo ""
echo "🔍 Проверяем переменные в контейнере..."
docker exec okypbot_app printenv | grep -E "WEBHOOK|BOT_TOKEN" | head -5

echo ""
echo "🔍 Проверяем порты..."
docker exec okypbot_app ss -tulpn | grep :800 || echo "Не удалось получить информацию о портах"

echo ""
echo "🌐 Тестируем endpoints..."
# Тест напрямую к приложению
docker exec okypbot_app curl -s "http://localhost:8001/health" -m 5 && echo "✅ Приложение на 8001 работает" || echo "❌ Приложение на 8001 недоступно"

# Тест через nginx
curl -s "http://localhost:8080/health" -m 5 && echo "✅ nginx → приложение работает" || echo "❌ nginx → приложение недоступно"

# Тест webhook endpoint
curl -s -X POST "http://localhost:8080/okdesk-webhook" -H "Content-Type: application/json" -d '{"test": true}' -m 5 && echo "✅ webhook endpoint работает" || echo "❌ webhook endpoint недоступен"

echo ""
echo "📋 Последние логи приложения..."
docker logs okypbot_app | tail -10

echo ""
echo "✅ Деплой завершен!"
echo ""
echo "🎯 Следующие шаги:"
echo "1. Проверьте что бот отвечает на команду /start в Telegram"
echo "2. Настройте webhook в Okdesk на URL: http://your-server:8080/okdesk-webhook"
echo "3. Протестируйте создание заявки в боте"
echo ""
echo "🔧 Если проблемы остались:"
echo "   docker logs okypbot_app"
echo "   docker exec -it okypbot_app bash"
