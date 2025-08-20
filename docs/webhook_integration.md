# Интеграция с Okdesk Webhooks

## Описание

Данный модуль реализует полную интеграцию с официальной системой webhooks Okdesk согласно [официальной документации](https://apidocs.okdesk.ru/webhookdoc/#!obshhee-obshhaya-informacziya).

## Поддерживаемые события

### 1. new_comment - Новый комментарий
```json
{
  "event": {
    "event_type": "new_comment",
    "author": {
      "type": "contact|employee",
      "id": 123,
      "first_name": "Имя",
      "last_name": "Фамилия",
      "name": "Полное имя"
    },
    "comment": {
      "id": 456,
      "content": "Текст комментария",
      "is_public": true,
      "created_at": "2024-12-19T10:30:00Z"
    }
  },
  "issue": {
    "id": 789,
    "title": "Название заявки",
    "contact": {
      "phone": "+7 (900) 123-45-67"
    }
  }
}
```

**Логика обработки:**
- Если `author.type = "contact"` → уведомляем специалиста о сообщении от клиента
- Если `author.type = "employee"` → уведомляем клиента о сообщении от специалиста

### 2. status_changed - Изменение статуса
```json
{
  "event": {
    "event_type": "status_changed",
    "old_status": {
      "id": 1,
      "name": "Новая",
      "code": "new"
    },
    "new_status": {
      "id": 2,
      "name": "В работе", 
      "code": "in_progress"
    }
  },
  "issue": {
    "id": 789,
    "title": "Название заявки"
  }
}
```

**Логика обработки:**
- Уведомляем клиента об изменении статуса заявки

### 3. assignee_changed - Назначение исполнителя
```json
{
  "event": {
    "event_type": "assignee_changed",
    "new_assignee": {
      "id": 555,
      "first_name": "Петр",
      "last_name": "Сидоров",
      "name": "Петр Сидоров"
    }
  },
  "issue": {
    "id": 789,
    "title": "Название заявки"
  }
}
```

**Логика обработки:**
- Уведомляем клиента о назначении специалиста

## Настройка в Okdesk

1. Перейдите в раздел "Администрирование" → "Интеграции" → "Webhooks"
2. Создайте новый webhook со следующими параметрами:
   - **URL:** `https://ваш-домен.com/okdesk-webhook`
   - **Метод:** POST
   - **События:** 
     - Новый комментарий
     - Изменение статуса
     - Назначение исполнителя
3. При необходимости настройте подпись для безопасности

## Безопасность

### Проверка подписи (рекомендуется)
```python
# В config.py добавьте:
OKDESK_WEBHOOK_SECRET = "ваш_секретный_ключ"

# Okdesk будет отправлять заголовок X-Okdesk-Signature
# содержащий HMAC-SHA256 подпись тела запроса
```

### IP-фильтрация
Рекомендуется настроить файрвол для приема webhooks только с IP-адресов Okdesk.

## Структура модуля

```
services/
└── webhook_server.py          # Основной сервер webhooks
    ├── WebhookHandler        # Класс обработки событий
    ├── handle_comment_added   # Обработка комментариев
    ├── handle_status_changed  # Обработка статусов
    └── handle_issue_assigned  # Обработка назначений

test_webhook.py               # Скрипт тестирования
```

## Запуск сервера

### Разработка
```bash
# Запуск webhook сервера
python -c "from services.webhook_server import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8001)"
```

### Продакшн
```bash
# Используйте gunicorn или аналогичный ASGI сервер
gunicorn services.webhook_server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001
```

## Тестирование

### Тестирование локально
```bash
# Запустите сервер в одном терминале
python -c "from services.webhook_server import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8001)"

# В другом терминале запустите тесты
python test_webhook.py
```

### Проверка работоспособности
```bash
curl http://localhost:8001/health
```

## Логирование

Все webhook события логируются с подробной информацией:

```python
logger.info(f"Получен webhook: {event_type}")
logger.info(f"Новый комментарий в заявке {issue_id} от {author_type}: {author_name}")
logger.error(f"Ошибка обработки webhook: {e}")
```

## Интеграция с Telegram ботом

### Связывание пользователей
- **Клиенты:** связываются по номеру телефона из Okdesk контакта
- **Специалисты:** связываются по `okdesk_employee_id` в профиле пользователя

### Уведомления
- Клиенты получают уведомления о:
  - Сообщениях от специалистов
  - Изменении статуса заявки
  - Назначении исполнителя
  
- Специалисты получают уведомления о:
  - Сообщениях от клиентов

## Обработка ошибок

1. **Неверная подпись** → HTTP 401
2. **Некорректный JSON** → HTTP 400  
3. **Пользователь не найден** → логирование предупреждения
4. **Ошибка отправки в Telegram** → логирование ошибки
5. **Общие ошибки** → HTTP 500

## Мониторинг

### Метрики для отслеживания:
- Количество обработанных webhooks по типам
- Время отклика на webhook
- Количество ошибок при обработке
- Успешность доставки уведомлений в Telegram

### Health check endpoint:
```
GET /health
Response: {"status": "healthy", "service": "okdesk-webhook-handler"}
```

## Расширение функциональности

### Добавление новых типов событий:
1. Добавьте обработчик в `WebhookHandler`
2. Добавьте условие в основной роутер
3. Добавьте тест в `test_webhook.py`

### Пример добавления события "new_issue":
```python
async def handle_new_issue(self, data: Dict[Any, Any]):
    """Обработка создания новой заявки"""
    try:
        issue = data.get('issue', {})
        issue_id = issue.get('id')
        
        # Логика обработки
        logger.info(f"Создана новая заявка: {issue_id}")
        
    except Exception as e:
        logger.error(f"Ошибка обработки новой заявки: {e}")
```
