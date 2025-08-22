#!/bin/bash
set -e

echo "🔧 Подготовка окружения для okypbot..."

# Создание директорий для хранения данных
echo "📁 Создание директорий..."
sudo mkdir -p /var/lib/okypbot/{postgres/{data,backup},ml/{models,backups,cache},logs,temp}

# Установка прав доступа
echo "🔐 Настройка прав доступа..."
sudo chown -R 999:999 /var/lib/okypbot/postgres
sudo chmod -R 700 /var/lib/okypbot/postgres/data
sudo chmod -R 755 /var/lib/okypbot/postgres/backup

sudo chown -R 1000:1000 /var/lib/okypbot/ml
sudo chmod -R 777 /var/lib/okypbot/ml
sudo chmod -R 777 /var/lib/okypbot/logs
sudo chmod -R 777 /var/lib/okypbot/temp

# Очистка старых томов Docker
echo "🧹 Очистка старых томов..."
docker volume rm docker_postgres_data docker_postgres_backup docker_ml_models docker_ml_backups docker_ml_cache docker_bot_logs docker_bot_data 2>/dev/null || true

# Остановка и удаление старых контейнеров
echo "🛑 Остановка старых контейнеров..."
docker-compose -f docker/docker-compose.prod.yml down -v 2>/dev/null || true

echo "✅ Окружение подготовлено!"
echo "📋 Теперь можно запустить:"
echo "docker-compose -f docker/docker-compose.prod.yml up -d"
