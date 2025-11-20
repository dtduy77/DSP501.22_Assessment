from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./audio_processing.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class AudioProcessing(Base):
    __tablename__ = "audio_processing"

    id = Column(Integer, primary_key=True, index=True)
    song_name = Column(String, index=True)
    original_file = Column(Text)  # Base64 or file path
    processed_file = Column(Text)  # Base64 or file path
    file_size_kb = Column(Float)
    date_process = Column(DateTime, default=datetime.now)
    
    # Filter A (Wiener Smooth)
    filter_a_improvement = Column(Float)
    filter_a_performance = Column(Float)
    filter_a_time = Column(Float)
    
    # Filter B (MMSE-LSA)
    filter_b_improvement = Column(Float)
    filter_b_performance = Column(Float)
    filter_b_time = Column(Float)
    
    # Best (Auto-select best filter)
    best_improvement = Column(Float)
    best_performance = Column(Float)
    best_time = Column(Float)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
