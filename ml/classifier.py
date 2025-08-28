"""
Текстовый классификатор поверх bot_model.
"""

import logging
import asyncio
from typing import Tuple, List

import numpy as np

from .bot_model_adapter import BotModelAdapter
from .text_vectorizer import TextVectorizer

logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    """Простая нормализация текста."""
    if not text:
        return ""
    return text.strip()


class TextClassifier:
    """Классификатор, оборачивающий загрузку и инфо из bot_model."""

    def __init__(self):
        self.bot_model_adapter: BotModelAdapter | None = None
        self.vectorizer = TextVectorizer()

    async def initialize(self) -> bool:
        """Инициализация: загрузка bot_model (в отдельном потоке)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._initialize_bot_model)

    def _initialize_bot_model(self) -> bool:
        """Синхронная загрузка bot_model с диска."""
        try:
            logger.info("Инициализация bot_model...")
            self.bot_model_adapter = BotModelAdapter(model_dir="/app/bot_model")

            if not self.bot_model_adapter.load_model():
                logger.error("Не удалось загрузить файлы bot_model из /app/bot_model")
                return False

            logger.info("OK: bot_model успешно инициализирован")
            return True

        except Exception as e:
            logger.error(f"Ошибка при инициализации bot_model: {e}")
            self.bot_model_adapter = None
            return False

    async def classify(self, text: str) -> Tuple[str, float]:
        """Классифицировать один текст, вернуть (категория, уверенность)."""
        try:
            normalized = normalize_text(text)
            if not normalized:
                return "пустой_текст", 0.0

            if not self.bot_model_adapter or not self.bot_model_adapter.is_available():
                logger.error("bot_model не инициализирован")
                return "модель_недоступна", 0.0

            # Векторизация и вызов предсказания адаптера
            vec = self.vectorizer.vectorize(normalized)  # (384,)
            features = vec.reshape(1, -1) if isinstance(vec, np.ndarray) else np.asarray(vec, dtype=np.float32).reshape(1, -1)

            category, confidence = self.bot_model_adapter.predict(features)
            logger.info(f"bot_model: {category} ({confidence:.2%})")
            return category, confidence

        except Exception as e:
            logger.error(f"Ошибка классификации: {e}")
            return "ошибка_классификации", 0.0

    def get_stats(self) -> dict:
        """Собрать статистику по активной модели и bot_model."""
        bot_stats = self.bot_model_adapter.get_stats() if self.bot_model_adapter else {"model_loaded": False}
        is_available = self.bot_model_adapter.is_available() if self.bot_model_adapter else False
        return {
            "active_model": "bot_model" if is_available else "none",
            "bot_model": bot_stats,
        }

    async def classify_batch(self, texts: List[str]) -> List[Tuple[str, float]]:
        """Классификация батча текстов по одному."""
        results: List[Tuple[str, float]] = []
        for text in texts:
            result = await self.classify(text)
            results.append(result)
        return results

    # API, ожидаемый MLService/обработчиками
    def get_categories(self) -> List[str]:
        return self.bot_model_adapter.get_categories() if self.bot_model_adapter else []

    def enable_lgb_model(self) -> bool:
        # В текущей реализации только bot_model
        return False

    def disable_lgb_model(self) -> bool:
        # В текущей реализации только bot_model
        return True

    async def add_training_example(self, text: str, correct_category: str) -> bool:
        # Заглушка: онлайн-додобучение не реализовано для bot_model
        return False

    async def retrain_model(self) -> bool:
        # Заглушка: переобучение не реализовано на лету
        return False

