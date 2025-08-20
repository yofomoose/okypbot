# Makefile для управления OkypBot

# Переменные
COMPOSE_FILE = docker-compose.prod.yml
COMPOSE_FILE_EXTERNAL = docker-compose.external-nginx.yml
CONTAINER_BOT = okypbot_app
CONTAINER_DB = okypbot_postgres
CONTAINER_NGINX = okypbot_nginx

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

# Развертывание
deploy:
	chmod +x deploy-full.sh
	./deploy-full.sh

deploy-external:
	docker-compose -f $(COMPOSE_FILE_EXTERNAL) up --build -d

# Обновление бота
update-bot:
	chmod +x update-bot.sh
	./update-bot.sh

# Управление сервисами
start:
	docker-compose -f $(COMPOSE_FILE) up -d

start-external:
	docker-compose -f $(COMPOSE_FILE_EXTERNAL) up -d

stop:
	docker-compose -f $(COMPOSE_FILE) stop

restart:
	docker-compose -f $(COMPOSE_FILE) restart

# Логи
logs:
	docker-compose -f $(COMPOSE_FILE) logs -f

logs-bot:
	docker-compose -f $(COMPOSE_FILE) logs -f bot

logs-db:
	docker-compose -f $(COMPOSE_FILE) logs -f postgres

logs-nginx:
	docker-compose -f $(COMPOSE_FILE) logs -f nginx

# Статус
status:
	docker-compose -f $(COMPOSE_FILE) ps

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
	chmod +x check-ml-model.sh
	./check-ml-model.sh

# Очистка
clean:
	docker system prune -f
	docker image prune -f

.PHONY: help deploy deploy-external update-bot start start-external stop restart logs logs-bot logs-db logs-nginx status shell-bot shell-db backup-db check-ml clean
