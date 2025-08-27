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

class LazyModelLoader:
    """Загрузчик моделей с поддержкой частичной загрузки"""
    
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self._model = None
        self._is_loaded = False
        
    def _load_pickle_in_chunks(self, chunk_size: int = 1024*1024) -> Any:
        """Загрузка pickle файла по частям"""
        logger.info(f"Загрузка модели по частям, размер чанка: {chunk_size} байт")
        
        try:
            data = bytearray()
            with open(self.model_path, 'rb') as f:
                # Читаем первые байты для анализа формата
                magic_bytes = f.read(16)
                f.seek(0)
                
                # Анализируем формат файла
                if magic_bytes.startswith(b'\x80\x03') or magic_bytes.startswith(b'\x80\x04'):
                    logger.info("Обнаружен формат Python 3 pickle")
                elif magic_bytes.startswith(b'\x80\x02'):
                    logger.info("Обнаружен формат Python 2 pickle")
                else:
                    hex_bytes = ' '.join(f'{b:02x}' for b in magic_bytes)
                    logger.info(f"Неизвестный формат файла. Первые байты: {hex_bytes}")
                
                # Читаем файл по частям
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                        
                    # Очищаем память после каждого чанка
                    gc.collect()
                    
                    data.extend(chunk)
                    logger.debug(f"Прочитано {len(data)} байт")

            # Пробуем разные варианты загрузки с разными протоколами
            import pickle
            model = None
            
            # Перебираем все комбинации протоколов и кодировок
            for protocol in [5, 4, 3, 2]:
                for encoding in ['latin1', 'bytes', 'ascii']:
                    try:
                        logger.info(f"Пробуем загрузить с protocol={protocol}, encoding={encoding}")
                        if protocol <= 2:
                            # Для старых протоколов используем fix_imports
                            model = pickle.loads(data, encoding=encoding, fix_imports=True)
                        else:
                            model = pickle.loads(data, encoding=encoding)
                        
                        if model is not None:
                            logger.info(f"Успешно загружено с protocol={protocol}, encoding={encoding}")
                            return model
                            
                    except Exception as e:
                        logger.warning(f"Не удалось загрузить с protocol={protocol}, encoding={encoding}: {e}")
                        continue
            
            # Если все попытки с pickle не удались, пробуем через joblib
            logger.info("Pickle загрузка не удалась, пробуем joblib...")
            try:
                import tempfile
                with tempfile.NamedTemporaryFile() as temp:
                    temp.write(data)
                    temp.flush()
                    model = joblib.load(temp.name)
                    if model is not None:
                        logger.info("Успешно загружено через joblib")
                        return model
            except Exception as e:
                logger.warning(f"Не удалось загрузить через joblib: {e}")
                raise ValueError("Не удалось загрузить модель ни одним способом")
        except Exception as e:
            logger.error(f"Ошибка при загрузке модели: {e}")
            raise
        finally:
            # Очищаем буфер и вызываем сборщик мусора
            if 'data' in locals():
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
