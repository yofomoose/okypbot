from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .base import Base

class EncryptedData(Base):
    __tablename__ = "encrypted_data"

    id = Column(Integer, primary_key=True)
    data_type = Column(String, nullable=False)
    encrypted_content = Column(String, nullable=False)
    user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
