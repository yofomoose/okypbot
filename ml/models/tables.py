from sqlalchemy import Column, Integer, BigInteger, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from config.db_config import Base  # Используем импорт из конфига
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True)
    is_admin = Column(Boolean, default=False)
    is_trainer = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Classification(Base):
    __tablename__ = "classifications"
    
    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False)
    predicted_category = Column(String, nullable=False)  # Изменено с category на predicted_category
    confidence = Column(Float)
    user_id = Column(BigInteger)  # Изменено с telegram_user_id на user_id для совместимости
    telegram_user_id = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_training = Column(Boolean, default=False)
    
    # Поля для обратной связи
    is_correct = Column(Boolean, nullable=True)
    correct_category = Column(String, nullable=True)
    feedback_at = Column(DateTime, nullable=True)
    
    # Техническая информация
    model_version = Column(String, nullable=True)
    processing_time = Column(Float, nullable=True)

class TrainingExample(Base):
    __tablename__ = "training_examples"
    
    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False)
    category = Column(String, nullable=False)
    added_by = Column(Integer, ForeignKey('users.telegram_id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    used_in_training = Column(Boolean, default=False)
