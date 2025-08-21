#!/bin/bash

# Скрипт полного развертывания

echo "🚀 Полное развертывание OkypBot..."

# Функция для определения команды docker compose
get_docker_compose_cmd() {
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    elif docker compose version &> /dev/null; then
        echo "docker compose"
    else
        echo "❌ Docker Compose не найден!"
        echo "Установите Docker Compose:"
        echo "  Ubuntu/Debian: apt-get install docker-compose-plugin"
        echo "  CentOS/RHEL: yum install docker-compose-plugin"
        echo "  Или установите standalone: https://docs.docker.com/compose/install/"
        exit 1
    fi
}

DOCKER_COMPOSE=$(get_docker_compose_cmd)
echo "📦 Используется: $DOCKER_COMPOSE"

# Проверка .env
if [ ! -f .env ]; then
    echo "📝 Создайте .env файл"
    cp .env.production .env
    exit 1
fi

# Остановка всех сервисов
$DOCKER_COMPOSE -f docker/docker-compose.prod.yml down

# Сборка образов
echo "🔨 Сборка образов..."
$DOCKER_COMPOSE -f docker/docker-compose.prod.yml build

# Запуск всех сервисов
echo "🚀 Запуск сервисов..."
$DOCKER_COMPOSE -f docker/docker-compose.prod.yml up -d

# Ожидание готовности
echo "⏳ Ожидание готовности сервисов..."
sleep 30

# Проверка статуса
echo "📊 Статус сервисов:"
$DOCKER_COMPOSE -f docker/docker-compose.prod.yml ps

# Проверка логов
echo "📝 Последние логи:"
$DOCKER_COMPOSE -f docker/docker-compose.prod.yml logs --tail=10

echo "✅ Развертывание завершено!"
echo "🔗 Проверьте webhook endpoint: http://your-domain/webhook/"

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
