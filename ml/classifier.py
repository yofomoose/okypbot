from typing import Dict, List, Tuple, Optional, Union, Any
import numpy as np
from pathlib import Path
import pickle
import logging
import tempfile
import shutil
import os
import re
import hashlib
from datetime import datetime, timedelta
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.exceptions import NotFittedError

def normalize_text(text: str) -> str:
    """Нормализует текст для стабильной классификации"""
    if not text:
        return ""
    
    # Удаляем лишние пробелы и переводы строк
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Удаляем многоточия в конце и начале
    text = re.sub(r'\.{2,}', '', text)
    
    # Удаляем специальные символы в конце текста (например, обрезку "...")
    text = re.sub(r'[\.]{2,}$', '', text)
    text = re.sub(r'…+', '', text)
    
    # Убираем обрезанные слова в конце (заканчивающиеся не на полную букву)
    # Например: "красная ла..." → "красная"
    words = text.split()
    if words and len(words[-1]) < 3 and not words[-1].isdigit():
        words = words[:-1]
    
    text = ' '.join(words).strip()
    
    # Приводим к нижнему регистру для нормализации
    text = text.lower()
    
    return text

def get_text_hash(text: str) -> str:
    """Создает хеш для текста для кеширования"""
    normalized = normalize_text(text)
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()

# Временные константы для ML
CATEGORIES = {
    "Техника": ["Компьютеры", "Принтеры", "Сеть"],
    "Программы": ["ОС", "Приложения", "Драйверы"],
    "Прочее": ["Консультация", "Прочее"]
}
MODEL_PATH = "ml/models"
CONFIDENCE_THRESHOLD = 0.5
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
MIN_TEXT_LENGTH = 3

from ml.embeddings import EmbeddingManager

logger = logging.getLogger(__name__)

# Заглушка для DataEncryption
class DataEncryption:
    @staticmethod
    def encrypt(data):
        return data
    
    @staticmethod
    def decrypt(data):
        return data



logger = logging.getLogger(__name__)

class TextClassifier:
    def __init__(self):
        self.embedder = EmbeddingManager()
        self.classifier = KNeighborsClassifier(n_neighbors=5)
        self.examples = []
        self.label_encoder = LabelEncoder()
        
        # Кеш для результатов классификации
        self.classification_cache = {}
        self.cache_max_size = 1000  # Максимальный размер кеша
        
        # Счетчик пользовательских исправлений
        self.user_corrections_count = 0
        self._user_corrections = 0  # Добавляем недостающий атрибут
        self._correction_threshold = 1  # Порог для отключения LightGBM
        self.lgb_disabled_by_corrections = False
        self.max_corrections_before_disable = 1  # Отключаем LightGBM после первого же исправления
        self.use_lightgbm = True  # Флаг использования LightGBM
        
        # Интеграция с LightGBM моделью
        self.lgb_adapter = None
        self._initialize_advanced_model()
        
        self.load_examples()
        self.last_save = datetime.now()
        self.save_interval = timedelta(minutes=5)  # Сохраняем каждые 5 минут
        self.backup_dir = Path(MODEL_PATH) / "backups"
        self.backup_dir.mkdir(exist_ok=True)
    
    def _initialize_advanced_model(self):
        """Инициализирует продвинутую LightGBM модель"""
        try:
            from .advanced_custom_model import AdvancedCustomModelAdapter
            
            self.lgb_adapter = AdvancedCustomModelAdapter()
            models_path = "ml/models"
            
            if self.lgb_adapter.load_user_model(models_path):
                logger.info("LightGBM модель успешно интегрирована")
                
                # Получаем информацию о модели
                model_info = self.lgb_adapter.get_model_info()
                logger.info(f"LightGBM модель: {model_info}")
                
            else:
                logger.info("LightGBM модель не найдена, используем базовую реализацию")
                self.lgb_adapter = None
                
        except Exception as e:
            logger.warning(f"Не удалось загрузить LightGBM модель: {e}")
            self.lgb_adapter = None

    async def initialize(self) -> bool:
        """Асинхронная инициализация классификатора"""
        try:
            logger.info("Инициализация TextClassifier...")
            # Загружаем примеры
            self.load_examples()
            
            # Пробуем инициализировать LightGBM модель
            self._initialize_advanced_model()
            
            # Проверяем состояние
            if self.lgb_adapter and self.lgb_adapter.model:
                logger.info("Классификатор инициализирован с LightGBM моделью")
                return True
            elif self.examples:
                logger.info("Классификатор инициализирован с базовой моделью")
                return True
            else:
                logger.warning("Классификатор инициализирован в минимальном режиме")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка инициализации классификатора: {e}")
            return False

    def get_stats(self) -> dict:
        """Получить статистику модели"""
        stats = {
            "examples_count": len(self.examples),
            "has_lgb_model": self.lgb_adapter is not None and hasattr(self.lgb_adapter, 'model') and self.lgb_adapter.model is not None,
            "model_type": "LightGBM" if self.lgb_adapter and hasattr(self.lgb_adapter, 'model') and self.lgb_adapter.model else "KNN"
        }
        
        if self.lgb_adapter:
            model_info = self.lgb_adapter.get_model_info()
            stats.update(model_info)
            
        return stats

    def load_examples(self):
        examples_file = Path(MODEL_PATH) / 'examples.pkl'
        if examples_file.exists():
            with open(examples_file, 'rb') as f:
                self.examples = pickle.load(f)
                logger.info(f"Загружено {len(self.examples)} обучающих примеров")

    def encode_text(self, text: str) -> np.ndarray:
        """Получение эмбеддинга для одного текста"""
        if not text:
            return np.array([])
        return self.embedder.encode_text(text)
    
    def encode_texts(self, texts: List[str]) -> np.ndarray:
        """Получение эмбеддингов для списка текстов"""
        if not texts:
            return np.array([])
        return self.embedder.encode_texts(texts)

    async def train(self, texts: list, labels: list) -> None:
        """Обучение модели на наборе текстов и меток"""
        logger.info("Начало обучения модели...")
        try:
            # Получаем эмбеддинги для всех текстов
            X = self.encode_texts(texts)
            
            # Кодируем метки
            unique_labels = sorted(set(labels))
            self.label_encoder = {label: i for i, label in enumerate(unique_labels)}
            y = np.array([self.label_encoder[label] for label in labels])
            
            # Обучаем классификатор
            self.classifier.fit(X, y)
            
            # Сохраняем модель
            await self.save_model()
            logger.info("Модель успешно обучена и сохранена")
            
        except Exception as e:
            logger.error(f"Ошибка при обучении модели: {e}")
            raise

    async def classify(self, text: str) -> tuple[str, float]:
        """Классификация текста с интеграцией LightGBM модели и кешированием"""
        try:
            if not text or len(text) < MIN_TEXT_LENGTH:
                return "Текст слишком короткий", 0.0
            
            # Нормализуем текст
            normalized_text = normalize_text(text)
            text_hash = get_text_hash(text)
            
            # Добавляем отладочное логирование
            logger.info(f"Оригинальный текст: '{text[:100]}'")
            logger.info(f"Нормализованный текст: '{normalized_text[:100]}'")
            logger.info(f"Хеш текста: {text_hash}")
            
            # Проверяем кеш
            if text_hash in self.classification_cache:
                cached_result = self.classification_cache[text_hash]
                logger.info(f"✅ Используем кешированный результат: {cached_result[0]} ({cached_result[1]:.3f})")
                return cached_result
            
            # Логируем информацию о доступных моделях
            has_lgb = hasattr(self, 'lgb_adapter') and self.lgb_adapter and self.lgb_adapter.model_loaded
            lgb_status = "отключена" if self.lgb_disabled_by_corrections else "активна"
            logger.info(f"Классифицируем текст (LightGBM: {has_lgb and not self.lgb_disabled_by_corrections} ({lgb_status}), KNN примеров: {len(self.examples)}, исправлений: {self.user_corrections_count}): {text[:50]}...")
            
            result = None
            
            # Пытаемся использовать продвинутую LightGBM модель если доступна и не отключена
            if has_lgb and not self.lgb_disabled_by_corrections:
                try:
                    lgb_result = self.lgb_adapter.predict(normalized_text)
                    if lgb_result:
                        category, confidence = lgb_result
                        logger.info(f"LightGBM предсказание: {category} ({confidence:.3f})")
                        result = (category, confidence)
                except Exception as e:
                    logger.warning(f"Ошибка в LightGBM предсказании: {e}")
                    
            # Если LightGBM отключена или дала плохой результат, используем KNN
            if not result:
                if self.examples:
                    logger.info("Используем KNN классификатор")
                    # Получаем эмбеддинг текста
                    embedding = self.encode_text(normalized_text)
                    if embedding.size == 0:
                        result = ("Ошибка кодирования", 0.0)
                    else:
                        # Находим ближайшие примеры
                        embeddings = np.array([x['embedding'] for x in self.examples])
                        distances = np.linalg.norm(embeddings - embedding, axis=1)
                        
                        nearest_idx = np.argmin(distances)
                        confidence = float(1 / (1 + distances[nearest_idx]))
                        
                        result = (self.examples[nearest_idx]['category'], confidence)
                        logger.info(f"KNN предсказание: {result[0]} ({result[1]:.3f})")
                else:
                    result = ("Модель не обучена", 0.0)
            
            # Кешируем результат
            if result:
                self._cache_result(text_hash, result)
                return result
            else:
                fallback_result = ("Ошибка классификации", 0.0)
                self._cache_result(text_hash, fallback_result)
                return fallback_result
                
        except Exception as e:
            logger.error(f"Ошибка при классификации: {e}")
            return "Ошибка классификации", 0.0

    def _cache_result(self, text_hash: str, result: tuple) -> None:
        """Кеширует результат классификации"""
        # Если кеш переполнен, удаляем старые записи
        if len(self.classification_cache) >= self.cache_max_size:
            # Удаляем половину кеша (простая стратегия)
            keys_to_remove = list(self.classification_cache.keys())[:self.cache_max_size // 2]
            for key in keys_to_remove:
                del self.classification_cache[key]
            logger.info(f"Очищен кеш классификации, удалено {len(keys_to_remove)} записей")
        
        self.classification_cache[text_hash] = result

    async def get_valid_categories(self) -> List[str]:
        """Возвращает список валидных категорий"""
        # Используем тот же метод что и get_categories для консистентности
        return self.get_categories()

    def get_categories(self) -> List[str]:
        """Возвращает список доступных категорий для классификации"""
        # Если есть LightGBM модель, получаем категории из неё
        if hasattr(self, 'lgb_adapter') and self.lgb_adapter and hasattr(self.lgb_adapter, 'get_categories'):
            try:
                lgb_categories = self.lgb_adapter.get_categories()
                if lgb_categories:
                    return lgb_categories
            except Exception as e:
                logger.warning(f"Ошибка получения категорий из LightGBM: {e}")
        
        # Иначе возвращаем стандартные категории
        # Если CATEGORIES - это словарь, извлекаем все подкатегории
        if isinstance(CATEGORIES, dict):
            all_categories = []
            for main_cat, sub_cats in CATEGORIES.items():
                all_categories.append(main_cat)  # Добавляем основную категорию
                if isinstance(sub_cats, list):
                    all_categories.extend(sub_cats)  # Добавляем подкатегории
            return all_categories
        elif isinstance(CATEGORIES, list):
            return CATEGORIES
        else:
            return []

    async def get_examples_count(self) -> int:
        """Возвращает количество обучающих примеров"""
        return len(self.examples)

    async def save_model(self) -> bool:
        """Сохраняет модель и эмбеддинги"""
        try:
            # Создаем временную директорию, которая автоматически удалится после выхода из контекста
            with tempfile.TemporaryDirectory() as temp_dir:
                # Создаем пути к временным файлам
                temp_model = Path(temp_dir) / "model.pkl"
                temp_encoder = Path(temp_dir) / "label_encoder.pkl"
                
                # Сохраняем файлы во временную директорию
                with open(temp_model, 'wb') as f:
                    pickle.dump(self.classifier, f)
                with open(temp_encoder, 'wb') as f:
                    pickle.dump(self.label_encoder, f)
                
                # Создаем целевую директорию
                os.makedirs(MODEL_PATH, exist_ok=True)
                
                # Перемещаем файлы в целевую директорию
                shutil.copy2(temp_model, Path(MODEL_PATH) / 'classifier.pkl')
                shutil.copy2(temp_encoder, Path(MODEL_PATH) / 'label_encoder.pkl')
                
                return True
                
        except Exception as e:
            logger.error(f"Ошибка сохранения модели: {e}")
            return False

    async def load_model(self) -> bool:
        """Загружает модель"""
        try:
            model_file = Path(MODEL_PATH) / 'classifier.pkl'
            encoder_file = Path(MODEL_PATH) / 'label_encoder.pkl'
            
            if model_file.exists() and encoder_file.exists():
                with open(model_file, 'rb') as f:
                    self.classifier = pickle.load(f)
                with open(encoder_file, 'rb') as f:
                    self.label_encoder = pickle.load(f)
                return True
            return False
            
        except Exception as e:
            logger.error(f"Ошибка загрузки модели: {e}")
            return False

    async def train(self, text: str, category: str, user_id: int) -> bool:
        """Обучение на одном примере"""
        try:
            # Увеличиваем счетчик пользовательских исправлений
            self.user_corrections_count += 1
            logger.info(f"Пользовательское исправление #{self.user_corrections_count}: '{category}'")
            
            # Отключаем LightGBM после нескольких исправлений
            if self.user_corrections_count >= self.max_corrections_before_disable and not self.lgb_disabled_by_corrections:
                self.lgb_disabled_by_corrections = True
                logger.warning(f"🚫 LightGBM модель отключена после {self.user_corrections_count} исправлений. Переключаемся на KNN с пользовательскими данными.")
            
            # Проверка валидности категории
            valid_categories = self.get_categories()
            if category not in valid_categories:
                logger.warning(f"Неверная категория: {category}")
                return False
                
            # Проверка длины текста
            if len(text) < MIN_TEXT_LENGTH:
                logger.warning(f"Текст слишком короткий: {len(text)} символов")
                return False
                
            # Получаем эмбеддинг
            embedding = self.encode_text(text)
            if embedding.size == 0:
                logger.error("Ошибка получения эмбеддинга")
                return False
                
            # Создаем пример
            example = {
                'text': text,
                'category': category, 
                'embedding': embedding,
                'user_id': user_id,
                'created_at': datetime.utcnow()
            }
            
            # Добавляем в примеры
            self.examples.append(example)
            
            # Сохраняем примеры
            examples_file = Path(MODEL_PATH) / 'examples.pkl'
            with open(examples_file, 'wb') as f:
                pickle.dump(self.examples, f)
            
            # Переобучаем если достаточно примеров
            if len(self.examples) > 1:
                X = np.array([x['embedding'] for x in self.examples])
                y = np.array([x['category'] for x in self.examples])
                self.classifier.fit(X, y)
                
                # Сохраняем обновленную модель
                await self.save_model()
                
            # Очищаем все кеши, чтобы новые классификации учитывали добавленный пример
            cache_size_before = len(self.classification_cache)
            self.classification_cache.clear()
            
            # Также очищаем кеш LightGBM адаптера
            lgb_cache_size = 0
            if hasattr(self, 'lgb_adapter') and self.lgb_adapter and hasattr(self.lgb_adapter, 'clear_cache'):
                lgb_cache_size = self.lgb_adapter.clear_cache()
            
            logger.info(f"🗑️ Очищен кеш классификации ({cache_size_before} записей) и LightGBM ({lgb_cache_size} записей) после добавления нового примера")
                
            logger.info(f"Добавлен новый пример категории {category}")
            
            # Автосохранение после обучения
            await self.maybe_auto_save()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при обучении: {e}")
            return False

    async def add_training_example(self, text: str, category: str, user_id: int = 0) -> bool:
        """Добавляет обучающий пример (обёртка для метода train)
        
        Args:
            text: Текст для обучения
            category: Категория
            user_id: ID пользователя (опционально)
            
        Returns:
            bool: Успешность добавления
        """
        return await self.train(text, category, user_id)

    def enable_lgb_model(self) -> bool:
        """Включает LightGBM модель обратно"""
        try:
            if hasattr(self, 'lgb_adapter') and self.lgb_adapter and self.lgb_adapter.model:
                self.lgb_adapter.model_loaded = True
                logger.info("LightGBM модель включена обратно")
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка включения LightGBM модели: {e}")
            return False

    def disable_lgb_model(self) -> bool:
        """Отключает LightGBM модель для использования KNN"""
        try:
            if hasattr(self, 'lgb_adapter') and self.lgb_adapter:
                self.lgb_adapter.model_loaded = False
                logger.info("LightGBM модель отключена, используется KNN")
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка отключения LightGBM модели: {e}")
            return False

    async def classify_batch(self, texts: List[str]) -> List[Tuple[str, float]]:
        """Пакетная классификация текстов"""
        try:
            if not self.examples:
                return [("Нет обучающих примеров", 0.0)] * len(texts)
                
            results = []
            for text in texts:
                category, confidence = await self.classify(text)
                results.append((category, confidence))
                
            return results
            
        except Exception as e:
            logger.error(f"Ошибка пакетной классификации: {e}")
            return [("Ошибка", 0.0)] * len(texts)

    async def maybe_auto_save(self):
        """Автоматическое сохранение если прошло достаточно времени"""
        now = datetime.now()
        if now - self.last_save > self.save_interval:
            await self.save_model()
            await self.backup_model()
            self.last_save = now

    async def backup_model(self) -> bool:
        """Создает резервную копию модели и данных"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"backup_{timestamp}"
            backup_path.mkdir(exist_ok=True)

            # Копируем файлы модели
            shutil.copy2(Path(MODEL_PATH) / "classifier.pkl", backup_path / "classifier.pkl")
            shutil.copy2(Path(MODEL_PATH) / "examples.pkl", backup_path / "examples.pkl")
            
            # Удаляем старые бэкапы (оставляем последние 5)
            backups = sorted(self.backup_dir.glob("backup_*"))
            if len(backups) > 5:
                for old_backup in backups[:-5]:
                    shutil.rmtree(old_backup)
                    
            return True
        except Exception as e:
            logger.error(f"Ошибка создания бэкапа: {e}")
            return False

    def load_latest_backup(self) -> bool:
        """Загружает последний бэкап если основные файлы повреждены"""
        try:
            backups = sorted(self.backup_dir.glob("backup_*"))
            if not backups:
                return False

            latest_backup = backups[-1]
            shutil.copy2(latest_backup / "classifier.pkl", Path(MODEL_PATH) / "classifier.pkl")
            shutil.copy2(latest_backup / "examples.pkl", Path(MODEL_PATH) / "examples.pkl")
            return True
        except Exception as e:
            logger.error(f"Ошибка загрузки бэкапа: {e}")
            return False
