from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import shutil
from pathlib import Path
import os
import sys

# Imports chính thức từ các file cần thiết
from .models import ProcessAudioResponse, FilterInfo, HistoryItem
from .database import get_db, init_db, AudioProcessing  # Import AudioProcessing class
from .audio_service import process_audio_file  # Hàm dịch vụ

# Khởi tạo App
app = FastAPI(
    title="Audio Processing API",
    description="API for noise filtering using Wiener Smooth, MMSE-LSA, and Best filters",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload and results directories
# Sử dụng resolve() để đảm bảo đường dẫn tuyệt đối
UPLOAD_DIR = (Path(__file__).parent.parent / "uploads").resolve()
RESULTS_DIR = (Path(__file__).parent.parent / "results").resolve()
# Đảm bảo các thư mục tồn tại
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Mount static files for serving audio files
# Mount thư mục cha để truy cập cả uploads và results
app.mount("/audio", StaticFiles(directory=str(UPLOAD_DIR.parent)), name="audio")


@app.on_event("startup")
async def startup_event():
    init_db()  # Khởi tạo database


@app.get("/")
async def root():
    return {
        "message": "Audio Processing API",
        "endpoints": {
            "POST /file/process": "Process audio file",
            "GET /file/{id}": "Get processing details by ID",
            "GET /file": "Get processing history",
        },
    }


@app.post("/file/process", response_model=ProcessAudioResponse)
async def process_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Process an audio file with Wiener Smooth, MMSE-LSA, and Best filters

    - **file**: WAV audio file (expected to be CLEAN)

    Returns processing results with comparison metrics
    """
    # 1. Validate file type
    if not file.filename.endswith(".wav"):
        raise HTTPException(status_code=400, detail="Only WAV files are supported")

    # 2. Save uploaded file (This is the CLEAN file)
    clean_file_path = UPLOAD_DIR / file.filename
    try:
        # Khắc phục lỗi [Errno 2] bằng cách đảm bảo thư mục tồn tại
        clean_file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(clean_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    # 3. Process audio (Clean -> Add Noise -> Filter)
    try:
        # Truyền đường dẫn file sạch vừa upload vào hàm dịch vụ
        results = process_audio_file(str(clean_file_path), str(RESULTS_DIR))
    except Exception as e:
        # Xóa file sạch nếu xử lý lỗi (trong trường hợp dịch vụ không chạy được)
        # LƯU Ý: Nếu dịch vụ chạy OK, file sạch này sẽ được giữ lại theo yêu cầu.
        if clean_file_path.exists():
            print(
                f"Error processing audio: {e}. Attempting to keep clean file for debugging.",
                file=sys.stderr,
            )
            # Không xóa file sạch ở đây nếu có lỗi, để người dùng kiểm tra file uploads/
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")

    # 4. Generate URLs for audio files

    # Lấy đường dẫn file CLEAN GỐC (nằm trong uploads/)
    original_file_url = f"/audio/uploads/{file.filename}"

    # Lấy đường dẫn file đã lọc (Processed Output)
    processed_filename = Path(results["processed_path"]).name
    processed_url = f"/audio/results/{processed_filename}"

    # Calculate file size (using the original uploaded file size)
    file_size_kb = os.path.getsize(clean_file_path) / 1024

    # 5. Create database record
    db_record = AudioProcessing(
        song_name=file.filename,
        original_file=original_file_url,  # <-- FILE CLEAN GỐC (uploads/)
        processed_file=processed_url,
        file_size_kb=round(file_size_kb, 2),
        filter_a_improvement=results["wiener"]["improvement_percent"],
        filter_a_performance=results["wiener"]["performance"],
        filter_a_time=results["wiener"]["time_seconds"],
        filter_b_improvement=results["mmse"]["improvement_percent"],
        filter_b_performance=results["mmse"]["performance"],
        filter_b_time=results["mmse"]["time_seconds"],
        best_improvement=results["best"]["improvement_percent"],
        best_performance=results["best"]["performance"],
        best_time=results["best"]["time_seconds"],
    )

    db.add(db_record)
    db.commit()  # Commit vào DB thật
    db.refresh(db_record)

    # 6. Build response
    response = ProcessAudioResponse(
        id=db_record.id,
        song_name=db_record.song_name,
        original_file=db_record.original_file,  # URL file CLEAN
        processed_file=db_record.processed_file,
        file_size_kb=db_record.file_size_kb,
        date_process=db_record.date_process,
        comparison={
            "wiener_smooth": FilterInfo(
                improvement_percent=db_record.filter_a_improvement,
                performance=db_record.filter_a_performance,
                time_seconds=db_record.filter_a_time,
            ),
            "mmse_lsa": FilterInfo(
                improvement_percent=db_record.filter_b_improvement,
                performance=db_record.filter_b_performance,
                time_seconds=db_record.filter_b_time,
            ),
            "best": FilterInfo(
                improvement_percent=db_record.best_improvement,
                performance=db_record.best_performance,
                time_seconds=db_record.best_time,
            ),
        },
    )

    # 7. Dọn dẹp: BỎ QUA việc xóa file sạch đã upload
    # File sạch (clean_file_path) sẽ được giữ lại trong thư mục uploads/

    return response


@app.get("/file/{file_id}", response_model=ProcessAudioResponse)
async def get_file_detail(file_id: int, db: Session = Depends(get_db)):
    """
    Get detailed processing information by ID

    - **file_id**: ID of the processed file
    """
    record = db.query(AudioProcessing).filter(AudioProcessing.id == file_id).first()

    if not record:
        raise HTTPException(status_code=404, detail="File not found")

    response = ProcessAudioResponse(
        id=record.id,
        song_name=record.song_name,
        original_file=record.original_file,
        processed_file=record.processed_file,
        file_size_kb=record.file_size_kb,
        date_process=record.date_process,
        comparison={
            "wiener_smooth": FilterInfo(
                improvement_percent=record.filter_a_improvement,
                performance=record.filter_a_performance,
                time_seconds=record.filter_a_time,
            ),
            "mmse_lsa": FilterInfo(
                improvement_percent=record.filter_b_improvement,
                performance=record.filter_b_performance,
                time_seconds=record.filter_b_time,
            ),
            "best": FilterInfo(
                improvement_percent=record.best_improvement,
                performance=record.best_performance,
                time_seconds=record.best_time,
            ),
        },
    )

    return response


@app.get("/file", response_model=List[HistoryItem])
async def get_file_history(db: Session = Depends(get_db)):
    """
    Get all processing history

    Returns list of all processed files with basic information
    """
    records = (
        db.query(AudioProcessing).order_by(AudioProcessing.date_process.desc()).all()
    )

    history = [
        HistoryItem(
            id=record.id, song_name=record.song_name, date_process=record.date_process
        )
        for record in records
    ]

    return history
