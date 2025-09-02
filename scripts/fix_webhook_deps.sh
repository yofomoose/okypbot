#!/bin/bash
# Скрипт для исправления ошибок с отсутствующими зависимостями FastAPI/uvicorn

echo "=== Скрипт исправления зависимостей для FastAPI ==="

# Проверяем, запущен ли Docker
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker не запущен или у вас нет прав для его использования!"
    exit 1
fi

# Проверяем, существует ли контейнер okypbot_app
if ! docker ps -a | grep -q okypbot_app; then
    echo "❌ Контейнер okypbot_app не найден!"
    exit 1
fi

echo "✅ Docker работает и контейнер okypbot_app найден"

# Устанавливаем необходимые пакеты в контейнер
echo "Установка FastAPI и uvicorn в контейнер..."
docker exec -it okypbot_app pip install fastapi==0.100.1 uvicorn[standard]==0.23.2

# Проверка успешности установки
if [ $? -eq 0 ]; then
    echo "✅ Зависимости успешно установлены"
else
    echo "❌ Ошибка при установке зависимостей!"
    exit 1
fi

# Перезапускаем контейнер
echo "Перезапуск контейнера okypbot_app..."
docker restart okypbot_app

# Проверяем, успешно ли перезапустился контейнер
if [ $? -eq 0 ]; then
    echo "✅ Контейнер успешно перезапущен"
else
    echo "❌ Ошибка при перезапуске контейнера!"
    exit 1
fi

# Ждем немного для запуска сервисов
echo "Ожидание запуска сервисов..."
sleep 5

# Проверяем работоспособность webhook-сервера
echo "Проверка работоспособности webhook-сервера..."
WEBHOOK_TEST=$(docker exec -it okypbot_nginx curl -s http://bot:8000/health)

if [[ $WEBHOOK_TEST == *"healthy"* ]]; then
    echo "✅ Webhook-сервер работает корректно!"
    echo "Ответ: $WEBHOOK_TEST"
else
    echo "❌ Webhook-сервер не отвечает или отвечает с ошибкой!"
    echo "Просмотр логов контейнера:"
    docker logs --tail 20 okypbot_app
fi

echo "=== Исправление завершено ==="
echo "Для проверки работы вебхука выполните:"
echo "curl -X POST http://localhost:8080/okdesk-webhook -H \"Content-Type: application/json\" -d '{\"event\":{\"event_type\":\"test_event\"},\"issue\":{\"id\":12345}}'"
