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

# Проверка и создание .env
if [ ! -f .env ]; then
    if [ -f .env.production ]; then
        echo "📝 Копирование .env.production в .env"
        cp .env.production .env
    else
        echo "❌ Файл .env.production не найден!"
        echo "Создайте файл .env.production с настройками или скопируйте .env.example"
        exit 1
    fi
fi

# Загрузка переменных окружения
echo "🔧 Загрузка переменных окружения..."
set -a
source .env
set +a

# Копирование .env в папку docker для docker-compose
cp .env docker/.env

# Проверка критических переменных
if [ -z "$BOT_TOKEN" ] || [ -z "$DB_PASSWORD" ]; then
    echo "❌ Критические переменные не заданы!"
    echo "Проверьте .env файл - должны быть заполнены BOT_TOKEN и DB_PASSWORD"
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
$DOCKER_COMPOSE -f docker/docker-compose.prod.yml exec bot curl -f http://localhost:8000/health || echo "⚠️ Bot недоступен"

# Получение IP для nginx
BOT_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' okypbot_app || echo ":8000")
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
