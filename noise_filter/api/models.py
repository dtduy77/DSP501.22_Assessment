from pydantic import BaseModel
from typing import Dict
from datetime import datetime


class FilterInfo(BaseModel):
    """Chi tiết hiệu suất của một bộ lọc (Wiener/MMSE)"""

    improvement_percent: float
    performance: float
    time_seconds: float


class ProcessAudioResponse(BaseModel):
    """Mô hình phản hồi chi tiết sau khi xử lý một file"""

    id: int
    song_name: str
    original_file: str  # URL path tới file nhiễu (INPUT)
    processed_file: str  # URL path tới file đã lọc (OUTPUT)
    file_size_kb: float
    date_process: datetime
    comparison: Dict[str, FilterInfo]


class HistoryItem(BaseModel):
    """Mô hình phản hồi rút gọn cho lịch sử xử lý"""

    id: int
    song_name: str
    date_process: datetime
