#!/bin/bash

echo "🔧 Исправление проблем с портами и конфигурацией"
echo "=============================================="

# 1. Останавливаем контейнеры
echo "🛑 Останавливаем контейнеры..."
docker-compose down

# 2. Обновляем переменные окружения для правильного порта
echo "📝 Обновляем переменные окружения..."
export WEBHOOK_PORT=8001

# 3. Обновляем requirements.txt для правильной версии scikit-learn
echo "📦 Обновляем scikit-learn до версии 1.4.0..."
if [ -f "../requirements.txt" ]; then
    sed -i 's/scikit-learn==1.3.0/scikit-learn==1.4.0/' ../requirements.txt
    echo "✅ requirements.txt обновлен"
else
    echo "⚠️ requirements.txt не найден"
fi

# 4. Пересобираем образ с новыми зависимостями
echo "🔨 Пересобираем образ с обновленными зависимостями..."
docker-compose build --no-cache okypbot

# 5. Запускаем с правильной конфигурацией
echo "🚀 Запускаем с исправленной конфигурацией..."
docker-compose --env-file .env.production up -d

# 6. Ждем запуска
echo "⏳ Ждем запуска сервисов..."
sleep 20

# 7. Проверяем результат
echo "📊 Проверяем статус..."
docker-compose ps

echo ""
echo "🔍 Проверяем порты приложения..."
docker exec okypbot_app netstat -tulpn 2>/dev/null | grep :800 || echo "Проверяем через ss..."
docker exec okypbot_app ss -tulpn 2>/dev/null | grep :800 || echo "Не удалось проверить порты"

echo ""
echo "🌐 Тестируем webhook endpoints..."
curl -s "http://localhost:8080/health" && echo " ✅ nginx health OK" || echo " ❌ nginx health failed"
curl -s "http://localhost:8080/okdesk-webhook" -X POST -H "Content-Type: application/json" -d '{"test": true}' && echo " ✅ webhook endpoint OK" || echo " ❌ webhook endpoint failed"

echo ""
echo "📋 Последние логи приложения..."
docker logs okypbot_app | tail -5

echo ""
echo "✅ Исправления применены!"
echo "🤖 Попробуйте отправить команду боту в Telegram"
