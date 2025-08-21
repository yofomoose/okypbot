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
import json
from datetime import datetime, timedelta
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.exceptions import NotFittedError

# Настройка логгера
logger = logging.getLogger(__name__)

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
# Устаревшие категории - оставляем только для совместимости с fallback
FALLBACK_CATEGORIES = {
    "Техника": ["Компьютеры", "Принтеры", "Сеть"],
    "Программы": ["ОС", "Приложения", "Драйверы"],
    "Прочее": ["Консультация", "Прочее"]
}
MODEL_PATH = "ml/models"
CONFIDENCE_THRESHOLD = 0.5
MIN_TEXT_LENGTH = 3

# Импорты для новой модели
try:
    from ml.bot_model_adapter import BotModelAdapter
    from ml.text_vectorizer import text_vectorizer
    BOT_MODEL_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Модель bot_model недоступна: {e}")
    BOT_MODEL_AVAILABLE = False

logger = logging.getLogger(__name__)

# Импорты для старых компонентов (только если bot_model недоступна)  
try:
    from ml.embeddings import EmbeddingManager
    EMBEDDINGS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"EmbeddingManager недоступен: {e}")
    EMBEDDINGS_AVAILABLE = False
    
    # Заглушка для EmbeddingManager
    class EmbeddingManager:
        def encode_text(self, text):
            return np.random.random(384)
        def encode_texts(self, texts):
            return np.random.random((len(texts), 384))

class TextClassifier:
    def __init__(self):
        # Кеш для результатов классификации
        self.classification_cache = {}
        self.cache_max_size = 1000  # Максимальный размер кеша
        
        # Счетчик пользовательских исправлений
        self._user_corrections = 0
        self._correction_threshold = 1  # Порог для отключения LightGBM
        self.lgb_disabled_by_corrections = False
        self.use_lightgbm = True  # Флаг использования LightGBM
        
        # Приоритет: bot_model > LightGBM > старая KNN
        self.bot_model_adapter = None
        self.use_bot_model = True  # Приоритет bot_model
        self.lgb_adapter = None
        
        # Fallback компоненты (только если bot_model недоступна)
        self.embedder = EmbeddingManager() if EMBEDDINGS_AVAILABLE else None
        self.classifier = KNeighborsClassifier(n_neighbors=5)
        self.examples = []
        self.label_encoder = LabelEncoder()
        
        # Инициализация моделей
        self._initialize_bot_model()
        if not (self.bot_model_adapter and self.bot_model_adapter.is_available()):
            self._initialize_advanced_model()
            self.load_examples()
        
        # Настройки сохранения
        self.last_save = datetime.now()
        self.save_interval = timedelta(minutes=5)
        self.backup_dir = Path(MODEL_PATH) / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
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

    def _initialize_bot_model(self):
        """Инициализирует модель bot_model"""
        if not BOT_MODEL_AVAILABLE:
            logger.info("bot_model недоступна")
            return
            
        try:
            logger.info("Инициализация bot_model...")
            self.bot_model_adapter = BotModelAdapter()
            
            if self.bot_model_adapter.load_model():
                # Загружаем векторизатор
                if text_vectorizer.load_model():
                    logger.info("✅ bot_model успешно инициализирована")
                    info = self.bot_model_adapter.get_model_info()
                    logger.info(f"bot_model: {info}")
                else:
                    logger.warning("Векторизатор не загружен, bot_model недоступна")
                    self.bot_model_adapter = None
            else:
                logger.info("bot_model не найдена")
                self.bot_model_adapter = None
                
        except Exception as e:
            logger.warning(f"Не удалось загрузить bot_model: {e}")
            self.bot_model_adapter = None

    async def initialize(self) -> bool:
        """Асинхронная инициализация классификатора"""
        try:
            logger.info("Инициализация TextClassifier...")
            # Загружаем примеры
            self.load_examples()
            
            # Пробуем инициализировать bot_model (приоритет)
            self._initialize_bot_model()
            
            # Пробуем инициализировать LightGBM модель
            self._initialize_advanced_model()
            
            # Проверяем состояние
            if self.bot_model_adapter and self.bot_model_adapter.is_available():
                logger.info("✅ Классификатор инициализирован с bot_model")
                return True
            elif self.lgb_adapter and self.lgb_adapter.model:
                logger.info("✅ Классификатор инициализирован с LightGBM моделью")
                return True
            elif self.examples:
                logger.info("✅ Классификатор инициализирован с базовой моделью")
                return True
            else:
                logger.warning("⚠️ Классификатор инициализирован в минимальном режиме")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка инициализации классификатора: {e}")
            return False

    def get_stats(self) -> dict:
        """Получить статистику модели"""
        # Определяем активную модель
        active_model = "Unknown"
        if self.bot_model_adapter and self.bot_model_adapter.is_available():
            active_model = "bot_model"
        elif self.lgb_adapter is not None and hasattr(self.lgb_adapter, 'model') and self.lgb_adapter.model is not None:
            active_model = "LightGBM"
        elif self.examples:
            active_model = "KNN"
        
        stats = {
            "examples_count": len(self.examples),
            "has_bot_model": self.bot_model_adapter is not None and self.bot_model_adapter.is_available(),
            "has_lgb_model": self.lgb_adapter is not None and hasattr(self.lgb_adapter, 'model') and self.lgb_adapter.model is not None,
            "active_model": active_model,
            "user_corrections": self._user_corrections,
            "cache_size": len(self.classification_cache),
            "use_bot_model": self.use_bot_model
        }
        
        # Добавляем статистику bot_model
        if self.bot_model_adapter and self.bot_model_adapter.is_available():
            bot_stats = self.bot_model_adapter.get_stats()
            stats["bot_model"] = bot_stats
            
        # Добавляем статистику LightGBM
        if self.lgb_adapter:
            model_info = self.lgb_adapter.get_model_info()
            stats["lightgbm"] = model_info
            
        return stats

    def load_examples(self):
        """Загружает старые примеры только для fallback"""
        if not (self.bot_model_adapter and self.bot_model_adapter.is_available()):
            examples_file = Path(MODEL_PATH) / 'examples.pkl'
            if examples_file.exists():
                with open(examples_file, 'rb') as f:
                    self.examples = pickle.load(f)
                    logger.info(f"Загружено {len(self.examples)} fallback примеров")
            else:
                logger.info("Файл с примерами не найден, используется пустой список")

    def encode_text(self, text: str) -> np.ndarray:
        """Получение эмбеддинга для одного текста (fallback)"""
        if not text or not self.embedder:
            return np.array([])
        return self.embedder.encode_text(text)
    
    def encode_texts(self, texts: List[str]) -> np.ndarray:
        """Получение эмбеддингов для списка текстов (fallback)"""
        if not texts or not self.embedder:
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
        """Классификация текста с интеграцией bot_model, LightGBM модели и кешированием"""
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
            has_bot_model = self.bot_model_adapter and self.bot_model_adapter.is_available()
            has_lgb = hasattr(self, 'lgb_adapter') and self.lgb_adapter and self.lgb_adapter.model_loaded
            lgb_status = "отключена" if self.lgb_disabled_by_corrections else "активна"
            logger.info(f"Классифицируем текст (bot_model: {has_bot_model}, LightGBM: {has_lgb and not self.lgb_disabled_by_corrections} ({lgb_status}), fallback данных: {len(getattr(self, '_training_embeddings', []))}, исправлений: {getattr(self, '_user_corrections', 0)}): {text[:50]}...")
            
            result = None
            
            # 1. Приоритет: Пытаемся использовать bot_model
            if has_bot_model and self.use_bot_model:
                try:
                    logger.info("Используем bot_model для классификации")
                    # Векторизуем текст
                    vector = text_vectorizer.vectorize(normalized_text)
                    features = vector.reshape(1, -1)  # Преобразуем в формат (1, 384)
                    
                    # Получаем предсказание
                    category, confidence = self.bot_model_adapter.predict(features)
                    logger.info(f"bot_model предсказание: {category} ({confidence:.3f})")
                    result = (category, confidence)
                except Exception as e:
                    logger.warning(f"Ошибка в bot_model предсказании: {e}")
            
            # 2. Fallback: Пытаемся использовать продвинутую LightGBM модель если доступна и не отключена
            if not result and has_lgb and not self.lgb_disabled_by_corrections:
                try:
                    lgb_result = self.lgb_adapter.predict(normalized_text)
                    if lgb_result:
                        category, confidence = lgb_result
                        logger.info(f"LightGBM предсказание: {category} ({confidence:.3f})")
                        result = (category, confidence)
                except Exception as e:
                    logger.warning(f"Ошибка в LightGBM предсказании: {e}")
                    
            # 3. Fallback: Если другие модели не сработали, используем KNN
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
        # Если есть bot_model, получаем категории из неё (приоритет)
        if hasattr(self, 'bot_model_adapter') and self.bot_model_adapter and self.bot_model_adapter.is_available():
            try:
                bot_categories = self.bot_model_adapter.get_categories()
                if bot_categories:
                    logger.info(f"Возвращаем {len(bot_categories)} категорий из bot_model")
                    return bot_categories
            except Exception as e:
                logger.warning(f"Ошибка получения категорий из bot_model: {e}")
        
        # Если есть LightGBM модель, получаем категории из неё
        if hasattr(self, 'lgb_adapter') and self.lgb_adapter and hasattr(self.lgb_adapter, 'get_categories'):
            try:
                lgb_categories = self.lgb_adapter.get_categories()
                if lgb_categories:
                    return lgb_categories
            except Exception as e:
                logger.warning(f"Ошибка получения категорий из LightGBM: {e}")
        
        # Иначе возвращаем fallback категории
        # Если FALLBACK_CATEGORIES - это словарь, извлекаем все подкатегории
        if isinstance(FALLBACK_CATEGORIES, dict):
            all_categories = []
            for main_cat, sub_cats in FALLBACK_CATEGORIES.items():
                all_categories.append(main_cat)  # Добавляем основную категорию
                if isinstance(sub_cats, list):
                    all_categories.extend(sub_cats)  # Добавляем подкатегории
            return all_categories
        elif isinstance(FALLBACK_CATEGORIES, list):
            return FALLBACK_CATEGORIES
        else:
            return ["Прочее"]  # Последний fallback

    async def get_examples_count(self) -> int:
        """Возвращает количество обучающих примеров"""
        # Если bot_model активна, возвращаем её статистику
        if self.bot_model_adapter and self.bot_model_adapter.is_available():
            return self.bot_model_adapter.get_training_examples_count()
        
        # Иначе возвращаем количество fallback примеров
        return len(getattr(self, '_training_embeddings', []))

    async def save_model(self) -> bool:
        """Сохраняет fallback модель (только если bot_model недоступна)"""
        if self.bot_model_adapter and self.bot_model_adapter.is_available():
            logger.info("bot_model активна, сохранение fallback модели пропущено")
            return True
            
        try:
            # Создаем временную директорию, которая автоматически удалится после выхода из контекста
            with tempfile.TemporaryDirectory() as temp_dir:
                # Создаем пути к временным файлам
                temp_model = Path(temp_dir) / "fallback_model.pkl"
                temp_encoder = Path(temp_dir) / "fallback_label_encoder.pkl"
                
                # Сохраняем файлы во временную директорию
                with open(temp_model, 'wb') as f:
                    pickle.dump(self.classifier, f)
                with open(temp_encoder, 'wb') as f:
                    pickle.dump(self.label_encoder, f)
                
                # Создаем целевую директорию
                os.makedirs(MODEL_PATH, exist_ok=True)
                
                # Перемещаем файлы в целевую директорию
                shutil.copy2(temp_model, Path(MODEL_PATH) / 'fallback_classifier.pkl')
                shutil.copy2(temp_encoder, Path(MODEL_PATH) / 'fallback_label_encoder.pkl')
                
                return True
                
        except Exception as e:
            logger.error(f"Ошибка сохранения модели: {e}")
            return False

    async def load_model(self) -> bool:
        """Загружает fallback модель (только если bot_model недоступна)"""
        if self.bot_model_adapter and self.bot_model_adapter.is_available():
            logger.info("bot_model активна, загрузка fallback модели пропущена")
            return True
            
        try:
            # Сначала пытаемся загрузить fallback файлы
            fallback_model_file = Path(MODEL_PATH) / 'fallback_classifier.pkl'
            fallback_encoder_file = Path(MODEL_PATH) / 'fallback_label_encoder.pkl'
            
            if fallback_model_file.exists() and fallback_encoder_file.exists():
                with open(fallback_model_file, 'rb') as f:
                    self.classifier = pickle.load(f)
                with open(fallback_encoder_file, 'rb') as f:
                    self.label_encoder = pickle.load(f)
                logger.info("Загружена fallback модель")
                return True
            
            # Если fallback нет, пытаемся загрузить старые файлы
            model_file = Path(MODEL_PATH) / 'classifier.pkl'
            encoder_file = Path(MODEL_PATH) / 'label_encoder.pkl'
            
            if model_file.exists() and encoder_file.exists():
                with open(model_file, 'rb') as f:
                    self.classifier = pickle.load(f)
                with open(encoder_file, 'rb') as f:
                    self.label_encoder = pickle.load(f)
                logger.info("Загружена старая модель")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Ошибка загрузки fallback модели: {e}")
            return False

    async def train(self, text: str, category: str, user_id: int) -> bool:
        """Обучение на одном примере (для bot_model используется отдельная система)"""
        try:
            # Если bot_model активна, логируем но не обучаем старую модель
            if self.bot_model_adapter and self.bot_model_adapter.is_available():
                logger.info(f"Обучающий пример для будущего дообучения bot_model: '{text[:50]}...' -> '{category}'")
                # TODO: Здесь можно сохранять примеры для будущего переобучения bot_model
                return True
            
            # Увеличиваем счетчик пользовательских исправлений для fallback модели
            self._user_corrections += 1
            logger.info(f"Fallback обучение #{self._user_corrections}: '{category}'")
            
            # Отключаем LightGBM после нескольких исправлений
            if self._user_corrections >= self._correction_threshold and not self.lgb_disabled_by_corrections:
                self.lgb_disabled_by_corrections = True
                logger.warning(f"🚫 LightGBM модель отключена после {self._user_corrections} исправлений.")
            
            # Проверка валидности категории
            valid_categories = self.get_categories()
            if category not in valid_categories:
                logger.warning(f"Неверная категория: {category}")
                return False
                
            # Проверка длины текста
            if len(text) < MIN_TEXT_LENGTH:
                logger.warning(f"Текст слишком короткий: {len(text)} символов")
                return False
                
            # Получаем эмбеддинг только если embedder доступен
            if not self.embedder:
                logger.warning("Embedder недоступен для fallback обучения")
                return False
                
            embedding = self.encode_text(text)
            if embedding.size == 0:
                logger.warning("Не удалось получить эмбеддинг для fallback обучения")
                return False
            
            # Добавляем пример в fallback обучающие данные
            if not hasattr(self, '_training_embeddings'):
                self._training_embeddings = []
                self._training_labels = []
            
            self._training_embeddings.append(embedding)
            self._training_labels.append(category)
            
            # Переобучаем fallback KNN модель
            if hasattr(self, 'knn_model') and self.knn_model:
                try:
                    X = np.array(self._training_embeddings)
                    y = np.array(self._training_labels)
                    self.knn_model.fit(X, y)
                    logger.info(f"✅ Fallback KNN модель переобучена на {len(self._training_embeddings)} примерах")
                except Exception as e:
                    logger.error(f"Ошибка переобучения fallback KNN: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка в train: {e}")
            return False
                
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
            # Проверяем доступность модели
            if not (self.bot_model_adapter and self.bot_model_adapter.is_available()) and not hasattr(self, '_training_embeddings'):
                return [("Нет доступных моделей", 0.0)] * len(texts)
                
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
        """Создает резервную копию fallback модели (только если bot_model недоступна)"""
        if self.bot_model_adapter and self.bot_model_adapter.is_available():
            logger.info("bot_model активна, бэкап fallback модели пропущен")
            return True
            
        try:
            # Упрощенный бэкап только для fallback данных
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"ml/trained/fallback_backup_{timestamp}.json"
            
            backup_data = {
                'user_corrections': getattr(self, '_user_corrections', 0),
                'training_examples': getattr(self, '_training_embeddings', []),
                'training_labels': getattr(self, '_training_labels', []),
                'timestamp': timestamp
            }
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
                
            logger.info(f"Fallback модель сохранена в {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка создания бэкапа fallback модели: {e}")
            return False

    def load_latest_backup(self) -> bool:
        """Загружает последний бэкап fallback модели (только если bot_model недоступна)"""
        if self.bot_model_adapter and self.bot_model_adapter.is_available():
            logger.info("bot_model активна, загрузка fallback бэкапа пропущена")
            return True
            
        try:
            # Ищем последний файл бэкапа
            backup_files = list(Path("ml/trained").glob("fallback_backup_*.json"))
            if not backup_files:
                logger.warning("Файлы бэкапа fallback модели не найдены")
                return False

            latest_backup = max(backup_files, key=lambda f: f.stat().st_mtime)
            
            with open(latest_backup, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # Восстанавливаем данные
            self._user_corrections = backup_data.get('user_corrections', 0)
            self._training_embeddings = backup_data.get('training_examples', [])
            self._training_labels = backup_data.get('training_labels', [])
            
            logger.info(f"Fallback модель восстановлена из {latest_backup}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка загрузки бэкапа fallback модели: {e}")
            return False

    def clear_cache(self) -> int:
        """Очищает кеш классификации и возвращает количество удаленных записей"""
        try:
            cache_size = len(getattr(self, 'classification_cache', {}))
            
            # Очищаем кеш классификации
            if hasattr(self, 'classification_cache'):
                self.classification_cache.clear()
            
            # Очищаем кеш LightGBM если доступен
            lgb_cache_size = 0
            if hasattr(self, 'lgb_adapter') and self.lgb_adapter and hasattr(self.lgb_adapter, 'clear_cache'):
                lgb_cache_size = self.lgb_adapter.clear_cache()
            
            # Очищаем кеш bot_model если доступен
            bot_cache_size = 0
            if hasattr(self, 'bot_model_adapter') and self.bot_model_adapter and hasattr(self.bot_model_adapter, 'clear_cache'):
                bot_cache_size = self.bot_model_adapter.clear_cache()
            
            total_cleared = cache_size + lgb_cache_size + bot_cache_size
            logger.info(f"Очищен кеш: классификатор ({cache_size}), LightGBM ({lgb_cache_size}), bot_model ({bot_cache_size})")
            
            return total_cleared
            
        except Exception as e:
            logger.error(f"Ошибка очистки кеша: {e}")
            return 0
