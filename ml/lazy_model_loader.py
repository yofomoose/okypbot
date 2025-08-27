"""
Ленивый загрузчик моделей ML с поддержкой частичной загрузки
"""

import gc
import sys
import pickle
import joblib
import logging
from pathlib import Path
from typing import Any, Optional, Dict, List

logger = logging.getLogger(__name__)

try:
    import numpy as np
    import numpy.core
    from numpy.core import multiarray
    from numpy.core import numeric
    from numpy.core import _multiarray_umath
    np._core = numpy.core  # Важный хак для поддержки pickle
    logger.info(f"NumPy {np.__version__} инициализирован для загрузки моделей")
except ImportError as e:
    logger.error(f"Ошибка инициализации NumPy: {e}")
    logger.error(f"Системная информация: Python {sys.version}")
    raise

class LazyModelLoader:
    def load(self) -> Optional[Any]:
        """
        Обратная совместимость: загрузить первую доступную модель из model_paths.
        Если моделей несколько, логирует предупреждение.
        """
        if not self.model_paths:
            logger.error("Нет доступных моделей для загрузки (model_paths пуст)")
            return None
        if len(self.model_paths) > 1:
            logger.warning(f"В model_paths несколько моделей: {list(self.model_paths.keys())}. Будет загружена первая.")
        first_model = next(iter(self.model_paths.keys()))
        return self.load_model(first_model)
    """Класс для ленивой загрузки ML моделей"""
    
    def __init__(self, model_paths: Dict[str, Path]):
        """
        Инициализация загрузчика моделей
        
        Args:
            model_paths: Словарь путей к файлам моделей {имя_модели: путь}
        """
        self.model_paths = model_paths
        self._loaded_models: Dict[str, Any] = {}
        self._model_metadata: Dict[str, Dict] = {}
        
    def load_model(self, model_name: str) -> Optional[Any]:
        """
        Ленивая загрузка модели по имени
        
        Args:
            model_name: Имя модели для загрузки
            
        Returns:
            Загруженная модель или None в случае ошибки
        """
        if model_name not in self.model_paths:
            logger.error(f"Модель {model_name} не найдена в paths")
            return None

        if model_name in self._loaded_models:
            return self._loaded_models[model_name]

        try:
            model_path = self.model_paths[model_name]

            logger.warning(f"Попытка загрузки файла: {model_path}")
            logger.info(f"Загружаем модель {model_name} из {model_path}")
            ext = str(model_path).lower().split('.')[-1]
            if ext == 'pkl':
                logger.warning(f"Открываю файл для pickle.load: {model_path}")
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
            elif ext == 'joblib':
                logger.warning(f"Открываю файл для joblib.load: {model_path}")
                model = joblib.load(model_path)
            else:
                logger.error(f"Файл {model_path} имеет неподдерживаемое расширение: .{ext}. Загрузка запрещена!")
                raise ValueError(f"Неподдерживаемое расширение файла модели: .{ext}")


            logger.info(f"Загружен объект типа: {type(model)}, методы: {dir(model)}")
            if not hasattr(model, 'get_stats'):
                logger.error(f"Загруженный объект из файла {model_path} не содержит метод 'get_stats'! Тип: {type(model)}. Методы: {dir(model)}")
            self._loaded_models[model_name] = model
            logger.info(f"Модель {model_name} успешно загружена")
            return model

        except Exception as e:
            logger.error(f"Ошибка при загрузке модели {model_name} из файла {model_path}: {e}")
            return None
            
    def unload_model(self, model_name: str) -> None:
        """
        Выгрузка модели из памяти
        
        Args:
            model_name: Имя модели для выгрузки
        """
        if model_name in self._loaded_models:
            logger.info(f"Выгружаем модель {model_name}")
            del self._loaded_models[model_name]
            gc.collect()  # Принудительный сбор мусора
            
    def get_loaded_models(self) -> List[str]:
        """Получение списка загруженных моделей"""
        return list(self._loaded_models.keys())
        
    def load_metadata(self, model_name: str) -> Optional[Dict]:
        """
        Загрузка метаданных модели
        
        Args:
            model_name: Имя модели
            
        Returns:
            Словарь метаданных или None
        """
        if model_name not in self.model_paths:
            return None
            
        if model_name in self._model_metadata:
            return self._model_metadata[model_name]
            
        try:
            metadata_path = self.model_paths[model_name].parent / f"{model_name}_metadata.json"
            if metadata_path.exists():
                import json
                with open(metadata_path) as f:
                    metadata = json.load(f)
                self._model_metadata[model_name] = metadata
                return metadata
        except Exception as e:
            logger.error(f"Ошибка загрузки метаданных для {model_name}: {e}")
            
        return None

