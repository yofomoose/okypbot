#!/bin/bash

echo "🚀 Правильный деплой okypbot с исправленной конфигурацией"
echo "======================================================="

# Проверяем что мы в правильной директории
if [[ ! -f "docker-compose.yml" ]]; then
    echo "❌ docker-compose.yml не найден. Убедитесь что вы в директории проекта."
    exit 1
fi

# Останавливаем старые контейнеры
echo "🛑 Останавливаем старые контейнеры..."
docker-compose down

# Очищаем старые образы
echo "🧹 Очищаем старые образы..."
docker system prune -f

# Принудительно удаляем старый образ okypbot
echo "🗑️ Удаляем старый образ okypbot..."
docker rmi okypbot:latest 2>/dev/null || echo "Образ okypbot:latest не найден"

# Пересобираем с новыми зависимостями
echo "🔨 Пересобираем приложение с новыми зависимостями..."
docker-compose build --no-cache --pull

# Запускаем с правильной конфигурацией
echo "🚀 Запускаем с исправленной конфигурацией..."
docker-compose --env-file .env.production up -d

# Ждем запуска
echo "⏳ Ждем запуска всех сервисов (60 секунд)..."
sleep 60

# Проверяем статус
echo "📊 Статус контейнеров:"
docker-compose ps

# Проверяем PostgreSQL
echo ""
echo "🐘 Проверка PostgreSQL..."
docker exec okypbot_postgres pg_isready -U postgres && echo "✅ PostgreSQL готов" || echo "❌ PostgreSQL не готов"

# Проверяем переменные окружения в приложении
echo ""
echo "🔍 Проверка переменных окружения в приложении..."
docker exec okypbot_app printenv | grep -E "(WEBHOOK_PORT|DB_HOST|DB_PORT)" | sort

# Проверяем порты
echo ""
echo "🔍 Проверка активных портов..."
docker exec okypbot_app ss -tulpn | grep -E ":800[01]" || echo "Не удалось определить порты"

# Тестируем endpoints
echo ""
echo "🌐 Тестирование endpoints..."

# Прямое подключение к приложению
docker exec okypbot_app curl -s "http://localhost:8001/health" -m 5 > /dev/null && echo "✅ Приложение на порту 8001 работает" || echo "❌ Приложение на порту 8001 недоступно"

# Через nginx
curl -s "http://localhost:8080/health" -m 5 > /dev/null && echo "✅ nginx → приложение работает" || echo "❌ nginx → приложение недоступно"

# Тестируем webhook endpoint
curl -s -X POST "http://localhost:8080/okdesk-webhook" \
  -H "Content-Type: application/json" \
  -d '{"test": true}' -m 5 > /dev/null && echo "✅ Webhook endpoint доступен" || echo "❌ Webhook endpoint недоступен"

# Показываем последние логи
echo ""
echo "📋 Последние логи приложения:"
docker logs okypbot_app | tail -10

echo ""
echo "✅ Деплой завершен!"
echo ""
echo "📋 Сводка:"
echo "   🌐 Webhook URL: http://ваш-сервер:8080/okdesk-webhook"
echo "   🤖 Telegram бот должен отвечать на команды"
echo "   🐘 PostgreSQL готов к работе"
echo ""
echo "🔧 Если есть проблемы, запустите диагностику:"
echo "   ./diagnose_bot_issues.sh"
echo "   python3 diagnose_telegram_bot.py"
