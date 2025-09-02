"""
Текстовый классификатор поверх bot_model.
"""

import logging
import asyncio
from typing import Tuple, List
from datetime import datetime

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
        self._user_corrections = 0  # Счетчик исправлений пользователя
        self._correction_threshold = 10  # Порог для отключения LightGBM

    async def initialize(self) -> bool:
        """Инициализация: загрузка bot_model (в отдельном потоке)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._initialize_bot_model)

    def _initialize_bot_model(self) -> bool:
        """Синхронная загрузка bot_model с диска."""
        try:
            logger.info("Инициализация bot_model...")
            # Используем относительный путь или переменную окружения
            import os
            model_dir = os.getenv("BOT_MODEL_DIR", "bot_model")
            self.bot_model_adapter = BotModelAdapter(model_dir=model_dir)

            if not self.bot_model_adapter.load_model():
                logger.error(f"Не удалось загрузить файлы bot_model из {model_dir}")
                return False

            # Инициализируем векторизатор
            if not self.vectorizer.load_model():
                logger.error("Не удалось загрузить модель векторизации")
                return False

            logger.info("OK: bot_model и векторизатор успешно инициализированы")
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
        """
        Добавляет новый обучающий пример
        
        Args:
            text: Текст заявки
            correct_category: Правильная категория
            
        Returns:
            bool: True если пример успешно добавлен
        """
        try:
            import os
            import json
            import pickle
            from pathlib import Path
            
            # Нормализуем текст
            normalized_text = normalize_text(text)
            if not normalized_text:
                logger.warning("Отклонен пустой обучающий пример")
                return False
                
            # Проверяем категорию на допустимость
            if not self.bot_model_adapter:
                logger.error("bot_model не инициализирован")
                return False
                
            categories = self.get_categories()
            if not categories or correct_category not in categories:
                logger.warning(f"Недопустимая категория: {correct_category}")
                return False
            
            # Векторизуем текст
            vec = self.vectorizer.vectorize(normalized_text)
            
            # Создаем новый обучающий пример
            example = {
                "text": normalized_text,
                "category": correct_category,
                "embedding": vec
            }
            
            # Загружаем существующие примеры
            examples_path = Path("bot_model/training_examples.pkl")
            examples = []
            
            if examples_path.exists():
                try:
                    with open(examples_path, 'rb') as f:
                        examples = pickle.load(f)
                    logger.info(f"Загружено {len(examples)} существующих примеров")
                except Exception as e:
                    logger.error(f"Ошибка загрузки примеров: {e}")
                    examples = []
            
            # Добавляем новый пример
            examples.append(example)
            
            # Сохраняем обновленные примеры
            try:
                # Убеждаемся, что директория существует и доступна для записи
                examples_path.parent.mkdir(exist_ok=True)
                
                # Проверяем права доступа и пытаемся сохранить
                with open(examples_path, 'wb') as f:
                    pickle.dump(examples, f)
                logger.info(f"Сохранен новый обучающий пример (всего {len(examples)})")
                return True
            except PermissionError as e:
                logger.error(f"Нет прав доступа для записи в {examples_path}: {e}")
                # Попробуем сохранить во временную директорию
                try:
                    import tempfile
                    temp_dir = Path(tempfile.gettempdir()) / "okypbot_examples"
                    temp_dir.mkdir(exist_ok=True)
                    temp_path = temp_dir / "training_examples.pkl"
                    with open(temp_path, 'wb') as f:
                        pickle.dump(examples, f)
                    logger.warning(f"Сохранено во временную директорию: {temp_path}")
                    return True
                except Exception as temp_e:
                    logger.error(f"Не удалось сохранить даже во временную директорию: {temp_e}")
                    return False
            except Exception as e:
                logger.error(f"Ошибка сохранения примеров: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка добавления обучающего примера: {e}")
            return False

    async def retrain_model(self) -> bool:
        """
        Переобучает модель на основе всех доступных примеров
        
        Returns:
            bool: True если модель успешно переобучена
        """
        try:
            import pickle
            import numpy as np
            from pathlib import Path
            from sklearn.neighbors import KNeighborsClassifier
            from sklearn.preprocessing import LabelEncoder
            import json
            from datetime import datetime
            
            logger.info("Начало переобучения модели")
            
            # Загружаем обучающие примеры
            examples_path = Path("bot_model/training_examples.pkl")
            if not examples_path.exists():
                logger.error("Файл с обучающими примерами не найден")
                return False
                
            try:
                with open(examples_path, 'rb') as f:
                    examples = pickle.load(f)
                logger.info(f"Загружено {len(examples)} обучающих примеров")
            except Exception as e:
                logger.error(f"Ошибка загрузки обучающих примеров: {e}")
                return False
                
            if not examples:
                logger.error("Нет обучающих примеров для обучения модели")
                return False
                
            # Подготовка данных
            texts = [ex["text"] for ex in examples]
            categories = [ex["category"] for ex in examples]
            embeddings = np.array([ex["embedding"] for ex in examples])
            
            # Кодирование категорий
            label_encoder = LabelEncoder()
            y = label_encoder.fit_transform(categories)
            
            # Обучение модели
            logger.info("Обучение KNeighborsClassifier...")
            n_neighbors = min(5, len(examples))
            classifier = KNeighborsClassifier(n_neighbors=n_neighbors, weights='distance')
            classifier.fit(embeddings, y)
            
            # Сохранение модели
            model_dir = Path("bot_model")
            model_dir.mkdir(exist_ok=True)
            
            # Сохраняем классификатор
            classifier_path = model_dir / "classifier.pkl"
            with open(classifier_path, 'wb') as f:
                pickle.dump(classifier, f)
            
            # Сохраняем энкодер
            encoder_path = model_dir / "label_encoder.pkl"
            with open(encoder_path, 'wb') as f:
                pickle.dump(label_encoder, f)
            
            # Обновляем метаданные
            metadata_path = model_dir / "model_metadata.json"
            metadata = {
                "model_type": "KNeighborsClassifier",
                "feature_count": embeddings.shape[1],
                "training_samples": len(examples),
                "n_neighbors": n_neighbors,
                "classes": list(label_encoder.classes_),
                "categories_count": len(label_encoder.classes_),
                "retrained_date": datetime.now().isoformat(),
                "update_strategy": "incremental",
                "vectorizer_model": self.vectorizer.model_name if hasattr(self.vectorizer, 'model_name') else None
            }
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
                
            logger.info(f"✅ Модель успешно переобучена на {len(examples)} примерах")
            
            # Перезагружаем модель
            if self.bot_model_adapter:
                self.bot_model_adapter.load_model()
                
            return True
            
        except Exception as e:
            logger.error(f"Ошибка переобучения модели: {e}")
            return False

    def clear_cache(self) -> int:
        """Очищает кеш предсказаний"""
        if self.bot_model_adapter:
            return self.bot_model_adapter.clear_cache()
        return 0
        
    async def train(self, text: str, category: str, user_id: int = 0) -> bool:
        """
        Обучение на примере (API для ModelTrainer)
        
        Args:
            text: Текст заявки
            category: Категория
            user_id: ID пользователя, добавившего пример
            
        Returns:
            bool: True если успешно
        """
        return await self.add_training_example(text, category)
        
    async def save_model(self) -> bool:
        """
        Сохранение модели (API для ModelTrainer)
        
        Returns:
            bool: True если успешно
        """
        return await self.retrain_model()
        
    async def get_examples_count(self) -> int:
        """
        Получить количество примеров (API для ModelTrainer)
        
        Returns:
            int: Количество примеров
        """
        try:
            import json
            from pathlib import Path
            
            examples_count = 0
            data_dir = Path("ml/data")
            
            if data_dir.exists():
                for file_path in data_dir.glob("*.json"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                examples_count += len(data)
                    except Exception:
                        pass
                        
            return examples_count
        except Exception:
            return 0

