#!/bin/bash
# Скрипт для обучения ML модели на новых данных

# Цвета для вывода
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
RED=$(tput setaf 1)
RESET=$(tput sgr0)

# Имя контейнера
CONTAINER_NAME="okypbot_app"

echo "🧠 ${YELLOW}Запуск процесса обучения ML модели...${RESET}"

# Проверяем, запущен ли контейнер
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "${RED}❌ Контейнер $CONTAINER_NAME не запущен!${RESET}"
    echo "${YELLOW}Запускаем контейнер...${RESET}"
    
    # Определение docker-compose команды
    if command -v docker-compose >/dev/null 2>&1; then
        DOCKER_COMPOSE="docker-compose"
    elif docker compose version >/dev/null 2>&1; then
        DOCKER_COMPOSE="docker compose"
    else
        echo "${RED}❌ Docker Compose не найден!${RESET}"
        exit 1
    fi
    
    # Запускаем контейнер
    COMPOSE_FILE="docker/docker-compose.prod.yml"
    $DOCKER_COMPOSE -f $COMPOSE_FILE up -d bot
    
    # Ждем запуска контейнера
    echo "${YELLOW}Ожидаем запуск контейнера...${RESET}"
    sleep 10
    
    if ! docker ps | grep -q "$CONTAINER_NAME"; then
        echo "${RED}❌ Не удалось запустить контейнер $CONTAINER_NAME!${RESET}"
        exit 1
    fi
fi

# Создаем временную директорию
TMP_DIR="/tmp/okypbot_ml_train"
mkdir -p $TMP_DIR

echo "${YELLOW}1. Создание резервной копии текущей модели...${RESET}"

# Создаем директорию для бэкапа
BACKUP_DIR="bot_model/backups"
mkdir -p $BACKUP_DIR

# Формируем имя бэкапа с датой и временем
BACKUP_NAME="model_backup_$(date +%Y%m%d_%H%M%S)"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
mkdir -p $BACKUP_PATH

# Копируем текущие файлы модели из контейнера
docker cp $CONTAINER_NAME:/app/bot_model/classifier.pkl $BACKUP_PATH/ 2>/dev/null
docker cp $CONTAINER_NAME:/app/bot_model/label_encoder.pkl $BACKUP_PATH/ 2>/dev/null
docker cp $CONTAINER_NAME:/app/bot_model/model_metadata.json $BACKUP_PATH/ 2>/dev/null
docker cp $CONTAINER_NAME:/app/bot_model/training_examples.pkl $BACKUP_PATH/ 2>/dev/null

echo "${GREEN}✓ Резервная копия модели создана: $BACKUP_PATH${RESET}"

echo "${YELLOW}2. Создание скрипта для обучения модели...${RESET}"

# Создаем скрипт обучения
cat > $TMP_DIR/train_model.py << 'EOL'
import sys
import os
import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# Функция загрузки данных для обучения
def load_training_data():
    # Пытаемся загрузить существующие примеры
    try:
        with open('/app/bot_model/training_examples.pkl', 'rb') as f:
            existing_data = pickle.load(f)
            print(f"Загружено {len(existing_data)} существующих примеров")
    except (FileNotFoundError, EOFError):
        existing_data = []
        print("Существующие примеры не найдены, создаем новый набор данных")
    
    # Пытаемся загрузить пользовательские запросы из базы данных
    try:
        from database.models import Classification
        from config.db_config import Session
        
        session = Session()
        db_samples = session.query(Classification).all()
        
        if db_samples:
            print(f"Найдено {len(db_samples)} примеров в базе данных")
            for sample in db_samples:
                existing_data.append({
                    'text': sample.text,
                    'category': sample.category
                })
        session.close()
    except Exception as e:
        print(f"Ошибка при загрузке данных из базы: {str(e)}")
    
    # Преобразуем в DataFrame
    df = pd.DataFrame(existing_data)
    
    # Проверяем наличие данных
    if df.empty:
        print("Ошибка: нет данных для обучения!")
        sys.exit(1)
    
    print(f"Итого для обучения: {len(df)} примеров")
    print(f"Количество категорий: {df['category'].nunique()}")
    
    return df

# Функция обучения модели
def train_model(df):
    # Проверяем минимальное количество примеров
    if len(df) < 10:
        print("Предупреждение: очень мало данных для обучения. Результаты могут быть неточными.")
    
    # Разделяем на признаки и метки
    X = df['text']
    y = df['category']
    
    # Кодируем метки
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    # Разделяем на обучающую и тестовую выборки
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded if len(df) >= 10 else None
    )
    
    print(f"Обучающая выборка: {len(X_train)} примеров")
    print(f"Тестовая выборка: {len(X_test)} примеров")
    
    # Создаем векторизатор и трансформируем текст
    vectorizer = TfidfVectorizer(
        max_features=5000, 
        ngram_range=(1, 2), 
        min_df=2, 
        max_df=0.9
    )
    
    # Обучаем векторизатор на обучающей выборке
    X_train_tfidf = vectorizer.fit_transform(X_train)
    
    # Трансформируем тестовую выборку
    X_test_tfidf = vectorizer.transform(X_test)
    
    # Обучаем классификатор
    print("Начинаем обучение модели...")
    classifier = RandomForestClassifier(
        n_estimators=100, 
        max_depth=10,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'
    )
    
    # Обучаем модель
    classifier.fit(X_train_tfidf, y_train)
    
    # Оцениваем точность
    y_pred = classifier.predict(X_test_tfidf)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"Точность модели: {accuracy:.4f}")
    
    # Сохраняем модель и векторизатор в единый объект
    combined_model = {
        'vectorizer': vectorizer,
        'classifier': classifier
    }
    
    # Создаем метаданные модели
    git_version = "unknown"
    try:
        with open('/app/version.txt', 'r') as f:
            git_version = f.read().strip()
    except:
        pass
    
    metadata = {
        'version': f"{datetime.now().strftime('%Y%m%d')}-{len(df)}",
        'trained_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'accuracy': f"{accuracy:.4f}",
        'samples_count': len(df),
        'categories_count': len(label_encoder.classes_),
        'categories': label_encoder.classes_.tolist(),
        'required_code_version': git_version
    }
    
    # Возвращаем обученную модель, кодировщик и метаданные
    return combined_model, label_encoder, metadata, df

# Функция сохранения модели
def save_model(combined_model, label_encoder, metadata, training_data):
    # Сохраняем модель
    with open('/app/bot_model/classifier.pkl', 'wb') as f:
        pickle.dump(combined_model, f)
    
    # Сохраняем кодировщик меток
    with open('/app/bot_model/label_encoder.pkl', 'wb') as f:
        pickle.dump(label_encoder, f)
    
    # Сохраняем метаданные
    with open('/app/bot_model/model_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=4)
    
    # Сохраняем обучающие данные
    training_data_list = training_data.to_dict('records')
    with open('/app/bot_model/training_examples.pkl', 'wb') as f:
        pickle.dump(training_data_list, f)
    
    print("Модель успешно сохранена!")

# Функция тестирования модели
def test_model(combined_model, label_encoder):
    # Тестовые фразы
    test_phrases = [
        "Не работает интернет",
        "Хочу сообщить о проблеме с оплатой",
        "Как узнать статус моей заявки?",
        "Мне нужна помощь с настройкой оборудования",
        "Хочу оформить новый заказ"
    ]
    
    print("\nТестирование модели на примерах:")
    
    vectorizer = combined_model['vectorizer']
    classifier = combined_model['classifier']
    
    for phrase in test_phrases:
        # Векторизуем фразу
        phrase_tfidf = vectorizer.transform([phrase])
        
        # Предсказываем категорию
        predicted_category_id = classifier.predict(phrase_tfidf)[0]
        predicted_category = label_encoder.inverse_transform([predicted_category_id])[0]
        
        print(f"Фраза: '{phrase}'")
        print(f"Категория: {predicted_category}")
        print()

# Главная функция
def main():
    print("Запуск процесса обучения ML модели...")
    
    # Загружаем данные
    training_data = load_training_data()
    
    # Обучаем модель
    combined_model, label_encoder, metadata, df = train_model(training_data)
    
    # Сохраняем модель
    save_model(combined_model, label_encoder, metadata, df)
    
    # Тестируем модель
    test_model(combined_model, label_encoder)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
EOL

echo "${GREEN}✓ Скрипт обучения создан${RESET}"

echo "${YELLOW}3. Копирование скрипта в контейнер...${RESET}"
docker cp $TMP_DIR/train_model.py $CONTAINER_NAME:/tmp/train_model.py

echo "${YELLOW}4. Запуск процесса обучения...${RESET}"
echo "${YELLOW}   Этот процесс может занять некоторое время, пожалуйста, подождите...${RESET}"

# Запускаем обучение в контейнере
if docker exec -e PYTHONPATH=/app $CONTAINER_NAME python /tmp/train_model.py; then
    echo "${GREEN}✅ Модель успешно обучена!${RESET}"
    
    # Копируем обновленные файлы модели из контейнера в локальную директорию
    echo "${YELLOW}5. Синхронизация обученной модели с локальной директорией...${RESET}"
    
    mkdir -p bot_model
    docker cp $CONTAINER_NAME:/app/bot_model/classifier.pkl bot_model/
    docker cp $CONTAINER_NAME:/app/bot_model/label_encoder.pkl bot_model/
    docker cp $CONTAINER_NAME:/app/bot_model/model_metadata.json bot_model/
    docker cp $CONTAINER_NAME:/app/bot_model/training_examples.pkl bot_model/
    
    echo "${GREEN}✓ Файлы модели синхронизированы с локальной директорией${RESET}"
    
    # Запускаем проверку модели
    echo "${YELLOW}6. Проверка работоспособности обученной модели...${RESET}"
    chmod +x scripts/check_ml_model.sh
    ./scripts/check_ml_model.sh
else
    echo "${RED}❌ Ошибка при обучении модели!${RESET}"
    echo "${YELLOW}Проверьте логи выше для получения информации об ошибке.${RESET}"
    
    # Восстанавливаем модель из резервной копии
    if [ -d "$BACKUP_PATH" ] && [ -f "$BACKUP_PATH/classifier.pkl" ]; then
        echo "${YELLOW}Восстанавливаем модель из резервной копии...${RESET}"
        
        docker cp $BACKUP_PATH/classifier.pkl $CONTAINER_NAME:/app/bot_model/
        docker cp $BACKUP_PATH/label_encoder.pkl $CONTAINER_NAME:/app/bot_model/
        docker cp $BACKUP_PATH/model_metadata.json $CONTAINER_NAME:/app/bot_model/
        docker cp $BACKUP_PATH/training_examples.pkl $CONTAINER_NAME:/app/bot_model/
        
        echo "${GREEN}✓ Модель восстановлена из резервной копии${RESET}"
    else
        echo "${RED}❌ Резервная копия модели не найдена или неполная!${RESET}"
    fi
fi

# Очистка временных файлов
rm -rf $TMP_DIR
