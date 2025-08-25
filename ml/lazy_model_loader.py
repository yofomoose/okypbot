"""
Ленивый загрузчик моделей ML с поддержкой частичной загрузки
"""

import numpy as np
import joblib
import pickle
import logging
import gc
from pathlib import Path
from typing import Any, Optional, Dict, List

logger = logging.getLogger(__name__)

class LazyModelLoader:
    """Загрузчик моделей с поддержкой частичной загрузки"""
    
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self._model = None
        self._is_loaded = False
        
    def _load_pickle_in_chunks(self, chunk_size: int = 1024*1024) -> Any:
        """Загрузка pickle файла по частям"""
        logger.info(f"Загрузка модели по частям, размер чанка: {chunk_size} байт")
        
        with open(self.model_path, 'rb') as f:
            # Читаем заголовок pickle
            header = f.readline()
            
            # Подготавливаем буфер для данных
            data = bytearray()
            
            # Читаем файл по частям
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                    
                # Очищаем память после каждого чанка
                gc.collect()
                
                data.extend(chunk)
                logger.debug(f"Прочитано {len(data)} байт")
                
        try:
            # Пробуем разные варианты загрузки
            for encoding in ['latin1', 'bytes', None]:
                try:
                    logger.info(f"Пробуем загрузить с encoding={encoding}")
                    model = pickle.loads(data, encoding=encoding)
                    return model
                except Exception as e:
                    logger.warning(f"Не удалось загрузить с encoding={encoding}: {e}")
                    continue
                    
            raise ValueError("Не удалось загрузить модель ни с одним encoding")
            
        finally:
            # Очищаем буфер и вызываем сборщик мусора
            del data
            gc.collect()
            
    def load(self) -> Any:
        """Загрузка модели"""
        if self._is_loaded:
            return self._model
            
        logger.info(f"Загрузка модели из {self.model_path}")
        
        try:
            # Сначала пробуем через joblib
            if str(self.model_path).endswith('.joblib'):
                logger.info("Загрузка через joblib...")
                self._model = joblib.load(str(self.model_path), mmap_mode='r')
            else:
                # Если не joblib, используем частичную загрузку pickle
                logger.info("Загрузка через pickle по частям...")
                self._model = self._load_pickle_in_chunks()
                
            self._is_loaded = True
            return self._model
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке модели: {e}")
            raise
