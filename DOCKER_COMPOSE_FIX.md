# 🚀 Быстрое исправление для Docker Compose

## 🔧 Проблема
На сервере отсутствует команда `docker-compose`, но есть `docker compose` (новая версия).

## ⚡ Быстрое решение

### Вариант 1: Обновление кода (рекомендуется)
```bash
# Обновление до новой версии с исправлениями
git pull origin feature/ml-classification

# Теперь скрипты автоматически определят правильную команду
make deploy
```

### Вариант 2: Установка docker-compose (если нужна совместимость)
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker-compose-plugin

# CentOS/RHEL
sudo yum install docker-compose-plugin

# Или standalone версия
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Вариант 3: Ручная замена команд
```bash
# Временное решение - замена в скриптах
sed -i 's/docker-compose/docker compose/g' deploy-full.sh
sed -i 's/docker-compose/docker compose/g' deploy.sh
sed -i 's/docker-compose/docker compose/g' update-bot.sh

# Запуск
make deploy
```

## ✅ Проверка
```bash
# Проверьте какая команда доступна
docker-compose --version    # Старая версия
docker compose version     # Новая версия

# Статус после исправления
make status
```

## 📊 Обновленные файлы
Новая версия поддерживает обе команды автоматически:
- `deploy-full.sh` - автоопределение Docker Compose
- `deploy.sh` - автоопределение Docker Compose  
- `update-bot.sh` - автоопределение Docker Compose
- `Makefile` - использует переменную для команды

## 🎉 Результат
После исправления все команды будут работать корректно:
```bash
make deploy         # ✅ Работает
make status         # ✅ Работает  
make logs          # ✅ Работает
make update-bot    # ✅ Работает
```
