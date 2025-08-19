import pickle
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

# Импортируем функции нормализации из classifier
try:
    from .classifier import normalize_text, get_text_hash
except ImportError:
    # Fallback функции если импорт не удался
    import re
    def normalize_text(text: str) -> str:
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
        normalized = normalize_text(text)
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    # Создаем заглушку для numpy
    class NumpyStub:
        @staticmethod
        def zeros(shape):
            return [0.0] * shape
        @staticmethod
        def ndarray(*args, **kwargs):
            return list
        @staticmethod
        def argmax(arr):
            if isinstance(arr, (list, tuple)):
                return arr.index(max(arr)) if arr else 0
            return 0
        @staticmethod
        def max(arr):
            return max(arr) if isinstance(arr, (list, tuple)) and arr else 0.0
    np = NumpyStub()

logger = logging.getLogger(__name__)

class AdvancedCustomModelAdapter:
    """Продвинутый адаптер для интеграции пользовательской обученной LightGBM модели"""
    
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.label_encoder = None
        self.categories = None  # Список категорий из файла categories.py
        self.text_classifier = None
        self.embedding_manager = None
        self.model_loaded = False
        self.prediction_cache = {}  # Кеш для стабильных предсказаний
        
    def load_user_model(self, model_path: str) -> bool:
        """Загружает пользовательскую LightGBM модель из указанного пути
        
        Args:
            model_path: Путь к папке с файлами модели
            
        Returns:
            bool: True если модель успешно загружена
        """
        try:
            model_dir = Path(model_path)
            logger.info(f"Загружаем продвинутую модель из: {model_dir}")
            
            # Загружаем LightGBM модель
            model_file = model_dir / "model.txt"
            if model_file.exists():
                try:
                    import lightgbm as lgb
                    self.model = lgb.Booster(model_file=str(model_file))
                    logger.info("LightGBM модель загружена")
                except ImportError:
                    logger.error("LightGBM не установлен")
                    return False
            else:
                logger.error(f"Файл модели не найден: {model_file}")
                return False
            
            # Загружаем категории из вашего файла
            categories_file = model_dir / "categories.py"
            self.categories = None
            if categories_file.exists():
                try:
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("categories", categories_file)
                    categories_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(categories_module)
                    self.categories = categories_module.CATEGORIES
                    logger.info(f"Загружено {len(self.categories)} категорий из categories.py")
                except Exception as e:
                    logger.warning(f"Не удалось загрузить categories.py: {e}")
            
            # Пробуем загрузить исправленный label encoder
            encoder_file_fixed = model_dir / "label_encoder_fixed.pkl"
            encoder_file_original = model_dir / "label_encoder.pkl"
            
            encoder_loaded = False
            if encoder_file_fixed.exists():
                try:
                    with open(encoder_file_fixed, 'rb') as f:
                        self.label_encoder = pickle.load(f)
                    logger.info("Исправленный Label encoder загружен")
                    encoder_loaded = True
                except Exception as e:
                    logger.warning(f"Не удалось загрузить исправленный encoder: {e}")
            
            if not encoder_loaded and encoder_file_original.exists():
                try:
                    with open(encoder_file_original, 'rb') as f:
                        self.label_encoder = pickle.load(f)
                    logger.info("Оригинальный Label encoder загружен")
                    encoder_loaded = True
                except Exception as e:
                    logger.warning(f"Не удалось загрузить оригинальный encoder: {e}")
            
            # Если encoder не загружен, но есть категории - создаем новый
            if not encoder_loaded and self.categories:
                try:
                    from sklearn.preprocessing import LabelEncoder
                    self.label_encoder = LabelEncoder()
                    self.label_encoder.fit(self.categories)
                    logger.info(f"Создан новый Label encoder для {len(self.categories)} категорий")
                    encoder_loaded = True
                except Exception as e:
                    logger.warning(f"Не удалось создать Label encoder: {e}")
            
            if not encoder_loaded:
                logger.warning("Label encoder не загружен - будут использоваться числовые категории")
            
            # Загружаем классификатор
            classifier_file = model_dir / "classifier.pkl"
            if classifier_file.exists():
                with open(classifier_file, 'rb') as f:
                    self.text_classifier = pickle.load(f)
                logger.info("Text classifier загружен")
            
            # Пытаемся загрузить ваш TextClassifier и EmbeddingManager
            try:
                from .trainer import TextClassifier
                from .embeddings import EmbeddingManager
                
                self.text_classifier = TextClassifier()
                self.embedding_manager = EmbeddingManager()
                
                # Загружаем модель в TextClassifier
                if hasattr(self.text_classifier, 'load_model'):
                    self.text_classifier.load_model(str(model_dir))
                    logger.info("TextClassifier успешно инициализирован")
                    
            except ImportError as e:
                logger.warning(f"Не удалось загрузить пользовательские классы: {e}")
            
            self.model_loaded = True
            logger.info("Пользовательская модель успешно загружена")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке пользовательской модели: {e}")
            return False
    
    def predict(self, text: str) -> Optional[Tuple[str, float]]:
        """Предсказание категории для текста используя LightGBM модель
        
        Args:
            text: Текст для классификации
            
        Returns:
            Tuple[str, float]: (категория, уверенность) или None
        """
        if not self.model_loaded:
            logger.warning("Модель не загружена")
            return None
            
        try:
            # Нормализуем текст для стабильной классификации
            normalized_text = normalize_text(text)
            text_hash = get_text_hash(text)
            
            # Проверяем кеш
            if text_hash in self.prediction_cache:
                cached_result = self.prediction_cache[text_hash]
                logger.debug(f"Возвращаем кешированный результат: {cached_result[0]} ({cached_result[1]:.3f})")
                return cached_result
                
            logger.debug(f"LightGBM предсказание для нормализованного текста: {normalized_text[:50]}...")
            
            # Проверяем, какие компоненты доступны
            has_embedding_mgr = self.embedding_manager and hasattr(self.embedding_manager, 'get_embeddings')
            logger.debug(f"Состояние компонентов: embedding_manager={has_embedding_mgr}, model={self.model is not None}")
            
            result = None
            
            # Используем embedding-based подход если доступен
            if has_embedding_mgr and self.model:
                try:
                    # Получаем эмбеддинги
                    if hasattr(self.embedding_manager, 'get_embeddings'):
                        embeddings = self.embedding_manager.get_embeddings([normalized_text])
                        if embeddings is not None and len(embeddings) > 0:
                            # Предсказание через LightGBM
                            prediction = self.model.predict(embeddings[0].reshape(1, -1))
                            
                            if HAS_NUMPY and isinstance(prediction, np.ndarray):
                                # Для многоклассовой классификации
                                if prediction.ndim > 1:
                                    class_idx = np.argmax(prediction[0])
                                    confidence = float(np.max(prediction[0]))
                                else:
                                    class_idx = int(prediction[0])
                                    confidence = 0.8
                            elif isinstance(prediction, (list, tuple)):
                                # Fallback для обычных списков
                                if len(prediction) > 0 and isinstance(prediction[0], (list, tuple)):
                                    class_idx = prediction[0].index(max(prediction[0])) if prediction[0] else 0
                                    confidence = float(max(prediction[0])) if prediction[0] else 0.5
                                else:
                                    class_idx = int(prediction[0]) if prediction else 0
                                    confidence = 0.8
                            else:
                                class_idx = 0
                                confidence = 0.5
                                
                            # Декодируем категорию
                            if self.label_encoder:
                                try:
                                    category = self.label_encoder.inverse_transform([class_idx])[0]
                                except:
                                    category = f"Категория_{class_idx}"
                            else:
                                category = f"Категория_{class_idx}"
                            
                            logger.info(f"Предсказание через LightGBM: {category} ({confidence:.3f})")
                            result = (str(category), confidence)
                            
                except Exception as e:
                    logger.warning(f"Ошибка в embedding-based предсказании: {e}")
            
            # Fallback на простое предсказание
            if not result and self.model:
                try:
                    # Простая векторизация для тестирования
                    features = self._extract_simple_features(normalized_text)
                    
                    if HAS_NUMPY:
                        if hasattr(features, 'reshape'):
                            prediction = self.model.predict(features.reshape(1, -1))
                        else:
                            # features уже список, конвертируем в numpy array
                            features_array = np.array(features).reshape(1, -1)
                            prediction = self.model.predict(features_array)
                    else:
                        # Для моделей, которые принимают списки
                        prediction = self.model.predict([features])
                    
                    if HAS_NUMPY and isinstance(prediction, np.ndarray):
                        if prediction.ndim > 1 and prediction.shape[1] > 1:
                            # Многоклассовая классификация - берем argmax
                            class_idx = np.argmax(prediction[0])
                            confidence = float(np.max(prediction[0]))
                        else:
                            # Бинарная или одномерная - приводим к диапазону классов
                            raw_prediction = float(prediction[0]) if hasattr(prediction[0], '__float__') else 0
                            if self.label_encoder and hasattr(self.label_encoder, 'classes_'):
                                class_idx = int(raw_prediction) % len(self.label_encoder.classes_)
                            elif self.categories:
                                class_idx = int(raw_prediction) % len(self.categories)
                            else:
                                class_idx = int(raw_prediction) % 118  # fallback
                            confidence = 0.6
                    elif isinstance(prediction, (list, tuple)):
                        # Fallback для обычных списков
                        if len(prediction) > 0 and isinstance(prediction[0], (list, tuple)) and len(prediction[0]) > 1:
                            class_idx = prediction[0].index(max(prediction[0])) if prediction[0] else 0
                            confidence = float(max(prediction[0])) if prediction[0] else 0.5
                        else:
                            raw_pred = float(prediction[0]) if prediction and len(prediction) > 0 else 0
                            if self.label_encoder and hasattr(self.label_encoder, 'classes_'):
                                class_idx = int(raw_pred) % len(self.label_encoder.classes_)
                            elif self.categories:
                                class_idx = int(raw_pred) % len(self.categories)
                            else:
                                class_idx = int(raw_pred) % 118
                            confidence = 0.6
                    else:
                        class_idx = 0
                        confidence = 0.5
                        
                    # Определяем категорию с правильной обработкой индексов
                    category = f"Категория_{class_idx}"
                    
                    # Сначала пробуем из categories файла
                    if self.categories and class_idx < len(self.categories):
                        category = self.categories[class_idx]
                    # Потом из label_encoder
                    elif self.label_encoder and hasattr(self.label_encoder, 'classes_') and class_idx < len(self.label_encoder.classes_):
                        try:
                            category = self.label_encoder.inverse_transform([class_idx])[0]
                        except:
                            pass
                    
                    logger.info(f"Fallback предсказание: {category} (индекс: {class_idx}, уверенность: {confidence:.3f})")
                    result = (str(category), confidence)
                        
                except Exception as e:
                    logger.warning(f"Ошибка в fallback предсказании: {e}")
            
            # Сохраняем результат в кеш
            if result:
                self.prediction_cache[text_hash] = result
                # Ограничиваем размер кеша
                if len(self.prediction_cache) > 1000:
                    # Удаляем самые старые записи
                    keys_to_remove = list(self.prediction_cache.keys())[:100]
                    for key in keys_to_remove:
                        del self.prediction_cache[key]
                return result
            
            logger.warning("Не удалось выполнить предсказание")
            return None
            
        except Exception as e:
            logger.error(f"Критическая ошибка при предсказании: {e}")
            return None
    
    def _extract_simple_features(self, text: str):
        """Извлекает простые признаки из текста для совместимости с моделью"""
        words = text.lower().split()
        
        # Создаем 384 признака (совпадает с размерностью вашей модели)
        if HAS_NUMPY:
            features = np.zeros(384)
        else:
            features = [0.0] * 384
        
        # Базовые статистические признаки
        features[0] = len(words)  # количество слов
        features[1] = len(text)   # длина текста
        features[2] = sum(len(word) for word in words) / max(len(words), 1)  # средняя длина слова
        features[3] = text.count(' ')   # количество пробелов
        features[4] = text.count('?')   # количество вопросов
        features[5] = text.count('!')   # количество восклицаний
        features[6] = text.count('.')   # количество точек
        features[7] = len(set(words))   # уникальные слова
        
        # Улучшенные ключевые слова для разных категорий
        text_lower = text.lower()
        keyword_features = {
            # Оргтехника (индексы 10-29)
            'принтер': 10, 'печать': 11, 'сканер': 12, 'мфу': 13, 'картридж': 14,
            'печатает': 15, 'сканирует': 16, 'заправка': 17, 'документ': 18,
            
            # ПК и железо (индексы 30-49)
            'компьютер': 30, 'пк': 31, 'ноутбук': 32, 'виснет': 33, 'тормозит': 34,
            'завис': 35, 'включается': 36, 'монитор': 37, 'комплектующие': 38,
            'диагностика': 39, 'модернизация': 40, 'чистка': 41,
            
            # Сеть и интернет (индексы 50-69)
            'интернет': 50, 'сеть': 51, 'wifi': 52, 'роутер': 53, 'соединение': 54,
            'доступ': 55, 'сервер': 56, 'подключение': 57, 'vpn': 58, 'ip': 59,
            
            # 1С (индексы 70-89)
            '1с': 70, 'база': 71, 'обновление': 72, 'конфигурация': 73, 'лицензия': 74,
            'чек': 75, 'консультация': 76, 'виснет': 77, 'вылетает': 78, 'доступы': 79,
            'платформа': 80, 'релиз': 81,
            
            # ПО и настройка (индексы 90-109)
            'настройка': 90, 'установка': 91, 'почта': 92, 'email': 93, 'антивирус': 94,
            'офис': 95, 'word': 96, 'excel': 97, 'программ': 98, 'по': 99,
            'активация': 100, 'криптопро': 101,
            
            # Проблемы и действия (индексы 110-129)
            'проблема': 110, 'ошибка': 111, 'работает': 112, 'помощь': 113, 'войти': 114,
            'система': 115, 'настроить': 116, 'создание': 117, 'ремонт': 118, 'выезд': 119,
            
            # Специфичные термины (индексы 130-149)
            'ккт': 130, 'эцп': 131, 'скуд': 132, 'атс': 133, 'web': 134,
            'банковский': 135, 'терминал': 136, 'видеонаблюдение': 137, 'монтаж': 138,
        }
        
        # Проверяем ключевые слова
        for keyword, idx in keyword_features.items():
            if idx < 384 and keyword in text_lower:
                features[idx] = 1.0
        
        # Биграммы и фразы (индексы 150-199)
        bigram_features = {
            'не работает': 150, 'не печатает': 151, 'не включается': 152,
            'не сканирует': 153, 'нет соединения': 154, 'нет доступа': 155,
            'настройка по': 156, 'установка программы': 157, 'обновление 1с': 158,
            'проблемы с': 159, 'помощь с': 160, 'нужна помощь': 161,
            'новый пк': 162, 'создание учетной': 163, 'подключение нового': 164,
        }
        
        for phrase, idx in bigram_features.items():
            if idx < 384 and phrase in text_lower:
                features[idx] = 2.0  # Более высокий вес для фраз
        
        # Хеши слов для дополнительного разнообразия (индексы 200-350)
        for i, word in enumerate(words[:150]):  # первые 150 слов
            if i + 200 < 384:
                features[i + 200] = (hash(word) % 1000) / 1000.0  # нормализованный хеш
        
        if HAS_NUMPY:
            return features
        else:
            return features
    
    def get_model_info(self) -> Dict[str, Any]:
        """Возвращает информацию о загруженной модели"""
        info = {
            'loaded': self.model_loaded,
            'has_model': self.model is not None,
            'has_label_encoder': self.label_encoder is not None,
            'has_text_classifier': self.text_classifier is not None,
            'has_embedding_manager': self.embedding_manager is not None,
            'has_categories_file': self.categories is not None,
            'model_type': 'LightGBM',
            'num_classes': len(self.categories) if self.categories else 118,
            'num_features': 384
        }
        
        # Добавляем информацию о классах
        if self.label_encoder and hasattr(self.label_encoder, 'classes_'):
            info['num_classes'] = len(self.label_encoder.classes_)
            info['sample_categories'] = list(self.label_encoder.classes_[:3])  # Первые 3 категории
            info['has_real_categories'] = True
        elif self.categories:
            info['num_classes'] = len(self.categories)
            info['sample_categories'] = self.categories[:3]  # Первые 3 категории из файла
            info['has_real_categories'] = True
        else:
            info['has_real_categories'] = False
        
        if self.model:
            try:
                info['model_type'] = type(self.model).__name__
                if hasattr(self.model, 'num_feature'):
                    info['num_features'] = self.model.num_feature()
                if hasattr(self.model, 'num_model_per_iteration'):
                    model_classes = self.model.num_model_per_iteration()
                    if model_classes and model_classes > 0:
                        info['model_num_classes'] = model_classes
            except:
                pass
                
        return info
    
    def get_categories(self) -> List[str]:
        """Возвращает список доступных категорий"""
        # Сначала проверяем label_encoder (приоритет - он содержит актуальные категории модели)
        if self.label_encoder and hasattr(self.label_encoder, 'classes_'):
            return list(self.label_encoder.classes_)
        
        # Если нет label_encoder, проверяем файл категорий
        if self.categories:
            return self.categories
            
        # Если ничего не найдено, возвращаем пустой список
        logger.warning("Не удалось получить категории из LightGBM модели")
        return []
    
    def clear_cache(self) -> int:
        """Очищает кеш предсказаний и возвращает количество удаленных записей"""
        cache_size = len(self.prediction_cache)
        self.prediction_cache.clear()
        if cache_size > 0:
            logger.info(f"🗑️ Очищен кеш LightGBM ({cache_size} записей)")
        return cache_size
    
    async def predict_async(self, text: str) -> Optional[Tuple[str, float]]:
        """Асинхронная версия предсказания"""
        return self.predict(text)
