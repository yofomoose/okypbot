from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from config.db_config import Base  # Используем импорт из конфига
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    is_admin = Column(Boolean, default=False)
    is_trainer = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Classification(Base):
    __tablename__ = "classifications"
    
    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False)
    category = Column(String, nullable=False)
    confidence = Column(Float)
    created_by = Column(Integer, ForeignKey('users.telegram_id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_training = Column(Boolean, default=False)

class TrainingExample(Base):
    __tablename__ = "training_examples"
    
    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False)
    category = Column(String, nullable=False)
    added_by = Column(Integer, ForeignKey('users.telegram_id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    used_in_training = Column(Boolean, default=False)
