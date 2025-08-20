# 📋 Полная инструкция по развертыванию OkypBot

## 🎯 Обзор

OkypBot - это Telegram бот для интеграции с Okdesk CRM с поддержкой ML-классификации заявок. Система состоит из нескольких компонентов и требует правильной настройки базы данных и ML модели.

## 🏗️ Архитектура системы

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │   OkypBot App   │    │     nginx       │
│   (База данных) │◄───┤  (Бот + API)    │◄───┤   (Прокси)      │
│   Порт: 5433    │    │   Порт: 8000    │    │   Порт: 80      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   ML модель     │
                       │  (Классификация)│
                       └─────────────────┘
```

## 📦 Что входит в систему

- **Telegram бот** - интерфейс для пользователей
- **Webhook сервер** - получение событий от Okdesk
- **PostgreSQL база** - хранение пользователей и заявок
- **ML модель** - классификация заявок по категориям
- **nginx** - проксирование и балансировка (опционально)

## 🚀 Быстрое развертывание

### Шаг 1: Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker и Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker
```

### Шаг 2: Клонирование и настройка

```bash
# Клонирование репозитория
git clone https://github.com/yofomoose/okypbot.git
cd okypbot

# Создание .env файла
cp .env.example .env
nano .env
```

### Шаг 3: Настройка переменных окружения

Отредактируйте файл `.env`:

```env
# Telegram Bot
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Okdesk API
OKDESK_API_TOKEN=your_okdesk_api_token
OKDESK_BASE_URL=https://your-company.okdesk.ru

# База данных
DB_PASSWORD=secure_password_here
POSTGRES_USER=postgres
POSTGRES_DB=okypbot

# Webhook
OKDESK_WEBHOOK_SECRET=your_webhook_secret

# Администраторы (Telegram ID через запятую)
ADMIN_IDS=123456789,987654321
```

### Шаг 4: Развертывание

```bash
# Вариант 1: Со встроенным nginx (рекомендуется)
make deploy

# Вариант 2: Без nginx (если у вас есть свой)
make deploy-external
```

## 🗄️ База данных - автоматическое создание таблиц

### Что происходит автоматически

При первом запуске бота **таблицы создаются автоматически**:

1. **Инициализация через SQLAlchemy ORM**
2. **Создание всех необходимых таблиц**
3. **Настройка индексов и связей**

### Структура создаваемых таблиц

```sql
-- Пользователи
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    user_type VARCHAR(20), -- 'individual' или 'legal'
    position VARCHAR(100), -- для юр. лиц
    inn VARCHAR(12), -- для юр. лиц
    okdesk_contact_id INTEGER,
    okdesk_company_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Заявки
CREATE TABLE issues (
    id SERIAL PRIMARY KEY,
    okdesk_issue_id INTEGER UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(500),
    description TEXT,
    status VARCHAR(50),
    priority VARCHAR(20),
    ml_category VARCHAR(100), -- ML классификация
    ml_confidence FLOAT, -- уверенность ML
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Логи ML классификации
CREATE TABLE ml_predictions (
    id SERIAL PRIMARY KEY,
    issue_id INTEGER REFERENCES issues(id),
    original_text TEXT,
    predicted_category VARCHAR(100),
    confidence FLOAT,
    model_version VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Проверка создания таблиц

```bash
# Подключение к базе данных
make shell-db

# Просмотр таблиц
\dt

# Проверка структуры таблицы
\d users
\d issues
\d ml_predictions

# Выход
\q
```

### Ручная инициализация (если нужно)

Если автоматическое создание не сработало:

```bash
# Подключение к базе
make shell-db

# Выполнение SQL скрипта
\i /docker-entrypoint-initdb.d/init.sql

# Или создание вручную
CREATE DATABASE okypbot;
\c okypbot
-- Вставьте SQL из структуры выше
```

## 🤖 ML модель - размещение и настройка

### Структура ML модели

```
ml/
├── models/
│   ├── issue_classifier.pkl      # Основная модель
│   ├── vectorizer.pkl           # Векторизатор текста
│   ├── label_encoder.pkl        # Кодировщик категорий
│   └── model_metadata.json      # Метаданные модели
├── training/
│   ├── train_model.py          # Скрипт обучения
│   ├── training_data.csv       # Данные для обучения
│   └── evaluate_model.py       # Оценка модели
└── inference/
    ├── classifier.py           # Класс для классификации
    └── preprocessing.py        # Предобработка текста
```

### Размещение ML модели на сервере

#### Вариант 1: Копирование файлов модели

```bash
# Создание папки для модели на сервере
mkdir -p /path/to/okypbot/ml/models

# Копирование модели с локального компьютера
scp ml/models/* user@server:/path/to/okypbot/ml/models/

# Или через git (если модель в репозитории)
git lfs pull  # если используется Git LFS для больших файлов
```

#### Вариант 2: Загрузка через Docker volume

```bash
# В docker-compose.yml уже настроено:
volumes:
  - ./ml/models:/app/ml/models

# Просто поместите файлы в папку ml/models перед запуском
```

#### Вариант 3: Скачивание с облачного хранилища

```bash
# Добавьте в deploy-full.sh скачивание модели
wget https://your-storage.com/models/issue_classifier.pkl -O ml/models/issue_classifier.pkl
wget https://your-storage.com/models/vectorizer.pkl -O ml/models/vectorizer.pkl
# и т.д.
```

### Проверка ML модели

```bash
# Проверка наличия файлов модели
make shell-bot
ls -la /app/ml/models/

# Тест классификации
python -c "
from ml.inference.classifier import IssueClassifier
classifier = IssueClassifier()
result = classifier.predict('Не работает компьютер')
print(f'Категория: {result}')
"
```

### Обновление ML модели

```bash
# Остановка только бота (БД остается работать)
make update-bot

# Или замена файлов модели на лету
docker cp new_model.pkl okypbot_app:/app/ml/models/issue_classifier.pkl
docker restart okypbot_app
```

## ⚙️ Настройка Okdesk

### Настройка API

1. Войдите в Okdesk → **Настройки** → **API**
2. Создайте новый API ключ
3. Скопируйте токен в `.env` файл

### Настройка Webhook

1. **Администрирование** → **Интеграции** → **Webhooks**
2. Создайте webhook:
   - **URL**: `https://your-domain.com/okdesk-webhook`
   - **События**: 
     - ✅ Новый комментарий
     - ✅ Изменение статуса 
     - ✅ Назначение исполнителя
   - **Подпись**: укажите секрет из `.env`

## 🔍 Проверка развертывания

### Проверка сервисов

```bash
# Статус всех контейнеров
make status

# Логи в реальном времени
make logs

# Логи отдельных сервисов
make logs-bot
make logs-db
make logs-nginx
```

### Проверка базы данных

```bash
# Подключение к БД
make shell-db

# Проверка таблиц
\dt

# Проверка данных
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM issues;
\q
```

### Проверка ML модели

```bash
# Подключение к контейнеру бота
make shell-bot

# Проверка файлов модели
ls -la ml/models/

# Тест ML классификации
python -c "
import sys
sys.path.append('/app')
from ml.inference.classifier import IssueClassifier
try:
    classifier = IssueClassifier()
    result = classifier.predict('Тестовая заявка')
    print(f'✅ ML модель работает: {result}')
except Exception as e:
    print(f'❌ Ошибка ML модели: {e}')
"
```

### Проверка webhook

```bash
# Тест health check
curl http://your-domain.com/health

# Тест webhook endpoint
curl -X POST http://your-domain.com/okdesk-webhook \
  -H "Content-Type: application/json" \
  -H "X-Okdesk-Signature: test" \
  -d '{"event":{"event_type":"test"},"issue":{"id":1,"title":"Test"}}'
```

## 🛠️ Команды управления

### Основные команды

```bash
make help              # Показать все команды
make deploy            # Полное развертывание
make deploy-external   # Развертывание без nginx
make start             # Запуск сервисов
make stop              # Остановка сервисов
make restart           # Перезапуск сервисов
make update-bot        # Обновление только бота
```

### Мониторинг

```bash
make status            # Статус сервисов
make logs              # Все логи
make logs-bot          # Логи бота
make logs-db           # Логи БД
make logs-nginx        # Логи nginx
```

### Обслуживание

```bash
make backup-db         # Бэкап базы данных
make shell-bot         # Подключение к контейнеру бота
make shell-db          # Подключение к PostgreSQL
make clean             # Очистка неиспользуемых образов
```

## 📊 Мониторинг и логи

### Расположение логов

```bash
# Логи контейнеров
docker-compose -f docker-compose.prod.yml logs

# Логи nginx (если используется)
docker exec okypbot_nginx tail -f /var/log/nginx/access.log
docker exec okypbot_nginx tail -f /var/log/nginx/error.log

# Логи приложения
docker exec okypbot_app tail -f /app/logs/bot.log
```

### Health checks

```bash
# Проверка здоровья всех сервисов
curl http://localhost/health

# Проверка отдельных компонентов
docker exec okypbot_postgres pg_isready -U postgres
docker exec okypbot_app curl -f http://localhost:8000/health
```

## 🔒 Безопасность

### Firewall настройки

```bash
# Открытие только необходимых портов
sudo ufw allow 22      # SSH
sudo ufw allow 80      # HTTP
sudo ufw allow 443     # HTTPS (если SSL)
sudo ufw enable
```

### SSL сертификат (рекомендуется)

```bash
# Установка Certbot
sudo apt install certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d your-domain.com

# Автообновление
sudo crontab -e
# Добавить: 0 12 * * * /usr/bin/certbot renew --quiet
```

## ⚠️ Решение проблем

### Бот не запускается

```bash
# Проверка логов
make logs-bot

# Проверка переменных окружения
docker exec okypbot_app env | grep BOT_TOKEN

# Перезапуск
make restart
```

### База данных недоступна

```bash
# Проверка статуса PostgreSQL
make logs-db

# Проверка подключения
make shell-db

# Пересоздание контейнера БД
docker-compose -f docker-compose.prod.yml down postgres
docker-compose -f docker-compose.prod.yml up -d postgres
```

### ML модель не работает

```bash
# Проверка файлов модели
make shell-bot
ls -la ml/models/

# Проверка загрузки модели
python -c "
import pickle
try:
    with open('ml/models/issue_classifier.pkl', 'rb') as f:
        model = pickle.load(f)
    print('✅ Модель загружается')
except Exception as e:
    print(f'❌ Ошибка загрузки: {e}')
"
```

### Webhook не работает

```bash
# Проверка nginx
make logs-nginx

# Проверка эндпоинта
curl -I http://localhost/okdesk-webhook

# Проверка портов
netstat -tlnp | grep :80
netstat -tlnp | grep :8000
```

## 📈 Масштабирование

### Увеличение производительности

1. **Увеличение ресурсов контейнера**:
```yaml
# В docker-compose.prod.yml
bot:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 2G
```

2. **Масштабирование воркеров**:
```yaml
# Добавление нескольких экземпляров бота
bot_1:
  # конфигурация бота
bot_2:
  # конфигурация бота
```

3. **Внешняя база данных**:
```env
# Использование внешней PostgreSQL
DB_HOST=external-postgres.example.com
DB_PORT=5432
```

## 🆘 Поддержка

При возникновении проблем:

1. **Проверьте логи**: `make logs`
2. **Проверьте статус**: `make status`
3. **Проверьте конфигурацию**: файл `.env`
4. **Создайте issue** в репозитории с:
   - Описанием проблемы
   - Логами ошибок
   - Конфигурацией (без секретов)

---

## 📋 Чеклист развертывания

- [ ] Сервер подготовлен (Docker установлен)
- [ ] Репозиторий склонирован
- [ ] Файл `.env` настроен
- [ ] ML модель размещена в `ml/models/`
- [ ] Выполнен `make deploy`
- [ ] Таблицы БД созданы автоматически
- [ ] Webhook настроен в Okdesk
- [ ] Health checks проходят
- [ ] ML классификация работает
- [ ] Тестовые сообщения обрабатываются

**✅ Готово! Ваш OkypBot развернут и готов к работе.**
