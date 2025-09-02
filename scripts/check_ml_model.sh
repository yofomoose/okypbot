#!/bin/bash
# Скрипт для проверки совместимости ML модели с текущим кодом бота

# Цвета для вывода
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
RED=$(tput setaf 1)
RESET=$(tput sgr0)

# Имя контейнера
CONTAINER_NAME="okypbot_app"

echo "🔍 ${YELLOW}Проверка совместимости ML модели с текущим кодом бота...${RESET}"

# Проверяем, запущен ли контейнер
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "${RED}❌ Контейнер $CONTAINER_NAME не запущен!${RESET}"
    exit 1
fi

# Создаем временную директорию
TMP_DIR="/tmp/okypbot_ml_check"
mkdir -p $TMP_DIR

echo "${YELLOW}1. Получение метаданных ML модели...${RESET}"

# Получаем метаданные модели
docker cp $CONTAINER_NAME:/app/bot_model/model_metadata.json $TMP_DIR/model_metadata.json 2>/dev/null

if [ ! -f "$TMP_DIR/model_metadata.json" ]; then
    echo "${RED}❌ Файл метаданных модели не найден!${RESET}"
    echo "${YELLOW}⚠️ Возможно, модель не загружена или повреждена.${RESET}"
    exit 1
fi

# Читаем метаданные модели
MODEL_VERSION=$(cat $TMP_DIR/model_metadata.json | grep -o '"version":[^,}]*' | cut -d':' -f2 | tr -d '" ')
MODEL_DATE=$(cat $TMP_DIR/model_metadata.json | grep -o '"trained_date":[^,}]*' | cut -d':' -f2 | tr -d '" ')
MODEL_ACCURACY=$(cat $TMP_DIR/model_metadata.json | grep -o '"accuracy":[^,}]*' | cut -d':' -f2 | tr -d ', ')
MODEL_SAMPLES=$(cat $TMP_DIR/model_metadata.json | grep -o '"samples_count":[^,}]*' | cut -d':' -f2 | tr -d ', ')
MODEL_CATEGORIES=$(cat $TMP_DIR/model_metadata.json | grep -o '"categories_count":[^,}]*' | cut -d':' -f2 | tr -d ', ')
MODEL_REQUIRED_CODE_VERSION=$(cat $TMP_DIR/model_metadata.json | grep -o '"required_code_version":[^,}]*' | cut -d':' -f2 | tr -d '" ')

echo "${GREEN}✓ Метаданные модели получены:${RESET}"
echo "   - Версия модели: $MODEL_VERSION"
echo "   - Дата обучения: $MODEL_DATE"
echo "   - Точность: $MODEL_ACCURACY"
echo "   - Количество образцов: $MODEL_SAMPLES"
echo "   - Количество категорий: $MODEL_CATEGORIES"
echo "   - Требуемая версия кода: $MODEL_REQUIRED_CODE_VERSION"

echo "${YELLOW}2. Получение текущей версии кода...${RESET}"

# Получаем версию кода из контейнера
docker exec $CONTAINER_NAME cat /app/version.txt > $TMP_DIR/version.txt 2>/dev/null

if [ ! -f "$TMP_DIR/version.txt" ]; then
    echo "${YELLOW}⚠️ Файл version.txt не найден в контейнере, создаем...${RESET}"
    
    # Создаем файл версии из git, если его нет
    GIT_VERSION=$(git describe --tags --always --dirty 2>/dev/null || echo "unknown")
    echo $GIT_VERSION > $TMP_DIR/version.txt
    
    # Копируем в контейнер
    docker cp $TMP_DIR/version.txt $CONTAINER_NAME:/app/version.txt
fi

CURRENT_VERSION=$(cat $TMP_DIR/version.txt)
echo "${GREEN}✓ Текущая версия кода: $CURRENT_VERSION${RESET}"

echo "${YELLOW}3. Проверка совместимости версий...${RESET}"

if [ -z "$MODEL_REQUIRED_CODE_VERSION" ] || [ "$MODEL_REQUIRED_CODE_VERSION" == "null" ]; then
    echo "${YELLOW}⚠️ В метаданных модели не указана требуемая версия кода${RESET}"
    echo "   Пропускаем проверку совместимости версий"
else
    # Сравниваем версии (простое сравнение строк)
    if [ "$MODEL_REQUIRED_CODE_VERSION" == "$CURRENT_VERSION" ]; then
        echo "${GREEN}✓ Версия кода соответствует требованиям модели${RESET}"
    else
        echo "${RED}❌ Версия кода ($CURRENT_VERSION) не соответствует требуемой ($MODEL_REQUIRED_CODE_VERSION)!${RESET}"
        echo "${YELLOW}⚠️ Возможны проблемы с работой ML классификатора${RESET}"
    fi
fi

echo "${YELLOW}4. Проверка структуры файлов модели...${RESET}"

# Список необходимых файлов
required_files=(
    "/app/bot_model/classifier.pkl"
    "/app/bot_model/label_encoder.pkl"
    "/app/bot_model/model_metadata.json"
    "/app/bot_model/training_examples.pkl"
)

all_files_exist=true

for file in "${required_files[@]}"; do
    if docker exec $CONTAINER_NAME ls $file >/dev/null 2>&1; then
        echo "${GREEN}✓ Файл $file существует${RESET}"
    else
        echo "${RED}❌ Файл $file отсутствует!${RESET}"
        all_files_exist=false
    fi
done

if [ "$all_files_exist" = true ]; then
    echo "${GREEN}✓ Все необходимые файлы модели присутствуют${RESET}"
else
    echo "${RED}❌ Некоторые файлы модели отсутствуют!${RESET}"
fi

echo "${YELLOW}5. Проверка работоспособности модели...${RESET}"

# Создаем временный скрипт для тестирования модели
cat > $TMP_DIR/test_model.py << EOL
import sys
import os
import pickle
import json

try:
    # Загружаем модель
    print("Загрузка модели...")
    with open('/app/bot_model/classifier.pkl', 'rb') as f:
        classifier = pickle.load(f)
    
    with open('/app/bot_model/label_encoder.pkl', 'rb') as f:
        label_encoder = pickle.load(f)
    
    # Тестовый запрос
    test_text = "Не работает интернет"
    
    print(f"Тестовая классификация текста: '{test_text}'")
    
    # Предсказание
    predicted_category_id = classifier.predict([test_text])[0]
    predicted_category = label_encoder.inverse_transform([predicted_category_id])[0]
    
    print(f"Результат классификации: {predicted_category}")
    print("Тест успешно завершен!")
    sys.exit(0)
except Exception as e:
    print(f"Ошибка при тестировании модели: {str(e)}")
    sys.exit(1)
EOL

# Копируем скрипт в контейнер
docker cp $TMP_DIR/test_model.py $CONTAINER_NAME:/tmp/test_model.py

# Запускаем тестовый скрипт
echo "Запуск тестовой классификации..."
if docker exec $CONTAINER_NAME python /tmp/test_model.py; then
    echo "${GREEN}✅ Тест модели успешно выполнен, модель работоспособна!${RESET}"
else
    echo "${RED}❌ Тест модели завершился с ошибкой!${RESET}"
    echo "${YELLOW}⚠️ Рекомендуется переобучить модель: make train-ml${RESET}"
fi

# Очистка временных файлов
rm -rf $TMP_DIR

echo ""
echo "${YELLOW}Результаты проверки ML модели:${RESET}"
if [ "$all_files_exist" = true ]; then
    echo "${GREEN}✓ Структура файлов модели в порядке${RESET}"
else
    echo "${RED}❌ Проблемы со структурой файлов модели${RESET}"
fi

echo ""
echo "${YELLOW}Рекомендации:${RESET}"
if [ "$all_files_exist" = false ]; then
    echo "1. ${YELLOW}Восстановите отсутствующие файлы модели из резервной копии${RESET}"
    echo "2. ${YELLOW}Или переобучите модель: make train-ml${RESET}"
elif [ "$MODEL_REQUIRED_CODE_VERSION" != "$CURRENT_VERSION" ] && [ -n "$MODEL_REQUIRED_CODE_VERSION" ] && [ "$MODEL_REQUIRED_CODE_VERSION" != "null" ]; then
    echo "${YELLOW}Обновите код до версии $MODEL_REQUIRED_CODE_VERSION или переобучите модель для текущей версии кода${RESET}"
else
    echo "${GREEN}Модель совместима с текущей версией кода и готова к использованию${RESET}"
fi
