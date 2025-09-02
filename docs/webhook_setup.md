# 🚀 Настройка Webhook в Okdesk

Для правильной работы webhook-интеграции между Okdesk и OkypBot необходимо выполнить следующие шаги:

## 1️⃣ Проверка доступности webhook-сервера

Перед настройкой интеграции в Okdesk убедитесь, что webhook-сервер доступен:

```bash
# Запустите скрипт проверки
./scripts/check_webhook.sh
```

Все эндпоинты должны быть доступны и отвечать с кодом 200.

## 2️⃣ Настройка webhook в интерфейсе Okdesk

1. Войдите в админ-панель Okdesk
2. Перейдите в раздел "Настройки" -> "Интеграции" -> "Webhook"
3. Нажмите "Добавить Webhook"
4. Заполните форму:

   * **URL**: `https://okbot.teftelyatun.ru/okdesk-webhook`
   * **Секрет**: `<ваш_секретный_ключ>` (тот же, что в переменной `OKDESK_WEBHOOK_SECRET` в файле `.env.production`)
   * **События**:
     * ✅ Создание заявки
     * ✅ Комментарий добавлен
     * ✅ Изменен статус заявки
     * ✅ Заявка назначена
   * **Формат**: JSON

5. Нажмите "Сохранить"

## 3️⃣ Проверка работоспособности

### Проверка с реальными данными:

1. Создайте тестовую заявку в Okdesk
2. Добавьте комментарий к заявке
3. Проверьте логи бота:

```bash
docker logs okypbot_app | grep -i "webhook\|comment\|issue"
```

### Проверка с тестовым скриптом:

1. Добавьте тестовую связь между заявкой и пользователем:

```bash
# На сервере выполните:
docker exec -it okypbot_app python /app/scripts/add_test_issue_link.py <ID_заявки> <ID_пользователя_Telegram>
```

2. Отправьте тестовый webhook запрос:

```bash
# На сервере выполните:
OKDESK_WEBHOOK_SECRET=<ваш_секрет> python /app/test_webhook_simple.py <ID_заявки>
```

3. Проверьте, получил ли пользователь уведомление в Telegram

## 4️⃣ Возможные проблемы и решения

### Ошибка 401 (Invalid signature)

Проблема с подписью webhook. Убедитесь, что:

1. В Okdesk и в переменной `OKDESK_WEBHOOK_SECRET` указан одинаковый секрет
2. Для тестирования можно временно отключить проверку подписи:

```bash
# На сервере выполните:
docker exec -it okypbot_app python /app/scripts/disable_webhook_signature.py /app/services/webhook_server.py
docker-compose -f docker/docker-compose.prod.yml restart bot
```

### Ошибка 404 (Not Found)

1. Проверьте конфигурацию nginx:

```bash
docker exec -it okypbot_nginx cat /etc/nginx/conf.d/default.conf
```

2. Убедитесь, что в конфигурации есть правильное проксирование:

```nginx
location /okdesk-webhook {
    proxy_pass http://bot:8000/okdesk-webhook;
    # ...остальные параметры...
}
```

3. Перезагрузите конфигурацию nginx:

```bash
docker exec -it okypbot_nginx nginx -s reload
```

### Пользователи не получают уведомления

1. Убедитесь, что в базе данных есть связь между заявкой и пользователем Telegram
2. Проверьте логи на наличие ошибок
3. Временно включите дополнительное логирование в функциях обработки webhook
