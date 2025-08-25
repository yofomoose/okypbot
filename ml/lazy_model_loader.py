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
