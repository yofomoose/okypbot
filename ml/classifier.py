"""
Классификатор заявок для Okdesk бота
Адаптированный из ML-бота для классификации заявок
"""

import asyncio
import logging
import pickle
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import re

# Для ML модели (будем устанавливать при необходимости)
try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    import joblib
except ImportError:
    # Заглушки если библиотеки не установлены
    np = None
    TfidfVectorizer = None
    LogisticRegression = None
    Pipeline = None
    joblib = None

logger = logging.getLogger(__name__)

class IssueClassifier:
    """Классификатор заявок по категориям"""
    
    def __init__(self, model_path: str = "ml/models/issue_classifier.pkl"):
        self.model_path = Path(model_path)
        self.model = None
        self.categories = []
        self.is_trained = False
        self.confidence_threshold = 0.6
        self.min_text_length = 10
        
        # Создаем директорию для моделей
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Базовые категории для начала
        self.default_categories = [
            "Техническая поддержка",
            "Проблемы с доступом", 
            "Ошибки в работе системы",
            "Запрос на изменение",
            "Консультация",
            "Жалоба",
            "Предложение",
            "Другое"
        ]
    
    async def initialize(self) -> bool:
        """Инициализация модели"""
        try:
            if self.model_path.exists():
                await self.load_model()
            else:
                logger.info("Модель не найдена, создаем базовую модель")
                await self.create_basic_model()
            return True
        except Exception as e:
            logger.error(f"Ошибка инициализации классификатора: {e}")
            return False
    
    async def load_model(self) -> bool:
        """Загрузка обученной модели"""
        try:
            if not joblib:
                logger.warning("scikit-learn не установлен, используем базовую классификацию")
                return False
                
            # Загружаем в отдельном потоке
            loop = asyncio.get_event_loop()
            model_data = await loop.run_in_executor(
                None, 
                joblib.load, 
                str(self.model_path)
            )
            
            self.model = model_data['model']
            self.categories = model_data['categories']
            self.is_trained = True
            
            logger.info(f"Модель загружена, доступно категорий: {len(self.categories)}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка загрузки модели: {e}")
            return False
    
    async def create_basic_model(self):
        """Создание базовой модели с примерами"""
        if not joblib:
            logger.warning("scikit-learn не установлен, классификация недоступна")
            self.categories = self.default_categories
            return
        
        # Базовые примеры для обучения
        training_data = [
            ("Не могу войти в систему", "Проблемы с доступом"),
            ("Забыл пароль", "Проблемы с доступом"),
            ("Система не отвечает", "Ошибки в работе системы"),
            ("Ошибка 500", "Ошибки в работе системы"),
            ("Нужна помощь с настройкой", "Техническая поддержка"),
            ("Как сделать отчет", "Консультация"),
            ("Предлагаю добавить функцию", "Предложение"),
            ("Недоволен работой", "Жалоба"),
            ("Изменить настройки", "Запрос на изменение"),
        ]
        
        texts = [item[0] for item in training_data]
        labels = [item[1] for item in training_data]
        
        # Создаем простую модель
        self.model = Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 2),
                stop_words=None  # Для русского языка можем добавить позже
            )),
            ('classifier', LogisticRegression(random_state=42))
        ])
        
        # Обучаем
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.model.fit, texts, labels)
        
        self.categories = list(set(labels))
        self.is_trained = True
        
        # Сохраняем
        await self.save_model()
        logger.info("Базовая модель создана и обучена")
    
    async def save_model(self):
        """Сохранение модели"""
        if not self.model or not joblib:
            return
            
        try:
            model_data = {
                'model': self.model,
                'categories': self.categories,
                'created_at': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                joblib.dump,
                model_data,
                str(self.model_path)
            )
            logger.info(f"Модель сохранена в {self.model_path}")
        except Exception as e:
            logger.error(f"Ошибка сохранения модели: {e}")
    
    async def classify(self, text: str) -> Tuple[str, float]:
        """
        Классификация текста заявки
        
        Returns:
            Tuple[str, float]: (категория, уверенность)
        """
        if not text or len(text.strip()) < self.min_text_length:
            return "Другое", 0.0
        
        # Предобработка текста
        processed_text = self._preprocess_text(text)
        
        if not self.is_trained or not self.model:
            # Базовая классификация по ключевым словам
            return self._basic_classify(processed_text)
        
        try:
            # ML классификация
            loop = asyncio.get_event_loop()
            
            # Предсказание
            prediction = await loop.run_in_executor(
                None,
                self.model.predict,
                [processed_text]
            )
            
            # Получаем вероятности
            probabilities = await loop.run_in_executor(
                None,
                self.model.predict_proba,
                [processed_text]
            )
            
            category = prediction[0]
            confidence = float(max(probabilities[0]))
            
            logger.info(f"Классификация: '{category}' с уверенностью {confidence:.2f}")
            return category, confidence
            
        except Exception as e:
            logger.error(f"Ошибка ML классификации: {e}")
            # Fallback на базовую классификацию
            return self._basic_classify(processed_text)
    
    def _preprocess_text(self, text: str) -> str:
        """Предобработка текста"""
        # Удаляем лишние пробелы и переводы строк
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Удаляем специальные символы (оставляем русские и английские буквы, цифры)
        text = re.sub(r'[^\w\s\-.,!?]', ' ', text)
        
        return text.lower()
    
    def _basic_classify(self, text: str) -> Tuple[str, float]:
        """Базовая классификация по ключевым словам"""
        keywords = {
            "Проблемы с доступом": [
                "пароль", "войти", "доступ", "авторизация", "логин", 
                "заблокирован", "не могу войти"
            ],
            "Ошибки в работе системы": [
                "ошибка", "не работает", "сломалось", "баг", "глюк",
                "500", "404", "ошибка сервера", "не отвечает"
            ],
            "Техническая поддержка": [
                "помощь", "поддержка", "как сделать", "инструкция",
                "настройка", "установка"
            ],
            "Консультация": [
                "как", "подскажите", "вопрос", "разъясните", "консультация"
            ],
            "Запрос на изменение": [
                "изменить", "поменять", "настроить", "добавить права",
                "удалить", "обновить"
            ],
            "Жалоба": [
                "жалоба", "недоволен", "плохо работает", "некачественно",
                "медленно", "не устраивает"
            ],
            "Предложение": [
                "предлагаю", "идея", "улучшение", "функция", "добавить"
            ]
        }
        
        text_lower = text.lower()
        scores = {}
        
        for category, words in keywords.items():
            score = 0
            for word in words:
                if word in text_lower:
                    score += 1
            
            if score > 0:
                scores[category] = score / len(words)
        
        if scores:
            best_category = max(scores.items(), key=lambda x: x[1])
            return best_category[0], min(best_category[1] * 0.7, 0.9)  # Максимум 0.9 для базовой
        
        return "Другое", 0.3
    
    async def add_training_example(self, text: str, category: str) -> bool:
        """Добавление примера для обучения"""
        try:
            # Сохраняем в файл для будущего переобучения
            training_file = self.model_path.parent / "training_data.json"
            
            # Загружаем существующие данные
            training_data = []
            if training_file.exists():
                with open(training_file, 'r', encoding='utf-8') as f:
                    training_data = json.load(f)
            
            # Добавляем новый пример
            training_data.append({
                'text': text,
                'category': category,
                'timestamp': datetime.now().isoformat(),
                'user_added': True
            })
            
            # Сохраняем
            with open(training_file, 'w', encoding='utf-8') as f:
                json.dump(training_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Добавлен пример обучения: '{category}'")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка добавления примера: {e}")
            return False
    
    async def retrain_model(self) -> bool:
        """Переобучение модели на новых данных"""
        if not joblib:
            logger.warning("scikit-learn не установлен")
            return False
            
        try:
            training_file = self.model_path.parent / "training_data.json"
            if not training_file.exists():
                logger.warning("Нет данных для переобучения")
                return False
            
            with open(training_file, 'r', encoding='utf-8') as f:
                training_data = json.load(f)
            
            if len(training_data) < 5:
                logger.warning("Недостаточно данных для переобучения")
                return False
            
            texts = [item['text'] for item in training_data]
            labels = [item['category'] for item in training_data]
            
            # Обучаем новую модель
            new_model = Pipeline([
                ('tfidf', TfidfVectorizer(
                    max_features=1000,
                    ngram_range=(1, 2)
                )),
                ('classifier', LogisticRegression(random_state=42))
            ])
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, new_model.fit, texts, labels)
            
            # Заменяем модель
            self.model = new_model
            self.categories = list(set(labels))
            self.is_trained = True
            
            # Сохраняем
            await self.save_model()
            
            logger.info(f"Модель переобучена на {len(training_data)} примерах")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка переобучения: {e}")
            return False
    
    def get_categories(self) -> List[str]:
        """Получить список доступных категорий"""
        return self.categories if self.categories else self.default_categories
    
    def get_stats(self) -> Dict[str, Any]:
        """Статистика классификатора"""
        return {
            'is_trained': self.is_trained,
            'categories_count': len(self.categories),
            'categories': self.categories,
            'model_exists': self.model is not None,
            'confidence_threshold': self.confidence_threshold,
            'ml_available': joblib is not None
        }
