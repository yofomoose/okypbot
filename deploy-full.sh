#!/bin/bash

# Скрипт полного развертывания

echo "🚀 Полное развертывание OkypBot..."

# Проверка .env
if [ ! -f .env ]; then
    echo "📝 Создайте .env файл"
    cp .env.production .env
    exit 1
fi

# Остановка всех сервисов
docker-compose -f docker-compose.prod.yml down

# Сборка образов
echo "🔨 Сборка образов..."
docker-compose -f docker-compose.prod.yml build

# Запуск всех сервисов
echo "🚀 Запуск сервисов..."
docker-compose -f docker-compose.prod.yml up -d

# Ожидание готовности
echo "⏳ Ожидание готовности сервисов..."
sleep 30

# Проверка статуса
echo "📊 Статус сервисов:"
docker-compose -f docker-compose.prod.yml ps

# Проверка здоровья
echo "🔍 Проверка health check..."
docker-compose -f docker-compose.prod.yml exec bot curl -f http://localhost:8000/health || echo "⚠️ Bot недоступен"

# Получение IP для nginx
BOT_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' okypbot_app)
echo "🔍 IP бота для nginx: $BOT_IP:8000"

echo "✅ Развертывание завершено!"
echo ""
echo "📋 Подключение к БД:"
echo "   Host: $(hostname -I | awk '{print $1}')"
echo "   Port: 5433"
echo "   Database: okypbot"
echo "   User: postgres"
echo ""
echo "🌐 Webhook: http://ваш-сервер/okdesk-webhook"
