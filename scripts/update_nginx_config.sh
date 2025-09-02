#!/bin/bash
# Скрипт для обновления конфигурации nginx и проверки работоспособности

# Путь к файлу конфигурации
NGINX_CONFIG="/etc/nginx/conf.d/default.conf"
BACKUP_CONFIG="/etc/nginx/conf.d/default.conf.bak"

# Создаем бэкап текущей конфигурации
echo "Создание бэкапа текущей конфигурации nginx..."
docker exec okypbot_nginx cp $NGINX_CONFIG $BACKUP_CONFIG

# Обновляем конфигурацию nginx в контейнере
echo "Обновление конфигурации nginx..."
cat nginx/default.conf.new | docker exec -i okypbot_nginx tee $NGINX_CONFIG > /dev/null

# Проверяем синтаксис новой конфигурации
echo "Проверка синтаксиса новой конфигурации..."
SYNTAX_CHECK=$(docker exec okypbot_nginx nginx -t 2>&1)
if [[ $? -ne 0 ]]; then
    echo "ОШИБКА: Неверный синтаксис в конфигурации nginx:"
    echo "$SYNTAX_CHECK"
    echo "Восстанавливаем предыдущую конфигурацию..."
    docker exec okypbot_nginx cp $BACKUP_CONFIG $NGINX_CONFIG
    exit 1
fi

# Перезапускаем nginx для применения новой конфигурации
echo "Перезапуск nginx..."
docker exec okypbot_nginx nginx -s reload

# Проверяем работоспособность после обновления
echo "Проверка работоспособности..."
sleep 2
echo "Проверка корневого маршрута..."
curl -s http://localhost:8080/
echo ""
echo "Проверка маршрута health..."
curl -s http://localhost:8080/health
echo ""
echo "Проверка маршрута okdesk-webhook (должен вернуть 405 Method Not Allowed, т.к. это POST эндпоинт)..."
curl -s -I http://localhost:8080/okdesk-webhook
echo ""

echo "Обновление конфигурации завершено. Проверьте результаты выше."
echo "Для окончательной проверки выполните внешний запрос к вашему серверу."
