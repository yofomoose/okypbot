#!/bin/bash
# Скрипт для проверки версии системы

# Цвета для вывода
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
RED=$(tput setaf 1)
RESET=$(tput sgr0)

echo "🔍 ${YELLOW}Проверка версии системы...${RESET}"

# Проверка git
if ! command -v git &> /dev/null; then
    echo "${RED}❌ Git не установлен!${RESET}"
    echo "${YELLOW}Установите git для корректной работы системы.${RESET}"
    exit 1
fi

# Получение текущей версии из git
GIT_VERSION=$(git describe --tags --always --dirty 2>/dev/null || echo "unknown")

# Создание файла версии, если его нет
if [ ! -f "version.txt" ]; then
    echo "${YELLOW}Создание файла version.txt...${RESET}"
    echo $GIT_VERSION > version.txt
    echo "${GREEN}✓ Создан файл version.txt с версией $GIT_VERSION${RESET}"
else
    # Обновление файла версии
    CURRENT_VERSION=$(cat version.txt)
    
    if [ "$CURRENT_VERSION" != "$GIT_VERSION" ]; then
        echo "${YELLOW}Обновление version.txt с $CURRENT_VERSION на $GIT_VERSION...${RESET}"
        echo $GIT_VERSION > version.txt
        echo "${GREEN}✓ Файл version.txt обновлен${RESET}"
    else
        echo "${GREEN}✓ Файл version.txt содержит актуальную версию${RESET}"
    fi
fi

echo "${YELLOW}Информация о системе:${RESET}"
echo "- Версия: $GIT_VERSION"
echo "- Дата сборки: $(date '+%Y-%m-%d %H:%M:%S')"

# Проверка docker
echo "${YELLOW}Проверка Docker...${RESET}"
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo "${GREEN}✓ Docker установлен: $DOCKER_VERSION${RESET}"
else
    echo "${RED}❌ Docker не установлен!${RESET}"
    echo "${YELLOW}Установите Docker для запуска системы.${RESET}"
    exit 1
fi

# Проверка docker-compose
echo "${YELLOW}Проверка Docker Compose...${RESET}"
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
    DOCKER_COMPOSE_VERSION=$(docker-compose --version)
    echo "${GREEN}✓ Docker Compose установлен: $DOCKER_COMPOSE_VERSION${RESET}"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
    DOCKER_COMPOSE_VERSION=$(docker compose version)
    echo "${GREEN}✓ Docker Compose (новая версия) установлен: $DOCKER_COMPOSE_VERSION${RESET}"
else
    echo "${RED}❌ Docker Compose не установлен!${RESET}"
    echo "${YELLOW}Установите Docker Compose для запуска системы.${RESET}"
    exit 1
fi

# Проверка доступа к интернету
echo "${YELLOW}Проверка доступа к интернету...${RESET}"
if ping -c 1 google.com &> /dev/null; then
    echo "${GREEN}✓ Доступ к интернету есть${RESET}"
else
    echo "${RED}❌ Нет доступа к интернету!${RESET}"
    echo "${YELLOW}Проверьте подключение к интернету.${RESET}"
fi

# Проверка наличия всех необходимых директорий
echo "${YELLOW}Проверка структуры проекта...${RESET}"
required_dirs=("api" "bot_model" "config" "database" "docker" "docs" "handlers" "keyboards" "ml" "scripts" "utils")
missing_dirs=()

for dir in "${required_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        missing_dirs+=("$dir")
    fi
done

if [ ${#missing_dirs[@]} -eq 0 ]; then
    echo "${GREEN}✓ Все необходимые директории присутствуют${RESET}"
else
    echo "${RED}❌ Отсутствуют следующие директории:${RESET}"
    for dir in "${missing_dirs[@]}"; do
        echo "  - $dir"
    done
    echo "${YELLOW}Создание отсутствующих директорий...${RESET}"
    for dir in "${missing_dirs[@]}"; do
        mkdir -p $dir
        echo "${GREEN}✓ Создана директория $dir${RESET}"
    done
fi

# Проверка наличия необходимых файлов
echo "${YELLOW}Проверка ключевых файлов...${RESET}"
key_files=("main.py" "requirements.txt" "docker/Dockerfile" "docker/docker-compose.prod.yml")
missing_files=()

for file in "${key_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -eq 0 ]; then
    echo "${GREEN}✓ Все ключевые файлы присутствуют${RESET}"
else
    echo "${RED}❌ Отсутствуют следующие файлы:${RESET}"
    for file in "${missing_files[@]}"; do
        echo "  - $file"
    done
    echo "${YELLOW}⚠️ Система может работать некорректно без этих файлов${RESET}"
fi

echo ""
echo "${YELLOW}Результаты проверки системы:${RESET}"
if [ ${#missing_dirs[@]} -eq 0 ] && [ ${#missing_files[@]} -eq 0 ]; then
    echo "${GREEN}✅ Система в полном порядке!${RESET}"
else
    echo "${YELLOW}⚠️ Обнаружены проблемы, требуется внимание${RESET}"
fi
