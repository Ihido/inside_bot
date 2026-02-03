from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os
from config import Config

Base = declarative_base()

class Submission(Base):
    __tablename__ = 'submissions'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, nullable=False)
    user_info = Column(Text, nullable=False)
    content_type = Column(String(20), nullable=False)  # photo/video/text
    caption = Column(Text, nullable=True)
    media_path = Column(String(500), nullable=True)
    status = Column(String(20), default='pending')
    submission_date = Column(DateTime, default=datetime.datetime.utcnow)
    admin_comment = Column(Text, nullable=True)

class Admin(Base):
    __tablename__ = 'admins'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)

# Инициализация БД
engine = create_engine(f'sqlite:///{os.path.join(Config.DATA_DIR, "database.db")}')
Base.metadata.create_all(engine)

# Создаем фабрику сессий
SessionLocal = sessionmaker(bind=engine)

# Функция для получения сессии
def get_session():
    """Создает и возвращает новую сессию БД"""
    return SessionLocal()