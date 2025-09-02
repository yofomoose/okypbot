#!/bin/bash
# Скрипт для проверки синхронизации кода ML между хостом и контейнером

# Цвета для вывода
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
RED=$(tput setaf 1)
RESET=$(tput sgr0)

# Имя контейнера
CONTAINER_NAME="okypbot_app"

echo "🔍 ${YELLOW}Проверка синхронизации кода ML между хостом и контейнером...${RESET}"

# Проверяем, запущен ли контейнер
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "${RED}❌ Контейнер $CONTAINER_NAME не запущен!${RESET}"
    exit 1
fi

# Создаем временные файлы для хэшей
HOST_HASH_FILE="/tmp/ml_host_checksums.txt"
CONTAINER_HASH_FILE="/tmp/ml_container_checksums.txt"

# Очищаем предыдущие результаты
rm -f $HOST_HASH_FILE $CONTAINER_HASH_FILE

# Проверяем ML модуль на хосте
echo "${YELLOW}1. Проверка ML файлов на хосте...${RESET}"

if [ -d "ml" ]; then
    find ml -type f -name "*.py" | sort | while read file; do
        md5sum "$file" | tee -a $HOST_HASH_FILE
    done
else
    echo "${RED}❌ Директория ml не найдена на хосте!${RESET}"
    exit 1
fi

# Проверяем ML модуль в контейнере
echo "${YELLOW}2. Проверка ML файлов в контейнере...${RESET}"

# Проверяем существование директории ml в контейнере
if ! docker exec $CONTAINER_NAME ls -la /app/ml >/dev/null 2>&1; then
    echo "${RED}❌ Директория ml не найдена в контейнере!${RESET}"
    exit 1
fi

# Получаем список файлов и их хэши в контейнере
docker exec $CONTAINER_NAME find /app/ml -type f -name "*.py" | sort | while read file; do
    # Извлекаем относительный путь (удаляем префикс /app/)
    rel_path=$(echo $file | sed 's|^/app/||')
    
    # Получаем хэш файла в контейнере
    container_hash=$(docker exec $CONTAINER_NAME md5sum $file)
    
    # Выводим хэш с относительным путем
    echo "$container_hash" | sed "s|$file|$rel_path|" | tee -a $CONTAINER_HASH_FILE
done

# Сравниваем хэши
echo "${YELLOW}3. Сравнение хэшей...${RESET}"

# Счетчики для статистики
total_files=$(grep -c "" $HOST_HASH_FILE || echo 0)
sync_files=0
diff_files=0
missing_files=0

while read -r line; do
    # Извлекаем хэш и имя файла
    hash=$(echo $line | cut -d ' ' -f 1)
    file=$(echo $line | cut -d ' ' -f 2-)
    
    # Проверяем наличие файла в контейнере
    container_hash=$(grep "$file" $CONTAINER_HASH_FILE | cut -d ' ' -f 1)
    
    if [ -z "$container_hash" ]; then
        echo "${RED}❌ Файл $file отсутствует в контейнере!${RESET}"
        missing_files=$((missing_files + 1))
    elif [ "$hash" != "$container_hash" ]; then
        echo "${RED}❌ Файл $file отличается:${RESET}"
        echo "   - Хост:      $hash"
        echo "   - Контейнер: $container_hash"
        diff_files=$((diff_files + 1))
    else
        echo "${GREEN}✓ Файл $file синхронизирован${RESET}"
        sync_files=$((sync_files + 1))
    fi
done < $HOST_HASH_FILE

# Выводим статистику
echo ""
echo "${YELLOW}Итоги проверки синхронизации:${RESET}"
echo "  - Всего файлов: $total_files"
echo "  - Синхронизировано: ${GREEN}$sync_files${RESET}"

if [ $diff_files -gt 0 ]; then
    echo "  - Отличаются: ${RED}$diff_files${RESET}"
fi

if [ $missing_files -gt 0 ]; then
    echo "  - Отсутствуют: ${RED}$missing_files${RESET}"
fi

if [ $diff_files -eq 0 ] && [ $missing_files -eq 0 ]; then
    echo ""
    echo "${GREEN}✅ Все файлы ML модуля синхронизированы!${RESET}"
    exit 0
else
    echo ""
    echo "${RED}❌ Обнаружены различия в файлах ML модуля!${RESET}"
    echo "${YELLOW}Рекомендуется выполнить пересборку контейнера: make rebuild-safe${RESET}"
    exit 1
fi
