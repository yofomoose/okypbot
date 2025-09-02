# Руководство по настройке Webhook в Okdesk

## 🔗 Настройка Webhook для двусторонней синхронизации комментариев

### Шаг 1: Настройка в админке Okdesk

1. **Войдите в админку Okdesk** как администратор
2. **Перейдите в раздел "API и интеграции"** или "Настройки" → "Webhook"
3. **Добавьте новый webhook** со следующими настройками:

```
URL: http://your-domain.com:8001/okdesk-webhook
или: https://your-domain.com/okdesk-webhook

События для отслеживания:
✅ new_comment - Новый комментарий  
✅ status_changed - Изменение статуса
✅ assignee_changed - Изменение исполнителя
✅ new_issue - Новая заявка (опционально)

Метод: POST
Формат: JSON
```

### Шаг 2: Запуск webhook сервера

```bash
# Локально для тестирования
python -m uvicorn services.webhook_server:app --host 0.0.0.0 --port 8001

# В продакшене через Docker
docker-compose up -d
```

### Шаг 3: Проверка работы

1. **Проверьте доступность эндпоинта:**
```bash
curl http://your-domain:8001/health
# Ответ: {"status":"healthy","service":"okdesk-webhook-handler"}
```

2. **Протестируйте webhook вручную:**
```bash
curl -X POST http://your-domain:8001/okdesk-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "event": {
      "event_type": "new_comment"
    },
    "issue": {
      "id": 70
    }
  }'
```

### Шаг 4: Настройка маппинга сотрудников

Создайте файл `database/employee_mapping.json`:

```json
{
  "1": {
    "okdesk_id": 1,
    "telegram_id": 123456789,
    "name": "Юлия Краева",
    "role": "specialist"
  },
  "2": {
    "okdesk_id": 2, 
    "telegram_id": 987654321,
    "name": "Иван Поддержкин",
    "role": "specialist"
  }
}
```

### Шаг 5: Тестирование полного цикла

1. **Создайте тестового пользователя в Telegram боте**
2. **Зарегистрируйте пользователя**
3. **Создайте заявку через бота**
4. **Добавьте комментарий в Okdesk как специалист**
5. **Проверьте, что клиент получил уведомление в Telegram**
6. **Ответьте как клиент в Telegram**
7. **Проверьте, что комментарий появился в Okdesk**

## 🧪 Готовые тестовые данные

Мы создали для вас тестовые данные:

- **Контакт ID:** 22 (Кирилл Клиентов)
- **Заявка ID:** 70 (Проблема с принтером)
- **Ссылка:** https://yapomogu55.okdesk.ru/issues/70

## 📋 Workflow системы

### Когда специалист отвечает в Okdesk:

1. Okdesk отправляет webhook с типом `new_comment`
2. Наш сервер получает событие
3. Система находит клиента по issue_id
4. Отправляется уведомление в Telegram клиенту
5. Клиент видит сообщение с кнопкой "Ответить"

### Когда клиент отвечает в Telegram:

1. Клиент нажимает "Ответить" и пишет сообщение
2. Бот обрабатывает сообщение
3. Комментарий добавляется в Okdesk через API
4. Специалист видит ответ в системе

### Когда специалист отвечает в Telegram:

1. Специалист получает уведомление о сообщении клиента
2. Нажимает "Ответить" и пишет ответ
3. Комментарий добавляется в Okdesk
4. Клиент получает уведомление в Telegram

## 🔧 Конфигурация

Убедитесь что в `.env` файле установлены:

```env
# Основные настройки
BOT_TOKEN=your_telegram_bot_token
OKDESK_API_TOKEN=your_okdesk_api_token
OKDESK_BASE_URL=https://yapomogu55.okdesk.ru
OKDESK_AUTHOR_ID=1

# Webhook настройки
WEBHOOK_ENABLED=true
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8001

# Администраторы (ID Telegram)
ADMIN_IDS=123456789,987654321
```

## 🚀 Продакшен деплой

### Nginx конфигурация

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /okdesk-webhook {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Docker Compose

```yaml
version: '3.8'
services:
  okypbot:
    build: .
    ports:
      - "8001:8001"
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - OKDESK_API_TOKEN=${OKDESK_API_TOKEN}
      - OKDESK_BASE_URL=${OKDESK_BASE_URL}
    volumes:
      - ./database:/app/database
      - ./logs:/app/logs
    restart: unless-stopped
```

## 📊 Мониторинг и логирование

### Логи webhook событий

```bash
# Просмотр логов webhook
docker-compose logs -f okypbot | grep webhook

# Логи обработки комментариев
docker-compose logs -f okypbot | grep comment
```

### Метрики

- Количество обработанных webhook событий
- Время отклика системы
- Ошибки синхронизации
- Статистика сообщений

## 🔍 Отладка

### Проверка webhook событий

1. **Логи Okdesk:** Проверьте, отправляет ли Okdesk webhook события
2. **Логи нашего сервера:** Смотрите что приходит на эндпоинт
3. **Базы данных:** Проверьте связки пользователей с заявками

### Частые проблемы

1. **Webhook не доходят** - проверьте URL и доступность сервера
2. **Пользователь не найден** - проверьте систему мониторинга заявок
3. **Комментарии не добавляются** - проверьте права API токена
4. **Специалист не найден** - настройте маппинг сотрудников

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `docker-compose logs`
2. Запустите диагностику: `python diagnose_okdesk.py`
3. Протестируйте систему: `python test_comment_sync.py`

---

## ✅ Система готова!

После выполнения всех шагов у вас будет работать полная двусторонняя синхронизация комментариев между Telegram и Okdesk! 🎉
