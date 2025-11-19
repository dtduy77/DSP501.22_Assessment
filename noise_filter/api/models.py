from pydantic import BaseModel
from typing import Dict
from datetime import datetime


class FilterInfo(BaseModel):
    improvement_percent: float
    performance: float
    time_seconds: float


class ProcessAudioResponse(BaseModel):
    id: int
    song_name: str
    original_file: str  # URL path to original file
    processed_file: str  # URL path to processed file
    file_size_kb: float
    date_process: datetime
    comparison: Dict[str, FilterInfo]


class HistoryItem(BaseModel):
    id: int
    song_name: str
    date_process: datetime
