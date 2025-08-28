#!/bin/bash
# Скрипт для проверки состояния Docker контейнеров и логов

echo "🔍 Проверка состояния Docker контейнеров..."
echo "========================================"

# Проверка запущенных контейнеров
echo "📋 Запущенные контейнеры:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo -e "\n📊 Использование ресурсов:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo -e "\n🔍 Проверка логов веб-сервера:"
echo "========================================"

# Логи основного приложения
echo "📝 Логи okypbot_app (последние 20 строк):"
docker logs --tail 20 okypbot_app 2>/dev/null || echo "❌ Контейнер okypbot_app не найден"

echo -e "\n🌐 Логи nginx (последние 20 строк):"
docker logs --tail 20 okypbot_nginx 2>/dev/null || echo "❌ Контейнер okypbot_nginx не найден"

echo -e "\n🗄️ Логи PostgreSQL (последние 10 строк):"
docker logs --tail 10 okypbot_postgres 2>/dev/null || echo "❌ Контейнер okypbot_postgres не найден"

echo -e "\n🔍 Проверка сетевых подключений:"
echo "========================================"

# Проверка открытых портов
echo "📡 Открытые порты:"
netstat -tlnp 2>/dev/null | grep -E "(80|8000|5432)" || ss -tlnp | grep -E "(80|8000|5432)" || echo "❌ Не удалось проверить порты"

echo -e "\n✅ Проверка завершена!"
