#!/bin/bash
# Скрипт для исправления проблем с системой

echo "🔧 Исправление проблем с okypbot системой..."
echo "=============================================="

# 1. Исправляем проблемы с базой данных
echo "📊 Шаг 1: Исправление проблем с базой данных..."
python fix_database_issues.py
if [ $? -eq 0 ]; then
    echo "✅ База данных исправлена"
else
    echo "❌ Ошибка исправления базы данных"
    exit 1
fi

# 2. Проверяем переменные окружения
echo ""
echo "🔍 Шаг 2: Проверка переменных окружения..."
if [ -f ".env" ]; then
    echo "✅ Файл .env найден"
    # Проверяем основные переменные
    if grep -q "BOT_TOKEN=" .env && grep -q "OKDESK_API_TOKEN=" .env; then
        echo "✅ Основные переменные окружения настроены"
    else
        echo "⚠️ Проверьте переменные BOT_TOKEN и OKDESK_API_TOKEN в .env"
    fi
else
    echo "❌ Файл .env не найден"
    echo "📝 Создайте .env файл на основе .env.example"
fi

# 3. Проверяем зависимости
echo ""
echo "📦 Шаг 3: Проверка зависимостей..."
python -c "import aiogram, fastapi, sqlalchemy, transformers" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Основные зависимости установлены"
else
    echo "⚠️ Некоторые зависимости могут отсутствовать"
    echo "📝 Установите зависимости: pip install -r requirements.txt"
fi

# 4. Тестируем webhook
echo ""
echo "🌐 Шаг 4: Тестирование webhook..."
if [ -f "test_webhook.py" ]; then
    echo "📝 Для тестирования webhook выполните:"
    echo "   python test_webhook.py --url https://your-domain.com --secret your_webhook_secret"
else
    echo "❌ Файл test_webhook.py не найден"
fi

echo ""
echo "✅ Исправления завершены!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Перезапустите Docker контейнеры: docker-compose restart"
echo "2. Проверьте логи: docker logs okypbot_app"
echo "3. Протестируйте webhook если необходимо"
echo ""
echo "📞 Если проблемы сохраняются, проверьте:"
echo "- Корректность переменных окружения в .env"
echo "- Доступность Okdesk API"
echo "- Настройки firewall и сети"
