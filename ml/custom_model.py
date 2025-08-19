"""
Адаптер для интеграции пользовательской обученной модели
"""

import asyncio
import logging
import pickle
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class CustomModelAdapter:
    """Адаптер для пользовательской ML модели"""
    
    def __init__(self, model_path: str = "ml/trained/"):
        self.model_path = Path(model_path)
        self.model = None
        self.vectorizer = None
        self.categories = []
        self.label_encoder = None
        self.is_loaded = False
        
        # Создаем директорию если не существует
        self.model_path.mkdir(parents=True, exist_ok=True)
        
    async def load_user_model(self, model_files: Dict[str, str]) -> bool:
        """
        Загрузка пользовательской модели
        
        Args:
            model_files: Словарь с путями к файлам модели
                - 'model': путь к основной модели
                - 'vectorizer': путь к векторизатору (опционально)
                - 'categories': путь к категориям/лейблам
                - 'encoder': путь к энкодеру лейблов (опционально)
        """
        try:
            logger.info("Загружаем пользовательскую модель...")
            
            # Загружаем основную модель
            if 'model' in model_files:
                model_file = Path(model_files['model'])
                if model_file.exists():
                    with open(model_file, 'rb') as f:
                        self.model = pickle.load(f)
                    logger.info(f"Модель загружена из {model_file}")
                else:
                    logger.error(f"Файл модели не найден: {model_file}")
                    return False
            
            # Загружаем векторизатор
            if 'vectorizer' in model_files:
                vectorizer_file = Path(model_files['vectorizer'])
                if vectorizer_file.exists():
                    with open(vectorizer_file, 'rb') as f:
                        self.vectorizer = pickle.load(f)
                    logger.info(f"Векторизатор загружен из {vectorizer_file}")
            
            # Загружаем категории
            if 'categories' in model_files:
                categories_file = Path(model_files['categories'])
                if categories_file.exists():
                    if categories_file.suffix == '.json':
                        with open(categories_file, 'r', encoding='utf-8') as f:
                            self.categories = json.load(f)
                    else:
                        with open(categories_file, 'rb') as f:
                            self.categories = pickle.load(f)
                    logger.info(f"Категории загружены: {len(self.categories)} шт.")
            
            # Загружаем энкодер лейблов
            if 'encoder' in model_files:
                encoder_file = Path(model_files['encoder'])
                if encoder_file.exists():
                    with open(encoder_file, 'rb') as f:
                        self.label_encoder = pickle.load(f)
                    logger.info(f"Энкодер лейблов загружен из {encoder_file}")
            
            self.is_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Ошибка загрузки пользовательской модели: {e}")
            return False
    
    async def predict(self, text: str) -> Tuple[str, float]:
        """Предсказание категории для текста"""
        if not self.is_loaded or not self.model:
            return "Другое", 0.0
        
        try:
            # Предобработка текста
            processed_text = self._preprocess_text(text)
            
            # Векторизация если есть векторизатор
            if self.vectorizer:
                text_vector = self.vectorizer.transform([processed_text])
            else:
                # Если векторизатор встроен в модель или не нужен
                text_vector = [processed_text]
            
            # Предсказание
            loop = asyncio.get_event_loop()
            
            if hasattr(self.model, 'predict_proba'):
                # Модель поддерживает вероятности
                prediction = await loop.run_in_executor(
                    None, self.model.predict, text_vector
                )
                probabilities = await loop.run_in_executor(
                    None, self.model.predict_proba, text_vector
                )
                
                predicted_class = prediction[0]
                confidence = float(max(probabilities[0]))
                
            else:
                # Модель без вероятностей
                prediction = await loop.run_in_executor(
                    None, self.model.predict, text_vector
                )
                predicted_class = prediction[0]
                confidence = 0.8  # Фиксированная уверенность
            
            # Декодируем категорию если есть энкодер
            if self.label_encoder:
                category = self.label_encoder.inverse_transform([predicted_class])[0]
            else:
                category = str(predicted_class)
            
            # Проверяем что категория в списке известных
            if category not in self.categories and self.categories:
                if isinstance(predicted_class, (int, float)) and predicted_class < len(self.categories):
                    category = self.categories[int(predicted_class)]
                else:
                    category = "Другое"
                    confidence = 0.3
            
            logger.info(f"Предсказание: {category} (уверенность: {confidence:.2f})")
            return category, confidence
            
        except Exception as e:
            logger.error(f"Ошибка предсказания: {e}")
            return "Другое", 0.0
    
    def _preprocess_text(self, text: str) -> str:
        """Предобработка текста (можно настроить под вашу модель)"""
        import re
        
        # Базовая предобработка
        text = text.lower()
        text = re.sub(r'\s+', ' ', text.strip())
        text = re.sub(r'[^\w\s\-.,!?]', ' ', text)
        
        return text
    
    def get_model_info(self) -> Dict[str, Any]:
        """Информация о загруженной модели"""
        return {
            'is_loaded': self.is_loaded,
            'has_model': self.model is not None,
            'has_vectorizer': self.vectorizer is not None,
            'has_encoder': self.label_encoder is not None,
            'categories_count': len(self.categories),
            'categories': self.categories[:10] if self.categories else [],  # Показываем первые 10
            'model_type': type(self.model).__name__ if self.model else None
        }

# Глобальный экземпляр адаптера
custom_model = CustomModelAdapter()
