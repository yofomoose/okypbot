"""
Классификатор с приоритетом bot_model
"""

import logging
import asyncio
from datetime import datetime
from typing import Tuple, List, Optional
from pathlib import Path

from .bot_model_adapter import BotModelAdapter
from .text_vectorizer import TextVectorizer

logger = logging.getLogger(__name__)

def normalize_text(text: str) -> str:
    """Нормализует текст для классификации"""
    if not text:
        return ""
    return text.strip().lower()

class TextClassifier:
    """Классификатор текста с приоритетом bot_model"""
    
    def __init__(self):
        self.bot_model_adapter = None
        
    async def initialize(self) -> bool:
        """Асинхронная инициализация классификатора"""
        return await asyncio.get_event_loop().run_in_executor(None, self._initialize_bot_model)
        
    def _initialize_bot_model(self):
        """Инициализирует модель bot_model"""
        try:
            logger.info("Инициализация bot_model...")
            self.bot_model_adapter = BotModelAdapter(model_dir="/app/bot_model")
            
            if not self.bot_model_adapter.load_model():
                logger.error("❌ Не удалось загрузить bot_model из /app/bot_model")
                return False
                
            logger.info("✅ bot_model успешно инициализирована")
            return True
                
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации bot_model: {e}")
            self.bot_model_adapter = None
            return False
            
    async def classify(self, text: str) -> Tuple[str, float]:
        """Классифицирует текст, возвращает категорию и уверенность"""
        try:
            normalized = normalize_text(text)
            if not normalized:
                return "Пустой запрос", 0.0
                
            logger.info(f"Классифицируем текст: {text}")

            # Используем только bot_model для классификации
            if self.bot_model_adapter:
                try:
                    result = self.bot_model_adapter.predict(normalized)
                    if result:
                        category, confidence = result
                        logger.info(f"✅ Результат классификации bot_model: {category} ({confidence:.2%})")
                        return category, confidence
                    else:
                        logger.warning("❌ bot_model не смогла определить категорию")
                except Exception as e:
                    logger.error(f"❌ Ошибка при классификации bot_model: {e}")
            else:
                logger.error("❌ bot_model не инициализирована")
                
            return "Модель не обучена", 0.0
            
        except Exception as e:
            logger.error(f"❌ Ошибка классификации: {e}")
            return "Ошибка классификации", 0.0
            
    async def classify_batch(self, texts: List[str]) -> List[Tuple[str, float]]:
        """Классифицирует список текстов"""
        results = []
        for text in texts:
            result = await self.classify(text)
            results.append(result)
        return results
