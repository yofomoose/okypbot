#!/bin/bash
# Скрипт для тестирования вебхука с правильной подписью

# Используйте фактический секрет из переменных окружения
SECRET=$(docker exec okypbot_app bash -c 'echo $OKDESK_WEBHOOK_SECRET')

# Если секрет не настроен, используем пустую строку для тестирования
if [ -z "$SECRET" ]; then
    echo "ВНИМАНИЕ: Секрет OKDESK_WEBHOOK_SECRET не настроен, используем пустую строку"
    SECRET=""
fi

# Подготавливаем тестовые данные
JSON='{"event":{"event_type":"test_event"},"issue":{"id":12345}}'

# Вычисляем подпись (HMAC-SHA256)
SIGNATURE=$(echo -n "$JSON" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $NF}')

echo "Тестовые данные: $JSON"
echo "Вычисленная подпись: $SIGNATURE"

# Отправляем запрос с подписью
echo "Отправка запроса с правильной подписью..."
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "X-Okdesk-Signature: sha256=$SIGNATURE" \
  -d "$JSON" \
  http://localhost:8080/okdesk-webhook

echo ""
echo "Запрос отправлен. Проверьте логи бота для подтверждения получения запроса."
