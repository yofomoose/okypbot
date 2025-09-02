# Команды для сохранения данных регистрации при пересборке Docker контейнеров

# Переменные
DATA_BACKUP_DIR = database_backup

# Директория для резервных копий
$(DATA_BACKUP_DIR):
	@mkdir -p $(DATA_BACKUP_DIR)

# Резервное копирование данных регистрации
backup-data: $(DATA_BACKUP_DIR)
	@echo "💾 Создание резервной копии данных регистрации..."
	@docker cp $(CONTAINER_BOT):/app/database/users.json $(DATA_BACKUP_DIR)/users_$$(date +%Y%m%d_%H%M%S).json 2>/dev/null || echo "    ⚠️ Файл users.json не найден в контейнере"
	@docker cp $(CONTAINER_BOT):/app/database/user_issues.json $(DATA_BACKUP_DIR)/user_issues_$$(date +%Y%m%d_%H%M%S).json 2>/dev/null || echo "    ⚠️ Файл user_issues.json не найден в контейнере"
	@docker cp $(CONTAINER_BOT):/app/database/employee_mapping.json $(DATA_BACKUP_DIR)/employee_mapping_$$(date +%Y%m%d_%H%M%S).json 2>/dev/null || echo "    ⚠️ Файл employee_mapping.json не найден в контейнере"
	@echo "✅ Резервная копия данных создана в $(DATA_BACKUP_DIR)/"

# Восстановление данных регистрации
restore-data:
	@echo "📥 Восстановление данных регистрации..."
	@LATEST_USERS=$$(ls -t $(DATA_BACKUP_DIR)/users_*.json 2>/dev/null | head -1); \
	LATEST_ISSUES=$$(ls -t $(DATA_BACKUP_DIR)/user_issues_*.json 2>/dev/null | head -1); \
	LATEST_MAPPING=$$(ls -t $(DATA_BACKUP_DIR)/employee_mapping_*.json 2>/dev/null | head -1); \
	\
	if [ -n "$$LATEST_USERS" ] || [ -n "$$LATEST_ISSUES" ] || [ -n "$$LATEST_MAPPING" ]; then \
		docker exec -i $(CONTAINER_BOT) mkdir -p /app/database; \
		\
		if [ -n "$$LATEST_USERS" ]; then \
			docker cp $$LATEST_USERS $(CONTAINER_BOT):/app/database/users.json; \
			echo "  ✅ Данные пользователей восстановлены из $$(basename $$LATEST_USERS)"; \
		fi; \
		\
		if [ -n "$$LATEST_ISSUES" ]; then \
			docker cp $$LATEST_ISSUES $(CONTAINER_BOT):/app/database/user_issues.json; \
			echo "  ✅ Данные заявок восстановлены из $$(basename $$LATEST_ISSUES)"; \
		fi; \
		\
		if [ -n "$$LATEST_MAPPING" ]; then \
			docker cp $$LATEST_MAPPING $(CONTAINER_BOT):/app/database/employee_mapping.json; \
			echo "  ✅ Данные сопоставлений восстановлены из $$(basename $$LATEST_MAPPING)"; \
		fi; \
		\
		docker exec -i $(CONTAINER_BOT) chmod 777 /app/database; \
		docker exec -i $(CONTAINER_BOT) chmod 666 /app/database/*.json; \
		\
		echo "  🔄 Перезапуск бота для применения изменений..."; \
		docker restart $(CONTAINER_BOT); \
		echo "  ✅ Бот перезапущен с восстановленными данными"; \
	else \
		echo "  ⚠️ Резервных копий не найдено, пропускаем восстановление..."; \
	fi

# Безопасное обновление бота с сохранением данных регистрации
update-safe: backup-data
	@echo "🔄 Начинаем безопасное обновление бота с сохранением данных регистрации..."
	@echo "1. Проверка изменений..."
	@git fetch origin
	@if [ "$$(git rev-parse HEAD)" = "$$(git rev-parse @{u})" ]; then \
		echo "$(GREEN)✓ Бот уже обновлен до последней версии$(RESET)"; \
		exit 0; \
	fi
	
	@echo "2. Создание резервной копии БД..."
	@make backup
	
	@echo "3. Получение обновлений..."
	@if git pull; then \
		echo "$(GREEN)✓ Код успешно обновлен$(RESET)"; \
	else \
		echo "$(RED)❌ Ошибка при получении обновлений$(RESET)"; \
		exit 1; \
	fi
	
	@echo "4. Проверка изменений в зависимостях..."
	@if git diff HEAD@{1} --name-only | grep -q "requirements.txt"; then \
		echo "📦 Обнаружены изменения в requirements.txt"; \
		echo "5. Полная пересборка контейнера..."; \
		$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) build --no-cache bot; \
	else \
		echo "5. Быстрая пересборка контейнера..."; \
		$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) build bot; \
	fi
	
	@echo "6. Перезапуск сервисов..."
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) stop bot
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) rm -f bot
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d bot
	
	@echo "7. Восстановление данных регистрации..."
	@sleep 10
	@make restore-data
	
	@echo "8. Проверка статуса..."
	@sleep 5
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) ps bot
	
	@echo "9. Проверка логов на ошибки..."
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) logs --tail=20 bot
	
	@echo "$(GREEN)✅ Бот успешно обновлен с сохранением данных регистрации!$(RESET)"
	@echo "💡 Используйте 'make logs' для просмотра полных логов"

# Безопасная пересборка контейнера с сохранением данных регистрации
rebuild-safe: backup-data stop
	@echo "🏗️ Безопасная пересборка контейнера с сохранением данных регистрации..."
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) build --no-cache bot
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d bot
	@sleep 10
	@make restore-data
	@echo "✅ Пересборка завершена, данные восстановлены"
	@make status

# Исправление тома для хранения данных в Docker
fix-persistence: backup-data
	@echo "🔧 Настройка постоянного тома для данных..."
	@echo "1. Проверка текущей конфигурации..."
	
	@if grep -q "../database:/app/database" $(COMPOSE_FILE); then \
		echo "$(GREEN)✓ Том для директории database уже настроен в $(COMPOSE_FILE)$(RESET)"; \
	else \
		echo "$(YELLOW)⚠️ Настраиваем том для директории database в $(COMPOSE_FILE)...$(RESET)"; \
		mkdir -p database; \
		sed -i '/volumes:/a \ \ \ \ \ \ - ../database:/app/database' $(COMPOSE_FILE) || echo "$(RED)❌ Не удалось обновить конфигурацию Docker$(RESET)"; \
		if grep -q "../database:/app/database" $(COMPOSE_FILE); then \
			echo "$(GREEN)✓ Том для директории database успешно добавлен в $(COMPOSE_FILE)$(RESET)"; \
		else \
			echo "$(RED)❌ Не удалось добавить том для директории database в $(COMPOSE_FILE)$(RESET)"; \
			echo "Добавьте вручную строку '- ../database:/app/database' в раздел volumes сервиса bot в файле $(COMPOSE_FILE)"; \
		fi; \
	fi
	
	@echo "2. Применяем изменения..."
	@make rebuild-safe
	
	@echo "✅ Настройка постоянного тома для данных завершена"

# Помощь по новым командам
help-persistence:
	@echo ""
	@echo "$(YELLOW)Команды для сохранения данных регистрации:$(RESET)"
	@echo "  make backup-data       - Создание резервной копии данных регистрации"
	@echo "  make restore-data      - Восстановление данных регистрации"
	@echo "  make update-safe       - Обновление бота с сохранением данных"
	@echo "  make rebuild-safe      - Пересборка с сохранением данных"
	@echo "  make fix-persistence   - Исправление проблемы сохранения данных"
