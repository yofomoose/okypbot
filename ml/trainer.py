from typing import List, Dict, Any, Optional
import logging
import asyncio
from datetime import datetime
from pathlib import Path
import json
try:
    from config.db_config import SessionLocal, get_session
except ImportError:
    # Заглушки для случая, когда БД компоненты недоступны
    SessionLocal = None
    get_session = None
from config.categories import CATEGORIES, CATEGORY_GROUPS
from ml.classifier import TextClassifier
from utils.stats_tracker import StatsTracker

logger = logging.getLogger(__name__)

class ModelTrainer:
    def __init__(self):
        self.classifier = TextClassifier()
        self.stats = StatsTracker()
        self.valid_categories = set(CATEGORIES)

    async def train_on_example(self, text: str, category: str, user_id: Optional[int] = None) -> bool:
        """Обучение на одном примере"""
        try:
            # Проверяем категорию на допустимость
            if category not in self.valid_categories:
                logger.warning(f"Недопустимая категория: {category}")
                return False

            return await self.classifier.train(text, category, user_id or 0)

        except Exception as e:
            logger.error(f"Ошибка обучения на примере: {e}")
            return False

    async def update_model(self) -> bool:
        """Обновление модели"""
        try:
            await self.classifier.save_model()
            return True
        except Exception as e:
            logger.error(f"Ошибка обновления модели: {e}")
            return False

    async def get_valid_categories(self) -> List[str]:
        """Получение списка валидных категорий"""
        return list(self.valid_categories)

    async def get_examples_count(self) -> int:
        """Получение количества примеров"""
        return await self.classifier.get_examples_count()
