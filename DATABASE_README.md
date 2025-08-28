# Работа с базами данных OkypBot

## Структура баз данных

В проекте используются две базы данных:

### 1. Файловая база данных (`database/users.json`)
- **Назначение**: Хранение основных данных пользователей (ФИО, телефон, тип пользователя)
- **Формат**: JSON файл
- **Расположение**: `/app/database/users.json` в контейнере
- **Volume**: `database_data:/app/database`

### 2. PostgreSQL база данных
- **Назначение**: Хранение статистики ML, классификаций, обратной связи
- **Расположение**: Контейнер `okypbot_postgres`
- **Volume**: `postgres_data:/var/lib/postgresql/data`

## Резервное копирование

### Создание бэкапа
```bash
make backup
```
Создает бэкап обеих баз данных в директории `backups/`:
- `users_YYYYMMDD_HHMMSS.json` - файловая база данных
- `user_issues_YYYYMMDD_HHMMSS.json` - заявки пользователей
- `postgres_okypbot_YYYYMMDD_HHMMSS.sql` - PostgreSQL база данных

### Восстановление из бэкапа
```bash
# Восстановление файловой базы данных
make restore FILE=backups/users_20231201_120000.json

# Восстановление PostgreSQL
make restore FILE=backups/postgres_okypbot_20231201_120000.sql
```

## Проверка состояния баз данных

```bash
make check-db
```
Показывает:
- Состояние файловой базы данных (users.json)
- Количество пользователей в PostgreSQL
- Количество классификаций в PostgreSQL

## Автоматическая защита данных

### При остановке сервисов
При выполнении `make stop` автоматически создается бэкап.

### При запуске контейнера
При запуске контейнера автоматически проверяется наличие файловой базы данных и при необходимости восстанавливается из последнего бэкапа.

## Миграции базы данных

При обновлении структуры базы данных:

1. **PostgreSQL**: Используйте SQL миграции в `sql/migrations/`
2. **Файловая БД**: Обновите структуру в `database/models.py`

## Важные замечания

⚠️ **Никогда не удаляйте volume `database_data` без бэкапа!**
```bash
# ❌ Плохо - удалит все данные пользователей
docker-compose down -v

# ✅ Хорошо - создаст бэкап перед удалением
make backup && docker-compose down -v
```

## Восстановление после сбоя

Если файловая база данных была потеряна:

1. Проверьте наличие бэкапов: `ls backups/`
2. Восстановите из последнего бэкапа: `make restore FILE=backups/users_...json`
3. Перезапустите сервисы: `make restart`

## Мониторинг

### Размер базы данных
```bash
# Размер файловой БД
docker exec okypbot_app du -sh /app/database/

# Размер PostgreSQL
docker exec okypbot_postgres du -sh /var/lib/postgresql/data/
```

### Логи работы с базами данных
```bash
# Логи приложения
make logs-bot

# Логи PostgreSQL
make logs-db
```</content>
<parameter name="filePath">c:\Users\YofoY\Documents\Что то долго хранимое\okypbot\DATABASE_README.md
