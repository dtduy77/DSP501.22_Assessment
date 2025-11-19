from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import shutil
from pathlib import Path
import os

from .models import ProcessAudioResponse, FilterInfo, HistoryItem
from .database import get_db, init_db, AudioProcessing
from .audio_service import process_audio_file

app = FastAPI(
    title="Audio Processing API",
    description="API for noise filtering using Wiener Smooth, MMSE-LSA, and Best filters",
    version="1.0.0"
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
UPLOAD_DIR = Path("uploads")
RESULTS_DIR = Path("results")
UPLOAD_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# Mount static files for serving audio files
app.mount("/audio", StaticFiles(directory=str(UPLOAD_DIR.parent)), name="audio")


@app.on_event("startup")
async def startup_event():
    init_db()


@app.get("/")
async def root():
    return {
        "message": "Audio Processing API",
        "endpoints": {
            "POST /file/process": "Process audio file",
            "GET /file/{id}": "Get processing details by ID",
            "GET /file": "Get processing history"
        }
    }


@app.post("/file/process", response_model=ProcessAudioResponse)
async def process_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Process an audio file with Wiener Smooth, MMSE-LSA, and Best filters
    
    - **file**: WAV audio file to process
    
    Returns processing results with comparison metrics
    """
    # Validate file type
    if not file.filename.endswith('.wav'):
        raise HTTPException(status_code=400, detail="Only WAV files are supported")
    
    # Save uploaded file
    file_path = UPLOAD_DIR / file.filename
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    # Process audio
    try:
        results = process_audio_file(str(file_path), str(RESULTS_DIR))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")
    
    # Generate URLs for audio files
    original_url = f"/audio/uploads/{file.filename}"
    processed_filename = Path(results['processed_path']).name
    processed_url = f"/audio/results/{processed_filename}"
    
    # Calculate file size
    file_size_kb = os.path.getsize(file_path) / 1024
    
    # Create database record
    db_record = AudioProcessing(
        song_name=file.filename,
        original_file=original_url,
        processed_file=processed_url,
        file_size_kb=round(file_size_kb, 2),
        filter_a_improvement=results['wiener']['improvement_percent'],
        filter_a_performance=results['wiener']['performance'],
        filter_a_time=results['wiener']['time_seconds'],
        filter_b_improvement=results['mmse']['improvement_percent'],
        filter_b_performance=results['mmse']['performance'],
        filter_b_time=results['mmse']['time_seconds'],
        combine_improvement=results['combined']['improvement_percent'],
        combine_performance=results['combined']['performance'],
        combine_time=results['combined']['time_seconds']
    )
    
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    
    # Build response
    response = ProcessAudioResponse(
        id=db_record.id,
        song_name=db_record.song_name,
        original_file=db_record.original_file,
        processed_file=db_record.processed_file,
        file_size_kb=db_record.file_size_kb,
        date_process=db_record.date_process,
        comparison={
            "wiener_smooth": FilterInfo(
                improvement_percent=db_record.filter_a_improvement,
                performance=db_record.filter_a_performance,
                time_seconds=db_record.filter_a_time
            ),
            "mmse_lsa": FilterInfo(
                improvement_percent=db_record.filter_b_improvement,
                performance=db_record.filter_b_performance,
                time_seconds=db_record.filter_b_time
            ),
            "best": FilterInfo(
                improvement_percent=db_record.combine_improvement,
                performance=db_record.combine_performance,
                time_seconds=db_record.combine_time
            )
        }
    )
    
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
                time_seconds=record.filter_a_time
            ),
            "mmse_lsa": FilterInfo(
                improvement_percent=record.filter_b_improvement,
                performance=record.filter_b_performance,
                time_seconds=record.filter_b_time
            ),
            "best": FilterInfo(
                improvement_percent=record.combine_improvement,
                performance=record.combine_performance,
                time_seconds=record.combine_time
            )
        }
    )
    
    return response


@app.get("/file", response_model=List[HistoryItem])
async def get_file_history(db: Session = Depends(get_db)):
    """
    Get all processing history
    
    Returns list of all processed files with basic information
    """
    records = db.query(AudioProcessing).order_by(AudioProcessing.date_process.desc()).all()
    
    history = [
        HistoryItem(
            id=record.id,
            song_name=record.song_name,
            date_process=record.date_process
        )
        for record in records
    ]
    
    return history
