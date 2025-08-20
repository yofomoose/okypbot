#!/bin/bash
# Скрипт проверки ML модели OkypBot

echo "🤖 Проверка ML модели OkypBot"
echo "=================================="

# Переменные
ML_DIR="./ml/models"
REQUIRED_FILES=("issue_classifier.pkl" "vectorizer.pkl" "label_encoder.pkl")
CONTAINER_NAME="okypbot_app"

# Проверка существования папки ml/models
if [ ! -d "$ML_DIR" ]; then
    echo "❌ Папка $ML_DIR не найдена!"
    echo "Создание папки..."
    mkdir -p "$ML_DIR"
    echo "✅ Папка создана: $ML_DIR"
fi

echo ""
echo "📁 Проверка файлов ML модели:"
echo "------------------------------"

# Проверка наличия файлов модели
missing_files=()
for file in "${REQUIRED_FILES[@]}"; do
    file_path="$ML_DIR/$file"
    if [ -f "$file_path" ]; then
        size=$(stat -f%z "$file_path" 2>/dev/null || stat -c%s "$file_path" 2>/dev/null || echo "unknown")
        echo "✅ $file (размер: $size байт)"
    else
        echo "❌ $file - отсутствует"
        missing_files+=("$file")
    fi
done

echo ""

# Если есть отсутствующие файлы
if [ ${#missing_files[@]} -gt 0 ]; then
    echo "⚠️  Отсутствующие файлы модели:"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    echo ""
    echo "📥 Варианты получения ML модели:"
    echo "1. Скачать с облачного хранилища:"
    echo "   wget https://your-storage.com/models/$file -O $ML_DIR/$file"
    echo ""
    echo "2. Скопировать с локального компьютера:"
    echo "   scp ml/models/* user@server:$ML_DIR/"
    echo ""
    echo "3. Обучить модель заново:"
    echo "   python ml/training/train_model.py"
    echo ""
else
    echo "✅ Все файлы ML модели найдены!"
fi

# Проверка работы модели в контейнере (если запущен)
echo "🐳 Проверка в Docker контейнере:"
echo "---------------------------------"

if docker ps | grep -q "$CONTAINER_NAME"; then
    echo "✅ Контейнер $CONTAINER_NAME запущен"
    
    echo "📂 Проверка файлов в контейнере:"
    docker exec "$CONTAINER_NAME" ls -la /app/ml/models/ 2>/dev/null || echo "❌ Папка /app/ml/models/ недоступна в контейнере"
    
    echo ""
    echo "🧪 Тест загрузки ML модели:"
    docker exec "$CONTAINER_NAME" python -c "
import sys
sys.path.append('/app')
try:
    # Попытка импорта и загрузки модели
    import pickle
    import os
    
    model_files = {
        'classifier': '/app/ml/models/issue_classifier.pkl',
        'vectorizer': '/app/ml/models/vectorizer.pkl', 
        'encoder': '/app/ml/models/label_encoder.pkl'
    }
    
    loaded = {}
    for name, path in model_files.items():
        if os.path.exists(path):
            try:
                with open(path, 'rb') as f:
                    loaded[name] = pickle.load(f)
                print(f'✅ {name}: загружен успешно')
            except Exception as e:
                print(f'❌ {name}: ошибка загрузки - {e}')
        else:
            print(f'❌ {name}: файл не найден - {path}')
    
    # Тест классификации
    if len(loaded) == 3:
        print('')
        print('🎯 Тест классификации:')
        test_texts = [
            'Не работает компьютер, черный экран',
            'Нужно установить программу автокад', 
            'Проблемы с интернетом в офисе'
        ]
        
        for text in test_texts:
            try:
                # Предобработка текста
                text_vector = loaded['vectorizer'].transform([text])
                # Предсказание
                prediction = loaded['classifier'].predict(text_vector)[0]
                confidence = max(loaded['classifier'].predict_proba(text_vector)[0])
                # Декодирование категории
                category = loaded['encoder'].inverse_transform([prediction])[0]
                
                print(f'   Текст: \"{text}\"')
                print(f'   Категория: {category} (уверенность: {confidence:.2f})')
                print('')
            except Exception as e:
                print(f'   ❌ Ошибка классификации: {e}')
                break
    else:
        print('❌ Не все компоненты модели загружены, тест классификации невозможен')
        
except ImportError as e:
    print(f'❌ Ошибка импорта: {e}')
except Exception as e:
    print(f'❌ Общая ошибка: {e}')
" 2>/dev/null || echo "❌ Ошибка выполнения теста в контейнере"
    
else
    echo "❌ Контейнер $CONTAINER_NAME не запущен"
    echo "Запустите контейнер: make start"
fi

echo ""
echo "📊 Информация о ML модели:"
echo "-------------------------"

# Проверка метаданных модели (если есть)
if [ -f "$ML_DIR/model_metadata.json" ]; then
    echo "✅ Найден файл метаданных модели:"
    cat "$ML_DIR/model_metadata.json" | python -m json.tool 2>/dev/null || cat "$ML_DIR/model_metadata.json"
else
    echo "⚠️  Файл метаданных модели не найден"
    echo "Создайте model_metadata.json с информацией о модели:"
    echo '{
  "version": "1.0.0",
  "created_date": "'$(date -Iseconds)'",
  "model_type": "RandomForest",
  "accuracy": 0.85,
  "categories": ["Техника", "ПО", "Сеть", "Другое"]
}'
fi

echo ""
echo "🔧 Полезные команды:"
echo "--------------------"
echo "Просмотр логов ML в контейнере:"
echo "  make shell-bot"
echo "  tail -f /app/logs/ml.log"
echo ""
echo "Переобучение модели:"
echo "  python ml/training/train_model.py"
echo ""
echo "Обновление только бота с новой моделью:"
echo "  make update-bot"

echo ""
echo "=================================="
echo "✅ Проверка ML модели завершена"
