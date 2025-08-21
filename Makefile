# Makefile для управления OkypBot

# Переменные
COMPOSE_FILE = docker/docker-compose.prod.yml
COMPOSE_FILE_EXTERNAL = docker/docker-compose.external-nginx.yml
CONTAINER_BOT = okypbot_app
CONTAINER_DB = okypbot_postgres
CONTAINER_NGINX = okypbot_nginx

# Определение команды Docker Compose
DOCKER_COMPOSE := $(shell if command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; elif docker compose version >/dev/null 2>&1; then echo "docker compose"; else echo "echo 'Error: Docker Compose not found' && exit 1"; fi)

# Помощь
help:
	@echo "🤖 OkypBot Management Commands:"
	@echo ""
	@echo "  deploy        - Полное развертывание (БД + бот + nginx)"
	@echo "  deploy-external - Развертывание без nginx (для внешнего nginx)"
	@echo "  update-bot    - Обновление только бота"
	@echo "  start         - Запуск всех сервисов"
	@echo "  start-external - Запуск без nginx"
	@echo "  stop          - Остановка всех сервисов"
	@echo "  restart       - Перезапуск всех сервисов"
	@echo "  logs          - Просмотр логов"
	@echo "  logs-bot      - Логи только бота"
	@echo "  logs-db       - Логи только БД"
	@echo "  logs-nginx    - Логи только nginx"
	@echo "  status        - Статус сервисов"
	@echo "  shell-bot     - Подключение к контейнеру бота"
	@echo "  shell-db      - Подключение к PostgreSQL"
	@echo "  backup-db     - Бэкап базы данных"
	@echo "  check-ml      - Проверка ML модели"
	@echo "  clean         - Очистка неиспользуемых образов"
	@echo ""
	@echo "🔧 Используется: $(DOCKER_COMPOSE)"

# Развертывание
deploy:
	chmod +x deployment/deploy-full.sh
	./deployment/deploy-full.sh

deploy-external:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_EXTERNAL) up --build -d

# Обновление бота
update-bot:
	chmod +x deployment/update-bot.sh
	./deployment/update-bot.sh

# Управление сервисами
start:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d

start-external:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_EXTERNAL) up -d

stop:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) stop

restart:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) restart

# Логи
logs:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) logs -f

logs-bot:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) logs -f bot

logs-db:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) logs -f postgres

logs-nginx:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) logs -f nginx

# Статус
status:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) ps

# Подключение к контейнерам
shell-bot:
	docker exec -it $(CONTAINER_BOT) bash

shell-db:
	docker exec -it $(CONTAINER_DB) psql -U postgres -d okypbot

# Бэкап
backup-db:
	docker exec $(CONTAINER_DB) pg_dump -U postgres okypbot > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Бэкап создан: backup_$(shell date +%Y%m%d_%H%M%S).sql"

# Проверка ML модели
check-ml:
	chmod +x deployment/check-ml-model.sh
	./deployment/check-ml-model.sh

# Очистка
clean:
	docker system prune -f
	docker image prune -f

.PHONY: help deploy deploy-external update-bot start start-external stop restart logs logs-bot logs-db logs-nginx status shell-bot shell-db backup-db check-ml clean
