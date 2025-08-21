"""
Сервис векторизации текста для модели bot_model
"""

import numpy as np
import logging
from typing import Optional, List
from sentence_transformers import SentenceTransformer
import re

logger = logging.getLogger(__name__)

class TextVectorizer:
    """Векторизатор текста для модели bot_model"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.is_loaded = False
        
    def load_model(self) -> bool:
        """Загружает модель векторизации"""
        try:
            logger.info(f"Загрузка модели векторизации: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.is_loaded = True
            logger.info("✅ Модель векторизации загружена")
            return True
        except Exception as e:
            logger.error(f"Ошибка загрузки модели векторизации: {e}")
            self.is_loaded = False
            return False
    
    def preprocess_text(self, text: str) -> str:
        """Предобрабатывает текст перед векторизацией"""
        if not text:
            return ""
        
        # Удаляем лишние пробелы и переводы строк
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Удаляем многоточия и специальные символы
        text = re.sub(r'\.{2,}', '', text)
        text = re.sub(r'…+', '', text)
        
        # Ограничиваем длину текста (модели обычно имеют лимит)
        if len(text) > 512:
            text = text[:512]
        
        return text.strip()
    
    def vectorize(self, text: str) -> np.ndarray:
        """
        Векторизует текст в 384-мерный вектор
        
        Args:
            text: Входной текст
            
        Returns:
            np.ndarray: Вектор размерности (384,)
        """
        if not self.is_loaded:
            if not self.load_model():
                # Возвращаем случайный вектор как fallback
                logger.warning("Используется случайный вектор (модель не загружена)")
                return np.random.random(384).astype(np.float32)
        
        try:
            # Предобрабатываем текст
            processed_text = self.preprocess_text(text)
            
            if not processed_text:
                # Для пустого текста возвращаем нулевой вектор
                return np.zeros(384, dtype=np.float32)
            
            # Векторизуем
            embedding = self.model.encode([processed_text])
            vector = embedding[0].astype(np.float32)
            
            # Проверяем размерность
            if vector.shape[0] != 384:
                logger.warning(f"Неожиданная размерность вектора: {vector.shape[0]}, ожидается 384")
                # Подгоняем размерность
                if vector.shape[0] > 384:
                    vector = vector[:384]
                else:
                    # Дополняем нулями
                    padded = np.zeros(384, dtype=np.float32)
                    padded[:vector.shape[0]] = vector
                    vector = padded
            
            return vector
            
        except Exception as e:
            logger.error(f"Ошибка векторизации текста: {e}")
            # Возвращаем случайный вектор как fallback
            return np.random.random(384).astype(np.float32)
    
    def vectorize_batch(self, texts: List[str]) -> np.ndarray:
        """
        Векторизует несколько текстов
        
        Args:
            texts: Список текстов
            
        Returns:
            np.ndarray: Массив векторов размерности (len(texts), 384)
        """
        if not self.is_loaded:
            if not self.load_model():
                # Возвращаем случайные векторы как fallback
                logger.warning("Используются случайные векторы (модель не загружена)")
                return np.random.random((len(texts), 384)).astype(np.float32)
        
        try:
            # Предобрабатываем тексты
            processed_texts = [self.preprocess_text(text) for text in texts]
            
            # Векторизуем
            embeddings = self.model.encode(processed_texts)
            vectors = embeddings.astype(np.float32)
            
            # Проверяем размерность
            if vectors.shape[1] != 384:
                logger.warning(f"Неожиданная размерность векторов: {vectors.shape[1]}, ожидается 384")
                # Подгоняем размерность
                if vectors.shape[1] > 384:
                    vectors = vectors[:, :384]
                else:
                    # Дополняем нулями
                    padded = np.zeros((len(texts), 384), dtype=np.float32)
                    padded[:, :vectors.shape[1]] = vectors
                    vectors = padded
            
            return vectors
            
        except Exception as e:
            logger.error(f"Ошибка векторизации текстов: {e}")
            # Возвращаем случайные векторы как fallback
            return np.random.random((len(texts), 384)).astype(np.float32)
    
    def get_info(self) -> dict:
        """Возвращает информацию о векторизаторе"""
        return {
            "model_name": self.model_name,
            "is_loaded": self.is_loaded,
            "vector_dimension": 384,
            "max_text_length": 512
        }

# Глобальный экземпляр векторизатора
text_vectorizer = TextVectorizer()
