# 🚀 Исправления проблем деплоя

## Проблемы и решения

### ✅ Исправлено:

1. **requirements.txt не найден**
   - Исправлен контекст сборки Docker: `context: ..` и `dockerfile: docker/Dockerfile`

2. **Переменные окружения не заданы**
   - Создан корректный `.env.production` с рабочими значениями
   - Исправлен поврежденный `.env.example`
   - Скрипт теперь автоматически копирует `.env.production` в `.env`
   - Добавлена загрузка и валидация переменных окружения

3. **PostgreSQL падает из-за отсутствия пароля**
   - Упрощена конфигурация PostgreSQL (убраны ссылки на несуществующие файлы)
   - Переменные окружения теперь правильно передаются в docker-compose

4. **docker-compose: command not found**
   - Скрипт автоматически определяет `docker compose` или `docker-compose`
   - Исправлена команда в health check

5. **Устаревший атрибут version**
   - Удален атрибут `version: '3.8'` из `docker/docker-compose.prod.yml`

## 🔧 Что нужно сделать на сервере:

1. **Обновить код:**
   ```bash
   cd /opt/okypbot
   git pull origin main
   ```

2. **Настроить переменные окружения:**
   ```bash
   # Отредактировать .env.production с вашими данными
   nano .env.production
   
   # Обязательно заполните:
   # - BOT_TOKEN (ваш токен бота)
   # - OKDESK_API_TOKEN (ваш API токен)
   # - ADMIN_IDS (ваш Telegram ID)
   # - DB_PASSWORD (надежный пароль для БД, например: MySecure2024!)
   ```

3. **Пример корректного .env.production:**
   ```bash
   BOT_TOKEN=1234567890:ABCdef1234567890abcdef1234567890ABC
   OKDESK_API_TOKEN=your_okdesk_api_token_here
   OKDESK_BASE_URL=https://yapomogu55.okdesk.ru
   OKDESK_WEBHOOK_SECRET=okdesk_webhook_secret_2024_secure_key
   DB_PASSWORD=MySecure2024Password!
   ADMIN_IDS=123456789
   DEBUG=false
   LOG_LEVEL=INFO
   ```

4. **Запустить деплой:**
   ```bash
   make deploy
   ```

## 📋 Что делает исправленный скрипт:

1. Проверяет наличие `.env.production`
2. Копирует его в `.env` (если нет)
3. Загружает переменные окружения
4. Копирует `.env` в папку `docker/` для docker-compose
5. Проверяет критические переменные (BOT_TOKEN, DB_PASSWORD)
6. Запускает сборку и деплой

## ⚠️ Важно:

- **Обязательно заполните ADMIN_IDS** вашим Telegram ID
- **Смените DB_PASSWORD** на надежный пароль (без этого PostgreSQL не запустится)
- Проверьте, что все токены корректны
- После деплоя проверьте статус: `docker compose -f docker/docker-compose.prod.yml ps`

После выполнения этих шагов деплой должен пройти успешно! 🎉
