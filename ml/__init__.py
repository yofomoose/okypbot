"""
ML модуль для классификации заявок
Поддерживает множественные модели: bot_model, LightGBM, KNN fallback
"""

import logging

# Настройка логгера для модуля
logger = logging.getLogger(__name__)

# Основные компоненты (всегда доступны)
from .classifier import TextClassifier

# Попытка импорта продвинутой LightGBM модели
try:
    from .advanced_custom_model import AdvancedCustomModelAdapter
    LIGHTGBM_AVAILABLE = True
    logger.info("✅ LightGBM модель доступна")
except ImportError as e:
    logger.info(f"⚠️ LightGBM модель недоступна: {e}")
    LIGHTGBM_AVAILABLE = False
    
    # Заглушка для совместимости
    class AdvancedCustomModelAdapter:
        def __init__(self):
            self.available = False
        
        def load_user_model(self, path):
            return False
        
        def predict(self, text):
            return None

# Попытка импорта новой bot_model
try:
    from .bot_model_adapter import BotModelAdapter
    from .text_vectorizer import TextVectorizer, text_vectorizer
    BOT_MODEL_AVAILABLE = True
    logger.info("✅ bot_model доступна")
except ImportError as e:
    logger.info(f"⚠️ bot_model недоступна: {e}")
    BOT_MODEL_AVAILABLE = False
    
    # Заглушки для совместимости
    class BotModelAdapter:
        def __init__(self):
            self.available = False
        
        def is_available(self):
            return False
        
        def load_model(self):
            return False
    
    class TextVectorizer:
        def __init__(self):
            self.available = False
        
        def load_model(self):
            return False
        
        def vectorize(self, text):
            import numpy as np
            return np.zeros(384)
    
    text_vectorizer = TextVectorizer()

# Попытка импорта embeddings (fallback)
try:
    from .embeddings import EmbeddingManager
    EMBEDDINGS_AVAILABLE = True
    logger.info("✅ EmbeddingManager доступен")
except ImportError as e:
    logger.info(f"⚠️ EmbeddingManager недоступен: {e}")
    EMBEDDINGS_AVAILABLE = False
    
    # Заглушка для EmbeddingManager
    class EmbeddingManager:
        def __init__(self):
            self.available = False
        
        def encode_text(self, text):
            import numpy as np
            return np.random.random(384)
        
        def encode_texts(self, texts):
            import numpy as np
            return np.random.random((len(texts), 384))

# Совместимость с предыдущим именем
IssueClassifier = TextClassifier

# Базовый экспорт (всегда доступно)
__all__ = [
    'TextClassifier', 
    'IssueClassifier',
    'AdvancedCustomModelAdapter',
    'BOT_MODEL_AVAILABLE',
    'LIGHTGBM_AVAILABLE', 
    'EMBEDDINGS_AVAILABLE'
]

# Условный экспорт в зависимости от доступности
if BOT_MODEL_AVAILABLE:
    __all__.extend(['BotModelAdapter', 'TextVectorizer', 'text_vectorizer'])

if EMBEDDINGS_AVAILABLE:
    __all__.extend(['EmbeddingManager'])

# Функция для получения информации о доступных моделях
def get_available_models():
    """Возвращает информацию о доступных ML моделях"""
    models = {
        'bot_model': BOT_MODEL_AVAILABLE,
        'lightgbm': LIGHTGBM_AVAILABLE,
        'embeddings': EMBEDDINGS_AVAILABLE,
        'fallback_knn': True  # Всегда доступна
    }
    
    active_models = [name for name, available in models.items() if available]
    logger.info(f"Доступные модели: {', '.join(active_models)}")
    
    return models

# Функция для создания классификатора с лучшей доступной моделью
def create_classifier():
    """Создает экземпляр классификатора с лучшей доступной моделью"""
    try:
        classifier = TextClassifier()
        logger.info("✅ Классификатор успешно создан")
        return classifier
    except Exception as e:
        logger.error(f"❌ Ошибка создания классификатора: {e}")
        raise

# Добавляем утилитарные функции в экспорт
__all__.extend(['get_available_models', 'create_classifier'])

# Логируем статус при импорте модуля
logger.info("🚀 ML модуль инициализирован")
get_available_models()

# Версия модуля
__version__ = "2.0.0"