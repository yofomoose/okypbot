# Руководство по устранению неполадок Okypbot

## Обнаруженные проблемы и решения

### 1. 🚨 Проблема с Okdesk API (404 ошибки)

**Симптомы:**
```
WARNING:services.okdesk_service:Endpoint /api/v1/employees/me вернул статус 404
ERROR:services.okdesk_service:Не удалось получить данные пользователя через все доступные endpoints
```

**Возможные причины:**
1. Неправильный `OKDESK_BASE_URL` в `.env`
2. Неправильный API токен
3. API токен не имеет необходимых прав
4. Неправильная версия API

**Решение:**
```bash
# 1. Проверьте .env файл
cat .env

# 2. Убедитесь что URL правильный (пример):
OKDESK_BASE_URL=https://your-company.okdesk.ru

# 3. Запустите диагностику
python diagnose_okdesk.py

# 4. Проверьте API токен в админке Okdesk
```

### 2. 🚨 Проблема с author_id

**Симптомы:**
```
ERROR:services.okdesk_service:Ошибка добавления комментария: 422 - {"errors":{"author_id":["отсутствует"]}}
```

**Решение:**
1. Добавьте в `.env`:
```
OKDESK_AUTHOR_ID=1
```

2. Или найдите правильный ID сотрудника в Okdesk и используйте его.

### 3. 🚨 Ошибка numpy._core

**Симптомы:**
```
ERROR:ml.classifier:Ошибка загрузки примеров: No module named 'numpy._core'
```

**Решение:**
```bash
# Переустановите numpy с правильной версией
pip install --upgrade numpy==1.25.2 --force-reinstall

# Проверьте установку
python -c "import numpy; import numpy.core; print('NumPy OK')"
```

### 4. 🚨 Permission denied

**Симптомы:**
```
ERROR:ml.classifier:Ошибка сохранения примеров: [Errno 13] Permission denied: 'bot_model/training_examples.pkl'
```

**Решение для локального запуска:**
```bash
# Создайте директории с правильными правами
mkdir -p bot_model logs data
chmod 755 bot_model logs data

# Создайте файл если его нет
touch bot_model/training_examples.pkl
chmod 666 bot_model/training_examples.pkl
```

**Решение для Docker:**
```bash
# Пересоберите образ с исправленным Dockerfile
docker-compose build --no-cache
docker-compose up
```

## Автоматическое исправление

Запустите скрипт автоматического исправления:

```bash
python fix_issues.py
```

Этот скрипт:
- ✅ Проверит и исправит `.env` файл
- ✅ Создаст необходимые директории
- ✅ Установит правильные права доступа
- ✅ Переустановит numpy с правильной версией
- ✅ Проверит критичные импорты

## Диагностика

Запустите полную диагностику:

```bash
python diagnose_okdesk.py
```

Этот скрипт:
- 🔍 Проверит конфигурацию
- 🌐 Протестирует подключение к Okdesk API
- 🔗 Проверит доступность endpoints
- 📋 Покажет детальный отчет

## Пошаговое решение

### Шаг 1: Проверьте .env файл

Убедитесь что файл `.env` содержит:

```env
BOT_TOKEN=your_bot_token_here
OKDESK_API_TOKEN=your_okdesk_api_token
OKDESK_BASE_URL=https://your-company.okdesk.ru
OKDESK_AUTHOR_ID=1
WEBHOOK_ENABLED=true
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8001
```

### Шаг 2: Исправьте зависимости

```bash
# Обновите pip
pip install --upgrade pip

# Переустановите критичные пакеты
pip install -r requirements.txt --force-reinstall

# Проверьте numpy
python -c "import numpy; print(numpy.__version__)"
```

### Шаг 3: Проверьте права доступа

```bash
# Локально
chmod -R 755 bot_model/ logs/ data/

# В Docker
docker exec -it okypbot_app chmod -R 777 /app/bot_model
```

### Шаг 4: Проверьте Okdesk API

```bash
# Запустите диагностику
python diagnose_okdesk.py

# Проверьте API токен в браузере
curl -H "Authorization: Bearer YOUR_TOKEN" https://your-company.okdesk.ru/api/v1/employees
```

## Логи и отладка

### Просмотр логов Docker

```bash
# Все логи
docker-compose logs -f

# Только ошибки
docker-compose logs | grep ERROR

# Последние 100 строк
docker-compose logs --tail=100
```

### Увеличение детализации логов

Добавьте в `.env`:
```
LOG_LEVEL=DEBUG
```

### Проверка состояния сервисов

```bash
# Статус контейнеров
docker-compose ps

# Здоровье приложения
curl http://localhost:8001/health
```

## Частые проблемы

### Проблема: "Module not found"
**Решение:** 
```bash
pip install -r requirements.txt
```

### Проблема: "Can't connect to Okdesk"
**Решение:**
1. Проверьте `OKDESK_BASE_URL`
2. Проверьте сетевое подключение
3. Проверьте API токен

### Проблема: "Permission denied in Docker"
**Решение:**
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Проблема: "Bot not responding"
**Решение:**
1. Проверьте `BOT_TOKEN`
2. Проверьте логи: `docker-compose logs`
3. Перезапустите: `docker-compose restart`

## Контакты для поддержки

Если проблемы не решаются:

1. 📝 Соберите логи: `docker-compose logs > logs.txt`
2. 🔍 Запустите диагностику: `python diagnose_okdesk.py > diagnostic.txt`
3. 📧 Отправьте файлы администратору

## Полезные команды

```bash
# Полная перезагрузка
docker-compose down && docker-compose up --build

# Очистка Docker
docker system prune -f

# Проверка дискового пространства
df -h

# Проверка памяти
free -h

# Просмотр процессов
docker-compose top
```
