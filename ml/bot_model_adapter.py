"""
Адаптер для интеграции модели из папки bot_model
"""

import json
import numpy as np
import logging
import gc
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from .lazy_model_loader import LazyModelLoader
from datetime import datetime

logger = logging.getLogger(__name__)

class BotModelAdapter:
    """Адаптер для работы с моделью из папки bot_model"""
    
    def __init__(self, model_dir: str = "bot_model"):
        self.model_dir = Path(model_dir)
        self.classifier = None
        self.label_encoder = None
        self.metadata = None
        self.is_loaded = False
        
        # Пути к файлам модели
        self.classifier_path = self.model_dir / "classifier.joblib"
        if not self.classifier_path.exists():
            self.classifier_path = self.model_dir / "classifier.pkl"
            
        self.encoder_path = self.model_dir / "label_encoder.joblib"
        if not self.encoder_path.exists():
            self.encoder_path = self.model_dir / "label_encoder.pkl"
            
        self.metadata_path = self.model_dir / "model_metadata.json"
        
    def load_model(self) -> bool:
        """Загружает модель и все компоненты"""
        try:
            logger.info("Загрузка модели из bot_model...")
            
            # Проверяем наличие всех файлов
            required_files = [self.classifier_path, self.encoder_path, self.metadata_path]
            for file_path in required_files:
                if not file_path.exists():
                    logger.error(f"Не найден файл: {file_path}")
                    return False
            
            # Проверяем, что numpy доступен
            try:
                import numpy as np
                logger.info(f"Numpy версия: {np.__version__}")
            except ImportError as e:
                logger.error(f"Ошибка импорта numpy: {e}")
                return False
            
            try:
                # Проверяем numpy.core
                try:
                    import numpy.core.numeric
                    import numpy.core.multiarray
                    logger.info("numpy.core компоненты успешно импортированы")
                except ImportError as e:
                    logger.error(f"Ошибка импорта numpy.core: {e}")
                    return False

                # Используем безопасный загрузчик моделей
                from .model_loader import safe_load_model
                
                # Загружаем классификатор
                logger.info("Загрузка классификатора...")
                filesize = Path(self.classifier_path).stat().st_size
                logger.info(f"Размер файла модели: {filesize} байт")
                
                try:
                    # Используем ленивую загрузку для классификатора
                    logger.info("Загрузка классификатора через LazyModelLoader...")
                    classifier_loader = LazyModelLoader(str(self.classifier_path))
                    self.classifier = classifier_loader.load()
                    logger.info(f"Классификатор загружен: {type(self.classifier).__name__}")
                    
                    # Очищаем память после загрузки классификатора
                    gc.collect()
                    
                    # Загружаем энкодер
                    logger.info("Загрузка label encoder...")
                    encoder_loader = LazyModelLoader(str(self.encoder_path))
                    self.label_encoder = encoder_loader.load()
                    logger.info(f"Энкодер загружен, классов: {len(self.label_encoder.classes_)}")
                    
                    # Очищаем память после загрузки энкодера
                    gc.collect()
                    
                except Exception as e:
                    logger.error(f"Ошибка при загрузке модели: {str(e)}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    return False
            except Exception as e:
                logger.error(f"Ошибка загрузки модели: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return False
            
            # Загружаем метаданные
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            logger.info(f"Метаданные загружены: {self.metadata.get('model_type', 'Unknown')}")
            
            self.is_loaded = True
            logger.info("✅ Модель bot_model успешно загружена")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка загрузки модели bot_model: {e}")
            self.is_loaded = False
            return False
    
    def predict(self, features: np.ndarray) -> Tuple[str, float]:
        """
        Выполняет предсказание категории
        
        Args:
            features: Массив признаков размерности (1, 384)
            
        Returns:
            Tuple[str, float]: (категория, уверенность)
        """
        if not self.is_loaded:
            raise ValueError("Модель не загружена")
        
        if features.shape[1] != self.metadata.get('feature_count', 384):
            raise ValueError(f"Неверная размерность признаков: {features.shape[1]}, ожидается {self.metadata.get('feature_count', 384)}")
        
        try:
            # Получаем предсказание
            prediction = self.classifier.predict(features)
            
            # Декодируем предсказание с обработкой ошибок
            try:
                category = self.label_encoder.inverse_transform(prediction)[0]
            except ValueError as e:
                # Если категория не найдена в encoder'е, используем fallback
                logger.warning(f"Категория {prediction[0]} не найдена в label_encoder: {e}")
                
                # Пытаемся найти ближайших соседей для получения категории
                if hasattr(self.classifier, 'kneighbors'):
                    distances, indices = self.classifier.kneighbors(features, n_neighbors=5)
                    
                    # Получаем категории ближайших соседей
                    neighbor_labels = self.classifier._y[indices[0]]
                    
                    # Находим наиболее частую категорию среди соседей
                    unique_labels, counts = np.unique(neighbor_labels, return_counts=True)
                    most_common_label = unique_labels[np.argmax(counts)]
                    
                    # Пытаемся декодировать наиболее частую категорию
                    try:
                        category = self.label_encoder.inverse_transform([most_common_label])[0]
                    except ValueError:
                        # Если и это не работает, ищем первую доступную категорию
                        available_categories = self.label_encoder.classes_
                        category = available_categories[0] if len(available_categories) > 0 else "Другое"
                        logger.warning(f"Использована fallback категория: {category}")
                else:
                    # Если нет kneighbors, используем первую доступную категорию
                    available_categories = self.label_encoder.classes_
                    category = available_categories[0] if len(available_categories) > 0 else "Другое"
                    logger.warning(f"Использована fallback категория: {category}")
            
            # Получаем уверенность если возможно
            confidence = 0.0
            if hasattr(self.classifier, 'predict_proba'):
                probabilities = self.classifier.predict_proba(features)[0]
                confidence = float(np.max(probabilities))
            elif hasattr(self.classifier, 'kneighbors'):
                # Для KNN используем расстояние до ближайших соседей
                distances, _ = self.classifier.kneighbors(features)
                # Преобразуем расстояние в уверенность (чем меньше расстояние, тем больше уверенность)
                avg_distance = np.mean(distances[0])
                confidence = float(1.0 / (1.0 + avg_distance))
            
            return category, confidence
            
        except Exception as e:
            logger.error(f"Ошибка предсказания: {e}")
            return "Другое", 0.0
    
    def get_categories(self) -> List[str]:
        """Возвращает список всех доступных категорий"""
        if not self.is_loaded or self.label_encoder is None:
            return []
        return list(self.label_encoder.classes_)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Возвращает информацию о модели"""
        if not self.is_loaded:
            return {"status": "not_loaded"}
        
        return {
            "status": "loaded",
            "model_type": self.metadata.get('model_type', 'Unknown'),
            "feature_count": self.metadata.get('feature_count', 0),
            "n_neighbors": self.metadata.get('n_neighbors', 0),
            "training_samples": self.metadata.get('training_samples', 0),
            "categories_count": len(self.get_categories()),
            "migration_date": self.metadata.get('migration_date', 'Unknown'),
            "optimized_for": self.metadata.get('optimized_for', 'Unknown')
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику модели"""
        info = self.get_model_info()
        categories = self.get_categories()
        
        return {
            "model_loaded": self.is_loaded,
            "model_type": info.get('model_type', 'Unknown'),
            "categories_count": len(categories),
            "feature_count": info.get('feature_count', 0),
            "training_samples": info.get('training_samples', 0),
            "example_categories": categories[:10] if categories else [],
            "supports_probability": hasattr(self.classifier, 'predict_proba') if self.classifier else False
        }
    
    def is_available(self) -> bool:
        """Проверяет доступность модели"""
        return self.is_loaded and self.classifier is not None and self.label_encoder is not None

    def clear_cache(self) -> int:
        """Очищает кеш предсказаний и возвращает количество удаленных записей"""
        try:
            if hasattr(self, '_prediction_cache'):
                cache_size = len(self._prediction_cache)
                self._prediction_cache.clear()
                logger.debug(f"Очищен кеш bot_model: {cache_size} записей")
                return cache_size
            return 0
        except Exception as e:
            logger.error(f"Ошибка очистки кеша bot_model: {e}")
            return 0

    def get_training_examples_count(self) -> int:
        """Возвращает количество обучающих примеров модели"""
        return self.metadata.get('training_samples', 0) if self.metadata else 0
