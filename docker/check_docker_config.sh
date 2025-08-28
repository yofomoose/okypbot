#!/bin/bash
# Скрипт проверки Docker конфигурации для okypbot

echo "🔍 Проверка Docker конфигурации okypbot..."
echo "=========================================="

# Проверяем наличие файлов
echo "📁 Проверка наличия файлов:"

files_to_check=(
    "docker/Dockerfile"
    "docker/docker-compose.prod.yml"
    "requirements.txt"
    "bot_model/classifier.pkl"
    "bot_model/label_encoder.pkl"
    "bot_model/model_metadata.json"
)

for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file - найден"
    else
        echo "❌ $file - отсутствует"
    fi
done

# Проверяем training_examples.pkl (опционально)
if [ -f "bot_model/training_examples.pkl" ]; then
    echo "✅ bot_model/training_examples.pkl - найден (данные обучения)"
else
    echo "⚠️  bot_model/training_examples.pkl - отсутствует (опционально)"
fi

echo ""
echo "🐳 Проверка Docker образов:"

# Проверяем, можем ли мы собрать образ
echo "🏗️  Проверка сборки Docker образа..."
if docker build -f docker/Dockerfile -t okypbot:test . --quiet; then
    echo "✅ Docker образ собирается успешно"
else
    echo "❌ Ошибка сборки Docker образа"
    exit 1
fi

# Проверяем переменные окружения
echo ""
echo "🔧 Проверка переменных окружения:"
echo "Создайте .env файл со следующими переменными:"
echo "  BOT_TOKEN=your_bot_token"
echo "  DB_PASSWORD=your_db_password"
echo "  OKDESK_API_TOKEN=your_okdesk_token"
echo "  OKDESK_BASE_URL=https://your-domain.okdesk.ru"
echo "  OKDESK_WEBHOOK_SECRET=your_webhook_secret"
echo "  ADMIN_IDS=123456789,987654321"

# Проверяем конфигурацию docker-compose
echo ""
echo "📋 Проверка docker-compose конфигурации:"
if docker-compose -f docker/docker-compose.prod.yml config --quiet; then
    echo "✅ docker-compose.prod.yml - валидная конфигурация"
else
    echo "❌ docker-compose.prod.yml - ошибки в конфигурации"
fi

echo ""
echo "🎉 Проверка завершена!"
echo ""
echo "💡 Для запуска используйте:"
echo "  docker-compose -f docker/docker-compose.prod.yml up -d"
echo ""
echo "📊 Для просмотра логов:"
echo "  docker-compose -f docker/docker-compose.prod.yml logs -f bot"
