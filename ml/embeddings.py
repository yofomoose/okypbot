from typing import List, Dict
import logging

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    # Создаем заглушки
    class SentenceTransformer:
        def __init__(self, model_name):
            self.model_name = model_name
        def encode(self, texts, **kwargs):
            # Простая заглушка - возвращаем случайные векторы
            if isinstance(texts, str):
                return [0.1] * 384  # 384-мерный вектор
            return [[0.1] * 384 for _ in texts]
    
    class np:
        @staticmethod
        def array(data):
            return data

# Константы для эмбеддингов
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
MAX_SEQUENCE_LENGTH = 512

logger = logging.getLogger(__name__)

class EmbeddingManager:
    def __init__(self):
        if HAS_SENTENCE_TRANSFORMERS:
            try:
                self.model = SentenceTransformer(EMBEDDING_MODEL)
                logger.info(f"Загружена модель эмбеддингов: {EMBEDDING_MODEL}")
            except Exception as e:
                logger.warning(f"Не удалось загрузить модель эмбеддингов: {e}")
                self.model = SentenceTransformer(EMBEDDING_MODEL)  # Заглушка
        else:
            logger.warning("sentence-transformers не установлен, используем заглушку")
            self.model = SentenceTransformer(EMBEDDING_MODEL)  # Заглушка
            
        self.cache: Dict[str, list] = {}
        
    def encode_text(self, text: str):
        """Получение эмбеддинга для одного текста"""
        if not text:
            if HAS_SENTENCE_TRANSFORMERS:
                return np.array([])
            else:
                return []
            
        if text in self.cache:
            return self.cache[text]
            
        try:
            if HAS_SENTENCE_TRANSFORMERS:
                embedding = self.model.encode(
                    text,
                    convert_to_tensor=False,
                    normalize_embeddings=True
                    # Убираем max_length - этот параметр не поддерживается
                )
            else:
                # Простая заглушка для эмбеддинга
                embedding = self.model.encode(text)
                
            self.cache[text] = embedding
            return embedding
            
        except Exception as e:
            logger.error(f"Ошибка кодирования текста: {e}")
            if HAS_SENTENCE_TRANSFORMERS:
                return np.array([])
            else:
                return []
            
    def encode_texts(self, texts: List[str]):
        """Получение эмбеддингов для списка текстов"""
        if not texts:
            if HAS_SENTENCE_TRANSFORMERS:
                return np.array([])
            else:
                return []
            
        try:
            if HAS_SENTENCE_TRANSFORMERS:
                embeddings = self.model.encode(
                    texts,
                    convert_to_tensor=False,
                    normalize_embeddings=True
                    # Убираем max_length - этот параметр не поддерживается
                )
            else:
                # Простая заглушка - возвращаем список эмбеддингов
                embeddings = self.model.encode(texts)
                
            # Кэшируем результаты
            for text, embedding in zip(texts, embeddings):
                self.cache[text] = embedding
                
            return embeddings
            
        except Exception as e:
            logger.error(f"Ошибка кодирования текстов: {e}")
            if HAS_SENTENCE_TRANSFORMERS:
                return np.array([])
            else:
                return []
    
    def get_embeddings(self, texts: List[str]):
        """Альтернативный метод для получения эмбеддингов (для совместимости)"""
        return self.encode_texts(texts)
