"""
Модели базы данных
"""
import json
import os
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class User:
    """Модель пользователя"""
    telegram_id: int
    full_name: str
    phone: str
    user_type: str  # "individual" или "legal"
    position: Optional[str] = None
    company_inn: Optional[str] = None
    okdesk_contact_id: Optional[int] = None
    okdesk_company_id: Optional[int] = None
    okdesk_issue_id: Optional[int] = None  # ID заявки на регистрацию
    is_registered: bool = False
    registration_date: Optional[str] = None

class Database:
    """Простая файловая база данных"""
    
    def __init__(self, db_path: str = "database/users.json"):
        self.db_path = db_path
        self.users: Dict[int, User] = {}
        self.load_data()
    
    def load_data(self):
        """Загрузить данные из файла"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for telegram_id, user_data in data.items():
                        self.users[int(telegram_id)] = User(**user_data)
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Ошибка загрузки базы данных: {e}")
                self.users = {}
    
    def save_data(self):
        """Сохранить данные в файл"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        data = {
            str(telegram_id): asdict(user) 
            for telegram_id, user in self.users.items()
        }
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_user(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        return self.users.get(telegram_id)
    
    def create_user(self, telegram_id: int, full_name: str, phone: str, 
                   user_type: str, position: str = None, company_inn: str = None) -> User:
        """Создать нового пользователя"""
        user = User(
            telegram_id=telegram_id,
            full_name=full_name,
            phone=phone,
            user_type=user_type,
            position=position,
            company_inn=company_inn,
            registration_date=datetime.now().isoformat()
        )
        self.users[telegram_id] = user
        self.save_data()
        return user
    
    def update_user(self, telegram_id: int, **kwargs) -> Optional[User]:
        """Обновить данные пользователя"""
        user = self.users.get(telegram_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            self.save_data()
            return user
        return None
    
    def mark_user_registered(self, telegram_id: int, 
                           okdesk_contact_id: int = None, 
                           okdesk_company_id: int = None,
                           okdesk_issue_id: int = None):
        """Отметить пользователя как зарегистрированного"""
        user = self.users.get(telegram_id)
        if user:
            user.is_registered = True
            if okdesk_contact_id:
                user.okdesk_contact_id = okdesk_contact_id
            if okdesk_company_id:
                user.okdesk_company_id = okdesk_company_id
            if okdesk_issue_id:
                user.okdesk_issue_id = okdesk_issue_id
            self.save_data()
    
    def get_all_users(self) -> List[User]:
        """Получить всех пользователей"""
        return list(self.users.values())
    
    def is_user_registered(self, telegram_id: int) -> bool:
        """Проверить, зарегистрирован ли пользователь"""
        user = self.users.get(telegram_id)
        return user is not None and user.is_registered

# Глобальный экземпляр базы данных
db = Database()
