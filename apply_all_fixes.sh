#!/bin/bash
# Скрипт для применения всех исправлений и перезапуска системы

echo "🔧 Применение всех исправлений и перезапуск системы..."
echo "======================================================="

# 1. Исправляем конфигурацию aiogram
echo "📝 Шаг 1: Исправление конфигурации aiogram..."
python fix_aiogram_config.py
if [ $? -eq 0 ]; then
    echo "✅ Конфигурация aiogram исправлена"
else
    echo "❌ Ошибка исправления aiogram"
    exit 1
fi

# 2. Исправляем проблемы с базой данных
echo ""
echo "📊 Шаг 2: Исправление проблем с базой данных..."
python fix_database_issues.py
if [ $? -eq 0 ]; then
    echo "✅ База данных исправлена"
else
    echo "❌ Ошибка исправления базы данных"
    exit 1
fi

# 3. Перезапускаем Docker контейнеры
echo ""
echo "🐳 Шаг 3: Перезапуск Docker контейнеров..."
if command -v docker-compose &> /dev/null; then
    echo "Останавливаем контейнеры..."
    docker-compose -f docker/docker-compose.prod.yml down

    echo "Запускаем контейнеры..."
    docker-compose -f docker/docker-compose.prod.yml up -d

    if [ $? -eq 0 ]; then
        echo "✅ Контейнеры успешно перезапущены"
    else
        echo "❌ Ошибка перезапуска контейнеров"
        exit 1
    fi
else
    echo "⚠️ docker-compose не найден, пропускаем перезапуск"
fi

# 4. Ждем запуска и проверяем статус
echo ""
echo "⏳ Шаг 4: Ожидание запуска системы..."
sleep 10

# 5. Проверяем статус
echo ""
echo "🔍 Шаг 5: Проверка статуса..."
if [ -f "check_docker_status.sh" ]; then
    ./check_docker_status.sh
else
    echo "⚠️ Скрипт check_docker_status.sh не найден"
fi

echo ""
echo "✅ Все исправления применены!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Проверьте логи: docker logs okypbot_app"
echo "2. Протестируйте webhook: python test_webhook.py --url https://your-domain.com"
echo "3. Проверьте работу бота в Telegram"
echo ""
echo "📞 Если проблемы сохраняются:"
echo "- Проверьте переменные окружения в .env"
echo "- Убедитесь в доступности Okdesk API"
echo "- Проверьте логи nginx: docker logs okypbot_nginx"
