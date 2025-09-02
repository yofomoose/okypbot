"""
Модуль для связывания сотрудников OkDesk и пользователей Telegram
"""
import os
import json
import logging
from typing import Dict, Optional, List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class EmployeeMappingService:
    """Сервис для сопоставления сотрудников OkDesk и пользователей Telegram"""
    
    def __init__(self, mapping_file: str = None):
        """
        Инициализация сервиса
        
        :param mapping_file: Путь к файлу с сопоставлениями. По умолчанию 'database/employee_mapping.json'
        """
        self.mapping_file = mapping_file or os.path.join('database', 'employee_mapping.json')
        self.mapping: Dict[str, int] = {}  # okdesk_employee_id -> telegram_id
        self.reverse_mapping: Dict[int, str] = {}  # telegram_id -> okdesk_employee_id
        self.default_employee_id = None
        self.load_mapping()
    
    def load_mapping(self) -> bool:
        """
        Загружает сопоставления из файла
        
        :return: True если сопоставления загружены успешно, иначе False
        """
        try:
            file_path = Path(self.mapping_file)
            if not file_path.exists():
                logger.warning(f"Файл сопоставлений {self.mapping_file} не найден, создаем пустой файл")
                self.save_mapping()
                return True
            
            with open(self.mapping_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Преобразуем ключи из строк в числа где нужно
                self.mapping = {str(k): int(v) for k, v in data.get('mapping', {}).items()}
                self.reverse_mapping = {int(k): str(v) for k, v in data.get('reverse_mapping', {}).items()}
                
                # Загружаем ID сотрудника по умолчанию
                default_id = data.get('default_employee_id')
                self.default_employee_id = str(default_id) if default_id else None
                
                logger.info(f"Загружено {len(self.mapping)} сопоставлений сотрудников")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка при загрузке сопоставлений сотрудников: {e}")
            return False
    
    def save_mapping(self) -> bool:
        """
        Сохраняет сопоставления в файл
        
        :return: True если сопоставления сохранены успешно, иначе False
        """
        try:
            # Создаем директорию, если она не существует
            os.makedirs(os.path.dirname(self.mapping_file), exist_ok=True)
            
            data = {
                'mapping': self.mapping,
                'reverse_mapping': self.reverse_mapping,
                'default_employee_id': self.default_employee_id
            }
            
            with open(self.mapping_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Сопоставления сохранены в {self.mapping_file}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении сопоставлений сотрудников: {e}")
            return False
    
    def add_mapping(self, okdesk_employee_id: str, telegram_id: int) -> bool:
        """
        Добавляет сопоставление между ID сотрудника OkDesk и ID пользователя Telegram
        
        :param okdesk_employee_id: ID сотрудника в OkDesk
        :param telegram_id: ID пользователя в Telegram
        :return: True если сопоставление добавлено успешно, иначе False
        """
        try:
            okdesk_employee_id = str(okdesk_employee_id)
            telegram_id = int(telegram_id)
            
            # Добавляем сопоставление
            self.mapping[okdesk_employee_id] = telegram_id
            self.reverse_mapping[telegram_id] = okdesk_employee_id
            
            # Сохраняем изменения
            return self.save_mapping()
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении сопоставления сотрудника: {e}")
            return False
    
    def remove_mapping(self, okdesk_employee_id: str = None, telegram_id: int = None) -> bool:
        """
        Удаляет сопоставление по ID сотрудника OkDesk или ID пользователя Telegram
        
        :param okdesk_employee_id: ID сотрудника в OkDesk
        :param telegram_id: ID пользователя в Telegram
        :return: True если сопоставление удалено успешно, иначе False
        """
        try:
            if okdesk_employee_id:
                okdesk_employee_id = str(okdesk_employee_id)
                if okdesk_employee_id in self.mapping:
                    telegram_id = self.mapping[okdesk_employee_id]
                    del self.mapping[okdesk_employee_id]
                    if telegram_id in self.reverse_mapping:
                        del self.reverse_mapping[telegram_id]
            
            elif telegram_id:
                telegram_id = int(telegram_id)
                if telegram_id in self.reverse_mapping:
                    okdesk_employee_id = self.reverse_mapping[telegram_id]
                    del self.reverse_mapping[telegram_id]
                    if okdesk_employee_id in self.mapping:
                        del self.mapping[okdesk_employee_id]
            
            # Сохраняем изменения
            return self.save_mapping()
            
        except Exception as e:
            logger.error(f"Ошибка при удалении сопоставления сотрудника: {e}")
            return False
    
    def set_default_employee_id(self, okdesk_employee_id: str) -> bool:
        """
        Устанавливает ID сотрудника OkDesk по умолчанию
        
        :param okdesk_employee_id: ID сотрудника в OkDesk
        :return: True если ID сотрудника установлен успешно, иначе False
        """
        try:
            self.default_employee_id = str(okdesk_employee_id)
            return self.save_mapping()
            
        except Exception as e:
            logger.error(f"Ошибка при установке ID сотрудника по умолчанию: {e}")
            return False
    
    def get_telegram_id(self, okdesk_employee_id: str) -> Optional[int]:
        """
        Получает ID пользователя Telegram по ID сотрудника OkDesk
        
        :param okdesk_employee_id: ID сотрудника в OkDesk
        :return: ID пользователя в Telegram или None, если сопоставление не найдено
        """
        okdesk_employee_id = str(okdesk_employee_id)
        return self.mapping.get(okdesk_employee_id)
    
    def get_okdesk_employee_id(self, telegram_id: int) -> Optional[str]:
        """
        Получает ID сотрудника OkDesk по ID пользователя Telegram
        
        :param telegram_id: ID пользователя в Telegram
        :return: ID сотрудника в OkDesk или None, если сопоставление не найдено
        """
        return self.reverse_mapping.get(telegram_id)
    
    def get_default_employee_id(self) -> Optional[str]:
        """
        Получает ID сотрудника OkDesk по умолчанию
        
        :return: ID сотрудника в OkDesk по умолчанию или None
        """
        return self.default_employee_id
    
    def get_all_mappings(self) -> List[Tuple[str, int]]:
        """
        Получает все сопоставления
        
        :return: Список кортежей (okdesk_employee_id, telegram_id)
        """
        return [(k, v) for k, v in self.mapping.items()]
