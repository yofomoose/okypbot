#!/bin/bash
# Скрипт для диагностики webhook на продакшене

echo "🔍 Проверка webhook сервера"
echo "=================================="

# Проверяем конфигурацию nginx
echo "📄 Текущая конфигурация nginx:"
docker exec -it okypbot_nginx cat /etc/nginx/conf.d/default.conf

echo -e "\n🌐 Проверка доступности эндпоинтов:"
echo "--------------------------------"

# Проверяем корневой URL
echo -n "🔍 Корневой эндпоинт (/) ... "
ROOT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -k https://okbot.teftelyatun.ru/)
if [ "$ROOT_STATUS" -eq 200 ]; then
  echo "✅ OK ($ROOT_STATUS)"
else
  echo "❌ ОШИБКА ($ROOT_STATUS)"
fi

# Проверяем health эндпоинт
echo -n "🔍 Health эндпоинт (/health) ... "
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -k https://okbot.teftelyatun.ru/health)
if [ "$HEALTH_STATUS" -eq 200 ]; then
  echo "✅ OK ($HEALTH_STATUS)"
else
  echo "❌ ОШИБКА ($HEALTH_STATUS)"
fi

# Проверяем webhook эндпоинт (HEAD запрос)
echo -n "🔍 Webhook эндпоинт (/okdesk-webhook) ... "
WEBHOOK_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -k -I https://okbot.teftelyatun.ru/okdesk-webhook)
if [ "$WEBHOOK_STATUS" -eq 200 ] || [ "$WEBHOOK_STATUS" -eq 405 ]; then
  echo "✅ OK ($WEBHOOK_STATUS) - 405 также считается успехом, т.к. может быть ограничение на HEAD запросы"
else
  echo "❌ ОШИБКА ($WEBHOOK_STATUS)"
fi

echo -e "\n🔌 Проверка сетевой связности между контейнерами:"
echo "--------------------------------"
echo -n "🔍 Bot контейнер доступен из nginx ... "
CONTAINER_CHECK=$(docker exec -it okypbot_nginx curl -s -o /dev/null -w "%{http_code}" http://bot:8000/)
if [ "$CONTAINER_CHECK" -eq 200 ]; then
  echo "✅ OK ($CONTAINER_CHECK)"
else
  echo "❌ ОШИБКА ($CONTAINER_CHECK)"
fi

echo -e "\n📊 Проверка маршрутов FastAPI:"
echo "--------------------------------"
echo "🔍 Зарегистрированные маршруты в FastAPI:"
docker exec -it okypbot_app python -c "from services.webhook_server import app; print('Зарегистрированные маршруты:'); [print(f'{route.path} [{route.methods}]') for route in app.routes]"

echo -e "\n📋 Дополнительные команды для диагностики:"
echo "--------------------------------"
echo "📝 Просмотр логов: docker logs okypbot_app | grep -i 'webhook'"
echo "📝 Проверка webhook подписи: OKDESK_WEBHOOK_SECRET=your_secret python3 test_webhook_simple.py"
echo "📝 Перезагрузка nginx: docker exec -it okypbot_nginx nginx -s reload"
echo "📝 Перезапуск всех сервисов: docker-compose -f docker/docker-compose.prod.yml restart"
