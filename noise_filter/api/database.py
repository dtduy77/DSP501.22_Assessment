from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import Generator

from pathlib import Path

# Xác định đường dẫn tuyệt đối tới file database
# File database sẽ được đặt ở thư mục gốc của dự án (cùng cấp với noise_filter)
db_path = Path(__file__).parent.parent / "audio_processing.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path.resolve()}"

# Khởi tạo Engine, thiết lập connect_args cho SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class AudioProcessing(Base):
    """Bảng lưu trữ kết quả xử lý âm thanh"""

    __tablename__ = "audio_processing"

    id = Column(Integer, primary_key=True, index=True)
    song_name = Column(String, index=True)
    # Lưu URL tĩnh của file nhiễu (original_file)
    original_file = Column(Text)
    # Lưu URL tĩnh của file đã lọc (processed_file)
    processed_file = Column(Text)
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
    """Tạo tất cả các bảng nếu chúng chưa tồn tại"""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator:
    """Dependency để cung cấp phiên làm việc (Session) của database"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
