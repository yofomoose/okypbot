from sqlalchemy import Column, Integer, String, DateTime
from .base import Base

class ActionLog(Base):
    __tablename__ = "action_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    action_type = Column(String, nullable=False)
    details = Column(String)
    timestamp = Column(DateTime, nullable=False)
