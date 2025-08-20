#!/bin/bash

# Скрипт развертывания OkypBot на сервере с n8n

echo "🚀 Развертывание OkypBot (интеграция с n8n)..."

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен"
    exit 1
fi

# Создание директорий
mkdir -p data logs

# Проверка сети n8n
if ! docker network ls | grep -q "n8n-net"; then
    echo "📝 Создание сети n8n-net..."
    docker network create n8n-net
fi

# Проверка .env файла
if [ ! -f .env ]; then
    echo "📝 Создайте .env файл на основе .env.production"
    cp .env.production .env
    echo "✏️  Отредактируйте .env файл с вашими данными"
    exit 1
fi

# Остановка предыдущих контейнеров
echo "🛑 Остановка предыдущих контейнеров..."
docker-compose down

# Сборка и запуск
echo "🔨 Сборка контейнеров..."
docker-compose build

echo "🚀 Запуск сервисов..."
docker-compose up -d

# Проверка статуса
echo "📊 Проверка статуса сервисов..."
sleep 10
docker-compose ps

# Получение IP контейнера для nginx
BOT_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker-compose ps -q bot))
echo "🔍 IP контейнера бота: $BOT_IP"

echo "✅ Развертывание завершено!"
echo ""
echo "📋 Настройка nginx:"
echo "   1. Добавьте в ваш nginx.conf upstream:"
echo "      upstream okypbot_backend { server $BOT_IP:8000; }"
echo "   2. Добавьте location для webhook в server блок"
echo "   3. Перезагрузите nginx: sudo nginx -s reload"
echo ""
echo "🌐 Webhook URL: http://ваш-домен.com/okdesk-webhook"
echo ""
echo "📋 Полезные команды:"
echo "   docker-compose logs -f bot       # Логи бота"
echo "   docker-compose restart bot      # Перезапуск бота"
echo "   docker inspect okypbot_bot_1    # IP адрес контейнера"
