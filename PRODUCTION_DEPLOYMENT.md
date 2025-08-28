# 🚀 Okypbot Production Deployment Guide

## 📋 Предварительные требования

1. **Docker и Docker Compose** установлены
2. **Файл .env.production** настроен с правильными токенами
3. **Папка bot_model** с обученными моделями существует

## 🔧 Быстрый запуск

### 1. Перейдите в директорию проекта
```bash
cd /path/to/okypbot
```

### 2. Запустите развертывание
```bash
# Linux/Mac
./deploy_production.sh

# Или вручную
cd docker
docker-compose -f docker-compose.prod.yml --env-file ../.env.production up -d --build
```

### 3. Проверьте статус
```bash
# Linux/Mac
./check_production_status.sh

# Или вручную
docker-compose -f docker/docker-compose.prod.yml ps
```

## 🌐 Доступ к сервисам

После успешного запуска:

- **Bot Webhook**: `http://localhost:8080/okdesk-webhook`
- **Health Check**: `http://localhost:8080/health`
- **Direct Bot API**: `http://localhost:8000`
- **PostgreSQL**: `localhost:5433`

## 📊 Мониторинг

### Просмотр логов
```bash
# Все логи
docker-compose -f docker/docker-compose.prod.yml logs -f

# Только bot логи
docker-compose -f docker/docker-compose.prod.yml logs -f bot

# Только database логи
docker-compose -f docker/docker-compose.prod.yml logs -f postgres
```

### Проверка здоровья
```bash
# Bot health
curl http://localhost:8080/health

# Database connectivity
docker-compose -f docker/docker-compose.prod.yml exec postgres pg_isready -U postgres -d okypbot
```

## 🛠️ Управление сервисами

### Остановка
```bash
docker-compose -f docker/docker-compose.prod.yml down
```

### Перезапуск
```bash
docker-compose -f docker/docker-compose.prod.yml restart
```

### Пересборка
```bash
docker-compose -f docker/docker-compose.prod.yml up -d --build
```

## 🔍 Диагностика проблем

### Если бот не запускается:
1. Проверьте логи: `docker-compose -f docker/docker-compose.prod.yml logs bot`
2. Проверьте переменные окружения в `.env.production`
3. Убедитесь, что файлы модели существуют: `ls -la bot_model/`

### Если webhook не работает:
1. Проверьте nginx логи: `docker-compose -f docker/docker-compose.prod.yml logs nginx`
2. Проверьте доступность порта 8080
3. Убедитесь, что `WEBHOOK_ENABLED=true` в `.env.production`

### Если проблемы с БД:
1. Проверьте PostgreSQL логи: `docker-compose -f docker/docker-compose.prod.yml logs postgres`
2. Проверьте подключение: `docker-compose -f docker/docker-compose.prod.yml exec postgres pg_isready -U postgres -d okypbot`

## 📁 Структура файлов

```
/app/
├── bot_model/          # ML модели
│   ├── classifier.pkl
│   ├── label_encoder.pkl
│   ├── model_metadata.json
│   └── training_examples.pkl
├── logs/               # Логи приложения
├── data/               # Данные приложения
├── ml/                 # ML данные и кэш
└── database/           # Данные БД
```

## ⚙️ Переменные окружения

Обязательные переменные в `.env.production`:

- `BOT_TOKEN` - токен Telegram бота
- `OKDESK_API_TOKEN` - токен Okdesk API
- `OKDESK_BASE_URL` - URL вашего Okdesk аккаунта
- `DB_PASSWORD` - пароль PostgreSQL
- `ADMIN_IDS` - ID администраторов через запятую

## 🔐 Безопасность

- Все пароли хранятся в переменных окружения
- Контейнеры запускаются с ограниченными правами
- Используется не-root пользователь (UID 1000)
- Secrets не логируются в выводе

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи контейнеров
2. Убедитесь в корректности `.env.production`
3. Проверьте доступность внешних сервисов (Telegram, Okdesk)
