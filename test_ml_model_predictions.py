#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для тестирования предсказаний ML модели
"""

import os
import sys
import json
import logging
import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Добавляем текущую директорию в PYTHONPATH для импорта модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Импортируем модуль для работы с моделью
    from ml.bot_model_adapter import BotModelAdapter
except ImportError as e:
    logger.error(f"❌ Ошибка импорта: {e}")
    logger.error("❌ Убедитесь, что модули ML установлены правильно")
    sys.exit(1)

def get_test_examples() -> List[Dict[str, Any]]:
    """
    Возвращает тестовые примеры для проверки модели
    """
    # Сначала проверим, есть ли файл с примерами обучения
    examples_file = Path("ml/data/training_examples.json")
    if examples_file.exists():
        try:
            with open(examples_file, 'r', encoding='utf-8') as f:
                examples = json.load(f)
                
            if isinstance(examples, list) and examples:
                # Возьмем случайные 5 примеров для теста
                import random
                test_examples = random.sample(examples, min(5, len(examples)))
                return test_examples
        except Exception as e:
            logger.warning(f"⚠️ Не удалось загрузить примеры из {examples_file}: {e}")
    
    # Если примеров нет или не удалось загрузить, используем эти
    test_examples = [
        {
            "text": "Компьютер не включается, горит только красная лампочка",
            "category": "Оборудование" 
        },
        {
            "text": "Не могу войти в свой аккаунт 1С",
            "category": "1С: Доступы в базе"
        },
        {
            "text": "Необходимо настроить новый принтер в бухгалтерии",
            "category": "Оргтехника: Принтеры"
        },
        {
            "text": "Установите Microsoft Office на новый компьютер",
            "category": "Программное обеспечение: Установка"
        },
        {
            "text": "Интернет работает очень медленно",
            "category": "Сеть: Другое"
        }
    ]
    
    return test_examples

def get_custom_examples() -> List[Dict[str, str]]:
    """
    Возвращает пользовательские примеры для проверки модели
    """
    return [
        {"text": "Компьютер зависает при запуске Excel"},
        {"text": "Не работает интернет в переговорной"},
        {"text": "Нужно настроить VPN для удаленной работы"},
        {"text": "Помогите восстановить удаленный файл"},
        {"text": "База данных 1С выдает ошибку при открытии"}
    ]

def load_pickle_examples() -> Optional[List[Dict[str, Any]]]:
    """
    Загружает сохраненные примеры из pickle файла
    """
    pickle_file = Path("bot_model/training_examples.pkl")
    if not pickle_file.exists():
        logger.warning(f"⚠️ Файл {pickle_file} не существует")
        return None
    
    try:
        with open(pickle_file, 'rb') as f:
            examples = pickle.load(f)
            
        if not isinstance(examples, list) or not examples:
            logger.warning(f"⚠️ Некорректные данные в файле {pickle_file}")
            return None
            
        # Берем последние 5 примеров для теста
        return examples[-5:]
    except Exception as e:
        logger.error(f"❌ Ошибка при чтении файла {pickle_file}: {e}")
        return None

def test_model_predictions():
    """
    Тестирует предсказания модели на примерах
    """
    logger.info("🔍 Загрузка модели...")
    
    # Инициализируем адаптер модели
    bot_model = BotModelAdapter()
    
    try:
        # Загружаем модель явно
        if bot_model.load_model():
            logger.info("✅ Модель успешно загружена")
        else:
            logger.error("❌ Ошибка загрузки модели")
            return False
        
        # Получаем тестовые примеры из обучающих данных
        test_examples = get_test_examples()
        
        logger.info("\n=== Тестирование на примерах из обучающих данных ===")
        success_count = 0
        
        for i, example in enumerate(test_examples, 1):
            text = example.get('text', '')
            expected = example.get('category', 'Unknown')
            
            try:
                # Здесь нам нужно обработать текст, чтобы получить embedding
                from ml.text_vectorizer import TextVectorizer
                vectorizer = TextVectorizer()
                
                # Векторизируем текст
                embedding = vectorizer.vectorize(text)
                
                if embedding is None:
                    logger.warning(f"❌ Пример #{i}: не удалось получить вектор для: '{text[:50]}...'")
                    continue
                
                # Получаем предсказание
                prediction_result = bot_model.predict(embedding.reshape(1, -1))
                
                if isinstance(prediction_result, tuple) and len(prediction_result) == 2:
                    predicted, confidence = prediction_result
                    logger.info(f"✅ Получено предсказание: {predicted} ({confidence:.2f})")
                else:
                    logger.warning(f"❌ Неожиданный формат предсказания: {prediction_result}")
                    continue
            except Exception as e:
                logger.warning(f"❌ Ошибка при предсказании для примера #{i}: {e}")
                continue
            
            # Проверяем результат
            match = predicted == expected
            status = "✅" if match else "❌"
            
            logger.info(f"{status} Пример #{i}:")
            logger.info(f"   Текст: '{text[:50]}...'")
            logger.info(f"   Ожидаемая категория: {expected}")
            logger.info(f"   Предсказанная категория: {predicted} (уверенность: {confidence:.2f})")
            
            if match:
                success_count += 1
                
        accuracy = success_count / len(test_examples) if test_examples else 0
        logger.info(f"📊 Точность на примерах из обучающих данных: {accuracy:.2%} ({success_count}/{len(test_examples)})")
        
        # Тестируем на пользовательских примерах
        custom_examples = get_custom_examples()
        
        logger.info("\n=== Тестирование на пользовательских примерах ===")
        
        for i, example in enumerate(custom_examples, 1):
            text = example.get('text', '')
            
            try:
                # Векторизируем текст
                from ml.text_vectorizer import TextVectorizer
                vectorizer = TextVectorizer()
                embedding = vectorizer.vectorize(text)
                
                if embedding is None:
                    logger.warning(f"❌ Пример #{i}: не удалось получить вектор для: '{text}'")
                    continue
                
                # Получаем предсказание
                prediction_result = bot_model.predict(embedding.reshape(1, -1))
                
                if isinstance(prediction_result, tuple) and len(prediction_result) == 2:
                    category, confidence = prediction_result
                    logger.info(f"📊 Пример #{i}: '{text}'")
                    logger.info(f"   Предсказано: {category} (уверенность: {confidence:.2f})")
                else:
                    logger.warning(f"❌ Неожиданный формат предсказания: {prediction_result}")
            except Exception as e:
                logger.warning(f"❌ Ошибка при предсказании для примера #{i}: {e}")
                
        # Тестируем на примерах из pickle файла
        pickle_examples = load_pickle_examples()
        
        if pickle_examples:
            logger.info("\n=== Тестирование на примерах из pickle файла ===")
            
            for i, example in enumerate(pickle_examples, 1):
                text = example.get('text', '')
                expected = example.get('category', 'Unknown')
                embedding = example.get('embedding')
                
                if embedding is None:
                    logger.warning(f"❌ Пример #{i}: отсутствует embedding для: '{text[:50]}...'")
                    continue
                
                try:
                    # Получаем предсказание, используя уже готовый embedding
                    prediction_result = bot_model.predict(embedding.reshape(1, -1))
                    
                    if isinstance(prediction_result, tuple) and len(prediction_result) == 2:
                        predicted, confidence = prediction_result
                        
                        # Проверяем результат
                        match = predicted == expected
                        status = "✅" if match else "❌"
                        
                        logger.info(f"{status} Пример #{i}:")
                        logger.info(f"   Текст: '{text[:50]}...'")
                        logger.info(f"   Ожидаемая категория: {expected}")
                        logger.info(f"   Предсказанная категория: {predicted} (уверенность: {confidence:.2f})")
                    else:
                        logger.warning(f"❌ Неожиданный формат предсказания: {prediction_result}")
                except Exception as e:
                    logger.warning(f"❌ Ошибка при предсказании для примера #{i}: {e}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании модели: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("🔍 Начало тестирования ML модели...")
    
    # Запускаем функцию тестирования
    result = test_model_predictions()
    
    if result:
        logger.info("✅ Тестирование завершено успешно")
    else:
        logger.error("❌ Тестирование завершилось с ошибками")
