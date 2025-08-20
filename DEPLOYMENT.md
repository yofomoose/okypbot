# 🚀 Инструкция по развертыванию OkypBot в продакшн

## Архитектура

Продакшн архитектура состоит из контейнеров:
- **PostgreSQL контейнер** - база данных с возможностью удаленного доступа
- **Bot контейнер** - Telegram бот + Webhook сервер
- **nginx контейнер** (опционально) - прокси для webhook endpoints

## Варианты развертывания

### Вариант 1: Со встроенным nginx (рекомендуется)

Подходит если у вас нет другого nginx или вы хотите изолированное решение.

```bash
# Автоматическое развертывание
make deploy

# Или вручную
chmod +x deploy-full.sh
./deploy-full.sh
```

**Порты:**
- nginx: 80 (webhook endpoints)
- PostgreSQL: 5433 (удаленный доступ)

### Вариант 2: С внешним nginx

Подходит если у вас уже есть nginx (например, с n8n) и вы хотите интеграцию.

```bash
# Развертывание без nginx
make deploy-external

# Интеграция с существующим nginx
sudo cp nginx/external-integration.conf /etc/nginx/sites-available/okypbot
sudo ln -s /etc/nginx/sites-available/okypbot /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

**Порты:**
- Bot webhook: 8000 (для проксирования через внешний nginx)
- PostgreSQL: 5433 (удаленный доступ)

## Доступные команды

### Основные
- `make deploy` - Полное развертывание (БД + бот)
- `make update-bot` - Обновление только бота
- `make start` - Запуск всех сервисов
- `make stop` - Остановка всех сервисов
- `make status` - Статус сервисов

### Мониторинг
- `make logs` - Просмотр всех логов
- `make logs-bot` - Логи только бота
- `make logs-db` - Логи только БД

### Обслуживание
- `make backup-db` - Бэкап базы данных
- `make shell-bot` - Подключение к контейнеру бота
- `make shell-db` - Подключение к PostgreSQL
- `make clean` - Очистка неиспользуемых образов

## Обновление бота

Для обновления только бота (без остановки БД):
```bash
make update-bot
```

Скрипт автоматически:
1. Делает git pull
2. Останавливает только бот
3. Пересобирает образ бота
4. Запускает обновленный бот
5. Проверяет health check

## Интеграция с существующим nginx

Если у вас уже есть nginx с n8n:

1. Скопируйте конфигурацию:
```bash
sudo cp nginx-n8n-integration.conf /etc/nginx/sites-available/okypbot
sudo ln -s /etc/nginx/sites-available/okypbot /etc/nginx/sites-enabled/
```

2. Перезагрузите nginx:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Порты и доступ

- **PostgreSQL**: 5432 (внешний доступ)
- **Bot webhook**: 8000 (проксируется через nginx)
- **Health check**: 8000/health

## Бэкапы

Автоматический бэкап:
```bash
make backup-db
```

Создается файл: `backup_YYYYMMDD_HHMMSS.sql`

Восстановление:
```bash
docker exec -i okypbot_postgres psql -U postgres -d okypbot < backup_file.sql
```

## Мониторинг

### Health checks
Бот имеет встроенный health check endpoint:
```bash
curl http://localhost:8000/health
```

### Логи
```bash
# Все логи в реальном времени
make logs

# Только ошибки
make logs | grep -i error

# Последние 50 строк
docker-compose -f docker-compose.prod.yml logs --tail=50
```

## Решение проблем

### Бот не запускается
```bash
make logs-bot
```

### База данных недоступна
```bash
make logs-db
make shell-db
```

### Webhook не работает
1. Проверьте nginx конфигурацию
2. Убедитесь что порт 8000 открыт
3. Проверьте логи бота

### Нет места на диске
```bash
make clean
docker system prune -a
```

## Переменные окружения

Основные переменные в `.env`:
```env
# Telegram Bot
BOT_TOKEN=your_bot_token

# Okdesk API
OKDESK_API_TOKEN=your_api_token
OKDESK_BASE_URL=https://your-account.okdesk.ru

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=okypbot

# Webhook
WEBHOOK_SECRET=your_webhook_secret
```

## Безопасность

1. **Firewall**: Откройте только необходимые порты
2. **SSL**: Используйте HTTPS для webhook
3. **Секреты**: Никогда не коммитьте .env файлы
4. **Бэкапы**: Регулярно делайте бэкапы БД
5. **Обновления**: Регулярно обновляйте образы

## Масштабирование

Для высоких нагрузок:
1. Увеличьте количество workers в docker-compose
2. Настройте load balancer
3. Используйте внешнюю базу данных
4. Добавьте мониторинг (Prometheus + Grafana)

## Поддержка

При возникновении проблем:
1. Проверьте логи: `make logs`
2. Проверьте статус: `make status`  
3. Проверьте конфигурацию: `.env` файл
4. Создайте issue в репозитории с логами ошибок
