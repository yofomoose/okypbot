#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки проблем с ML моделью
"""
import logging
import os
import sys
import pickle
import numpy as np
import json
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_pickle_file(file_path):
    """Проверка файла pickle"""
    print(f"\n🔍 Проверка файла: {file_path}")
    try:
        file_size = os.path.getsize(file_path)
        print(f"📊 Размер файла: {file_size} байт")
        
        # Пробуем открыть файл в бинарном режиме
        with open(file_path, 'rb') as f:
            header = f.read(10)  # Читаем первые 10 байт для анализа
            print(f"🔤 Начало файла (hex): {header.hex()}")
        
        # Пробуем загрузить с помощью pickle
        try:
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
            print(f"✅ Файл успешно загружен через pickle")
            print(f"📋 Тип объекта: {type(data)}")
            
            # Дополнительная информация в зависимости от типа объекта
            if hasattr(data, 'classes_'):
                print(f"📚 Классы: {len(data.classes_)}")
                print(f"📝 Примеры классов: {data.classes_[:5]}")
            
            if hasattr(data, '_fit_X') and hasattr(data, '_y'):
                print(f"🧮 Обучающие примеры: {len(data._y)}")
                print(f"📐 Размерность признаков: {data._fit_X.shape}")
            
            return True
        except Exception as e:
            print(f"❌ Ошибка загрузки через pickle: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        return False

def check_json_file(file_path):
    """Проверка JSON файла"""
    print(f"\n🔍 Проверка файла: {file_path}")
    try:
        file_size = os.path.getsize(file_path)
        print(f"📊 Размер файла: {file_size} байт")
        
        # Пробуем открыть и прочитать JSON
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ JSON успешно загружен")
            print(f"🔑 Ключи верхнего уровня: {list(data.keys())}")
            
            # Проверяем полезные данные
            if 'model_type' in data:
                print(f"📊 Тип модели: {data['model_type']}")
                
            if 'feature_count' in data:
                print(f"📐 Количество признаков: {data['feature_count']}")
                
            if 'training_samples' in data:
                print(f"📚 Обучающие примеры: {data['training_samples']}")
                
            if 'classes' in data:
                print(f"📝 Классы: {len(data['classes'])}")
                print(f"📋 Примеры классов: {data['classes'][:5] if len(data['classes']) > 0 else 'Нет классов'}")
                
            return True
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка декодирования JSON: {e}")
            
            # Пробуем прочитать как бинарный файл
            with open(file_path, 'rb') as f:
                header = f.read(20)
                print(f"🔤 Начало файла (hex): {header.hex()}")
                
            return False
            
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        return False

def check_bot_model_integrity():
    """Проверка целостности всех компонентов модели"""
    model_dir = Path("bot_model")
    
    if not model_dir.exists():
        print(f"❌ Директория {model_dir} не существует")
        return False
        
    print(f"✅ Директория {model_dir} найдена")
    
    # Список необходимых файлов
    required_files = [
        model_dir / "classifier.pkl", 
        model_dir / "label_encoder.pkl",
        model_dir / "model_metadata.json"
    ]
    
    # Проверяем наличие файлов
    for file_path in required_files:
        if not file_path.exists():
            print(f"❌ Файл {file_path} не найден")
            return False
    
    print("✅ Все необходимые файлы найдены")
    
    # Проверяем каждый файл
    check_pickle_file(model_dir / "classifier.pkl")
    check_pickle_file(model_dir / "label_encoder.pkl")
    check_json_file(model_dir / "model_metadata.json")
    
    if Path(model_dir / "training_examples.pkl").exists():
        check_pickle_file(model_dir / "training_examples.pkl")
    
    return True

def test_text_vectorizer():
    """Тестирование векторизатора текста"""
    print("\n🧪 Тестирование векторизатора текста")
    try:
        from ml.text_vectorizer import TextVectorizer
        
        vectorizer = TextVectorizer()
        loaded = vectorizer.load_model()
        
        print(f"✅ Векторизатор создан, загружен: {loaded}")
        
        # Тестовые тексты
        test_texts = [
            "Компьютер не включается, горит красная лампочка",
            "Принтер печатает полосами, нужна диагностика"
        ]
        
        for text in test_texts:
            vector = vectorizer.vectorize(text)
            print(f"📏 Векторизация текста: {text[:30]}...")
            print(f"   Размер вектора: {vector.shape}, тип: {vector.dtype}")
            print(f"   L2 норма вектора: {np.linalg.norm(vector):.4f}")
            
        return True
            
    except Exception as e:
        print(f"❌ Ошибка тестирования векторизатора: {e}")
        return False

def test_bot_model_adapter():
    """Тестирование адаптера модели"""
    print("\n🧪 Тестирование BotModelAdapter")
    try:
        from ml.bot_model_adapter import BotModelAdapter
        
        adapter = BotModelAdapter()
        loaded = adapter.load_model()
        
        print(f"✅ Адаптер создан, загружен: {loaded}")
        
        if loaded:
            # Получаем статистику
            stats = adapter.get_stats()
            print(f"📊 Статистика адаптера: {stats}")
            
            # Тестовый вектор
            test_vector = np.random.random(384).reshape(1, -384)
            
            try:
                category, confidence = adapter.predict(test_vector)
                print(f"🎯 Тестовое предсказание: {category}, уверенность: {confidence:.3f}")
            except Exception as e:
                print(f"❌ Ошибка предсказания: {e}")
            
            # Категории
            categories = adapter.get_categories()
            print(f"📑 Всего категорий: {len(categories)}")
            print(f"📋 Примеры категорий: {categories[:5] if len(categories) > 0 else 'Нет категорий'}")
            
        return loaded
            
    except Exception as e:
        print(f"❌ Ошибка тестирования адаптера: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Проверка проблем с ML моделью")
    print("=" * 50)
    
    # Проверка целостности модели
    check_bot_model_integrity()
    
    # Тестирование векторизатора
    test_text_vectorizer()
    
    # Тестирование адаптера
    test_bot_model_adapter()
