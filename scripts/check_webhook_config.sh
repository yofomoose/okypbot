# Скрипт для проверки конфигурации вебхуков в OkypBot

# Функция для проверки внешнего URL
function test_url() {
    url=$1
    expected_status=$2
    method=${3:-GET}
    
    echo "Проверка $method $url (ожидаемый статус: $expected_status)"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" -X GET "$url")
    elif [ "$method" = "HEAD" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" -X HEAD "$url")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d '{"test":"data"}' "$url")
    fi
    
    if [ "$response" = "$expected_status" ]; then
        echo "✅ Успешно! Статус: $response"
    else
        echo "❌ Ошибка! Ожидался статус $expected_status, получен $response"
    fi
    echo ""
}

# Проверяем доступность контейнеров
echo "Проверка доступности контейнеров..."
docker ps | grep okypbot_nginx || { echo "❌ Контейнер nginx не запущен!"; exit 1; }
docker ps | grep okypbot_app || { echo "❌ Контейнер бота не запущен!"; exit 1; }

# Проверяем внутреннее соединение между контейнерами
echo "Проверка внутреннего соединения между контейнерами..."
docker exec -it okypbot_nginx curl -s http://bot:8000/health
echo ""

# Проверяем конфигурацию nginx
echo "Проверка конфигурации nginx..."
docker exec -it okypbot_nginx cat /etc/nginx/conf.d/default.conf | grep "proxy_pass http://bot:8000/okdesk-webhook" || echo "❌ Неправильная конфигурация для /okdesk-webhook!"
echo ""

# Проверяем внешние URL
echo "Проверка внешних URL..."
test_url "http://localhost:8080/" 200
test_url "http://localhost:8080/health" 200
test_url "http://localhost:8080/okdesk-webhook" 405 "POST"

echo "Проверки завершены. Если все тесты пройдены успешно, вебхук должен работать корректно."
echo "Убедитесь, что внешний URL вебхука настроен в CRM-системе правильно."
