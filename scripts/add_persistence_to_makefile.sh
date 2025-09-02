#!/usr/bin/env bash
# add_persistence_to_makefile.sh
# Скрипт для интеграции команд сохранения данных в основной Makefile

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Интеграция команд сохранения данных в Makefile ===${NC}"

# Проверка наличия файлов
if [ ! -f "Makefile" ]; then
    echo -e "${RED}❌ Файл Makefile не найден${NC}"
    exit 1
fi

if [ ! -f "Makefile.persistence" ]; then
    echo -e "${RED}❌ Файл Makefile.persistence не найден${NC}"
    exit 1
fi

# Создаем резервную копию оригинального Makefile
echo "📑 Создание резервной копии Makefile..."
cp Makefile Makefile.bak
echo -e "${GREEN}✓ Резервная копия создана: Makefile.bak${NC}"

# Добавляем include директиву в конец Makefile
echo "📝 Добавление директивы include в Makefile..."
echo "" >> Makefile
echo "# Включение модуля сохранения данных при пересборке контейнеров" >> Makefile
echo "include Makefile.persistence" >> Makefile

# Модифицируем раздел help для добавления новых команд
echo "🔄 Обновление справки в Makefile..."
sed -i "s/.PHONY: help setup deploy update start stop restart rebuild logs logs-bot logs-db status backup restore check-db check-ml train-ml clean clean-all disk-usage/.PHONY: help setup deploy update start stop restart rebuild logs logs-bot logs-db status backup restore check-db check-ml train-ml clean clean-all disk-usage backup-data restore-data update-safe rebuild-safe fix-persistence help-persistence/" Makefile

# Модифицируем команду help для вызова help-persistence
sed -i '/help:/,/OMP_NUM_THREADS/ s/\(@echo ".*Обслуживание.*"\)/\1\n\t@make help-persistence/' Makefile

echo -e "${GREEN}✓ Makefile обновлен${NC}"
echo -e "${YELLOW}Теперь доступны следующие команды:${NC}"
echo "  make backup-data   - Создание резервной копии данных регистрации"
echo "  make restore-data  - Восстановление данных регистрации"
echo "  make update-safe   - Обновление с сохранением данных регистрации"
echo "  make rebuild-safe  - Пересборка с сохранением данных регистрации"
echo "  make fix-persistence - Исправление проблемы сохранения данных"

echo -e "\n${GREEN}=== Интеграция завершена ===${NC}"
echo -e "Для применения изменений в продакшене выполните: ${YELLOW}make fix-persistence${NC}"
