# 🚀 Инструкция по тестированию webhook на продакшене

## 📋 Предварительные требования

1. **Docker Compose** должен быть запущен:
   ```bash
   docker-compose -f docker/docker-compose.prod.yml up -d
   ```

2. **Переменные окружения** должны быть настроены в `.env` файле:
   - `OKDESK_WEBHOOK_SECRET` - секрет для подписи webhook
   - `OKDESK_BASE_URL` - URL вашего Okdesk
   - `TELEGRAM_BOT_TOKEN` - токен Telegram бота

## 🧪 Шаг 1: Проверка состояния системы

Запустите скрипт проверки состояния:

```bash
chmod +x check_docker_status.sh
./check_docker_status.sh
```

**Ожидаемый результат:**
- Все контейнеры должны быть в состоянии "Up"
- Порты 80, 8000, 5432 должны быть открыты
- Нет ошибок в логах

## 🌐 Шаг 2: Тестирование webhook эндпоинтов

### Вариант A: Использование Python скрипта (рекомендуется)

```bash
python test_webhook.py --url https://your-domain.com --secret your_webhook_secret
```

### Вариант B: Ручное тестирование с curl

```bash
# Проверка health эндпоинта
curl -X GET https://your-domain.com/health

# Тест webhook с образцом данных
curl -X POST https://your-domain.com/okdesk-webhook \
  -H "Content-Type: application/json" \
  -H "X-Okdesk-Signature: test_signature" \
  -d '{
    "event": "new_comment",
    "data": {
      "issue_id": "12345",
      "comment": "Тестовый комментарий",
      "author": "test@example.com"
    }
  }'
```

## 📊 Шаг 3: Мониторинг в реальном времени

В отдельном терминале запустите мониторинг логов:

```bash
chmod +x monitor_webhook_logs.sh
./monitor_webhook_logs.sh
```

## 🔍 Шаг 4: Проверка в Okdesk

1. **Перейдите в настройки webhook** в вашем Okdesk
2. **Убедитесь что URL** указан правильно: `https://your-domain.com/okdesk-webhook`
3. **Проверьте секрет** подписи
4. **Отправьте тестовый webhook** из интерфейса Okdesk

## ⚠️ Возможные проблемы и решения

### Проблема: 502 Bad Gateway
```
✅ Решение: Проверьте что контейнер okypbot_app запущен
docker logs okypbot_app
```

### Проблема: 401 Unauthorized
```
✅ Решение: Проверьте OKDESK_WEBHOOK_SECRET в .env файле
```

### Проблема: Connection refused
```
✅ Решение: Проверьте nginx конфигурацию
docker logs okypbot_nginx
```

## 📝 Логи для анализа

- **Webhook логи**: `docker logs okypbot_app | grep webhook`
- **Nginx логи**: `docker logs okypbot_nginx`
- **Сетевые логи**: `docker logs okypbot_app | grep -i error`

## 🎯 Ожидаемые результаты тестирования

✅ **Health check** возвращает `{"status": "healthy"}`
✅ **Webhook endpoint** принимает POST запросы
✅ **Signature verification** работает корректно
✅ **Логи** показывают обработку событий
✅ **Telegram бот** получает уведомления

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи всех контейнеров
2. Убедитесь в корректности переменных окружения
3. Проверьте сетевые настройки firewall
4. Свяжитесь с администратором системы
