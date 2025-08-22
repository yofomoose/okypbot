# Makefile для управления OkypBot

# Переменные
COMPOSE_FILE = docker/docker-compose.prod.yml
COMPOSE_FILE_EXTERNAL = docker/docker-compose.external-nginx.yml
CONTAINER_BOT = okypbot_app
CONTAINER_DB = okypbot_postgres
CONTAINER_NGINX = okypbot_nginx
SCRIPTS_DIR = scripts

# Определение команды Docker Compose
DOCKER_COMPOSE := $(shell if command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; elif docker compose version >/dev/null 2>&1; then echo "docker compose"; else echo "echo 'Error: Docker Compose not found' && exit 1"; fi)

# Цвета для вывода
GREEN := $(shell tput setaf 2)
YELLOW := $(shell tput setaf 3)
RED := $(shell tput setaf 1)
RESET := $(shell tput sgr0)

# Помощь
help:
	@echo "🤖 $(GREEN)OkypBot Management Commands:$(RESET)"
	@echo ""
	@echo "$(YELLOW)Развертывание:$(RESET)"
	@echo "  make setup        - Подготовка окружения"
	@echo "  make deploy       - Полное развертывание (подготовка + сборка + запуск)"
	@echo "  make update       - Обновление бота"
	@echo ""
	@echo "$(YELLOW)Управление сервисами:$(RESET)"
	@echo "  make start        - Запуск всех сервисов"
	@echo "  make stop         - Остановка всех сервисов"
	@echo "  make restart      - Перезапуск всех сервисов"
	@echo "  make rebuild      - Пересборка и перезапуск"
	@echo ""
	@echo "$(YELLOW)Мониторинг:$(RESET)"
	@echo "  make logs         - Просмотр всех логов"
	@echo "  make logs-bot     - Логи только бота"
	@echo "  make logs-db      - Логи только БД"
	@echo "  make status       - Статус сервисов"
	@echo ""
	@echo "$(YELLOW)База данных:$(RESET)"
	@echo "  make backup       - Создание бэкапа БД"
	@echo "  make restore FILE=backup.sql - Восстановление из бэкапа"
	@echo ""
	@echo "$(YELLOW)ML модель:$(RESET)"
	@echo "  make check-ml     - Проверка ML модели"
	@echo "  make train-ml     - Обучение ML модели"
	@echo ""
	@echo "$(YELLOW)Обслуживание:$(RESET)"
	@echo "  make clean        - Очистка неиспользуемых ресурсов"
	@echo "  make clean-all    - Полная очистка с остановкой"
	@echo "  make disk-usage   - Анализ использования диска"
	@echo ""
	@echo "🔧 Используется: $(DOCKER_COMPOSE)"

# Подготовка окружения
setup:
	@echo "📦 Подготовка окружения..."
	@chmod +x $(SCRIPTS_DIR)/prepare_environment.sh
	@./$(SCRIPTS_DIR)/prepare_environment.sh

# Развертывание
deploy: setup
	@echo "🚀 Развертывание..."
	@echo "1. Сборка образов..."
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) build --no-cache
	@echo "2. Запуск сервисов..."
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d
	@echo "3. Проверка статуса..."
	@sleep 5
	@make status
	@echo "\n4. Проверка логов на ошибки..."
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) logs --tail=20 bot

# Управление сервисами
start:
	@echo "▶️ Запуск сервисов..."
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d
	@make status

stop:
	@echo "⏹️ Остановка сервисов..."
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down

restart:
	@echo "🔄 Перезапуск сервисов..."
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) restart
	@make status

rebuild: stop
	@echo "🏗️ Пересборка..."
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) build --no-cache
	@make start

# Мониторинг
logs:
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) logs -f

logs-bot:
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) logs -f bot

logs-db:
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) logs -f postgres

status:
	@echo "📊 Статус сервисов:"
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) ps

# База данных
backup:
	@echo "💾 Создание бэкапа..."
	@mkdir -p backups
	@docker exec $(CONTAINER_DB) pg_dump -U postgres okypbot > backups/okypbot_$$(date +%Y%m%d_%H%M%S).sql
	@echo "✅ Бэкап создан в директории backups/"

restore:
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)❌ Укажите файл бэкапа: make restore FILE=backup.sql$(RESET)"; \
		exit 1; \
	fi
	@echo "📥 Восстановление из $(FILE)..."
	@cat $(FILE) | docker exec -i $(CONTAINER_DB) psql -U postgres -d okypbot
	@echo "✅ База данных восстановлена"

# Обновление
update:
	@echo "🔄 Обновление бота..."
	git pull
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) stop bot
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) rm -f bot
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) build --no-cache bot
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d bot
	@echo "✅ Бот обновлен"

# ML модель
check-ml:
	@echo "🔍 Проверка ML модели..."
	@docker exec $(CONTAINER_BOT) python -c "from ml.classifier import TextClassifier; print('ML модель работает' if TextClassifier().is_ready() else 'ML модель не готова')"

train-ml:
	@echo "🧠 Запуск обучения ML модели..."
	@docker exec $(CONTAINER_BOT) python -m ml.trainer

# Обслуживание
clean:
	@echo "🧹 Очистка неиспользуемых ресурсов..."
	@echo "📊 До очистки:"
	@docker system df
	@echo "\n1. Очистка неиспользуемых образов..."
	@docker image prune -f
	@echo "\n2. Очистка неиспользуемых томов..."
	@docker volume prune -f
	@echo "\n3. Очистка кэша сборки..."
	@docker builder prune -f
	@echo "\n📊 После очистки:"
	@docker system df
	@echo "\n✅ Очистка завершена"

clean-all: stop
	@echo "⚠️ $(RED)Внимание! Будут удалены ВСЕ неиспользуемые ресурсы Docker!$(RESET)"
	@echo "📊 До очистки:"
	@docker system df
	@echo "\n🗑️ Выполняется полная очистка..."
	@docker system prune -a --volumes -f
	@echo "\n📊 После очистки:"
	@docker system df
	@echo "\n✅ Полная очистка завершена"

disk-usage:
	@echo "📊 Использование диска Docker:"
	@docker system df -v

.PHONY: help setup deploy update start stop restart rebuild logs logs-bot logs-db status backup restore check-ml train-ml clean clean-all disk-usage
