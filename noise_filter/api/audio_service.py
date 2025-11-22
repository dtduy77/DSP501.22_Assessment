import librosa
import numpy as np
import time
import soundfile as sf
from pathlib import Path
import sys
import shutil

# Add parent directory to path to import filters
sys.path.append(str(Path(__file__).parent.parent))

from filter.wiener_smooth_filter import wiener_smooth
from filter.mmse_lsa import mmse_lsa
from utils.audio_io import load_wav
from utils.metrics import snr_db


def add_white_noise(clean_path, snr_db=20, sr=16000):
    
    clean_path_obj = Path(clean_path)
    # Save noisy file to noise_filter/uploads, add timestamp
    uploads_dir = Path(__file__).parent.parent / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    noisy_path = str(uploads_dir / f"{clean_path_obj.stem}_noisy_{timestamp}{clean_path_obj.suffix}")
    
    # Load clean audio
    music, _ = librosa.load(clean_path, sr=sr, mono=True)
    L = len(music)

    # Generate white noise
    white = np.random.randn(L)

    # Scale noise theo SNR
    P_music = np.mean(music**2)
    P_noise = np.mean(white**2)
    k = np.sqrt(P_music / (P_noise * 10**(snr_db/10)))
    white_scaled = white * k

    # Tạo noisy signal
    noisy = music + white_scaled
    noisy /= np.max(np.abs(noisy))

    # Save noisy file
    sf.write(noisy_path, noisy, sr)
    return noisy_path


def calculate_improvement(snr_before, snr_after):
    """Calculate improvement percentage"""
    improvement = ((snr_after - snr_before) / abs(snr_before)) * 100
    return round(improvement, 2)



def calculate_performance(snr_after):
    """Calculate performance score (normalized 0-1)"""
    # Map SNR to 0-1 range (assume SNR range -10 to 30 dB)
    min_snr = -10
    max_snr = 30
    performance = (snr_after - min_snr) / (max_snr - min_snr)
    performance = max(0, min(1, performance))  # Clip to [0, 1]
    return round(performance, 2)


def save_audio_file(audio_data, output_path, sr=16000):
    """Save audio data to file"""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    sf.write(output_path, audio_data, sr)
    return output_path


def process_audio_file(clean_path: str, output_dir: str, snr_for_noise: float = 20, sr: int = 16000):

    # Tạo noisy từ clean
    # Tạo timestamp cho mọi file output
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    noisy_path = add_white_noise(clean_path, snr_db=snr_for_noise, sr=sr)

    # Load lại dữ liệu
    clean = load_wav(clean_path)
    noisy = load_wav(noisy_path)

    # Align clean and noisy lengths for evaluation
    min_len_eval = min(len(clean), len(noisy))
    clean = clean[:min_len_eval]
    noisy = noisy[:min_len_eval]

    results = {}

    # Calculate baseline SNR (original noisy signal) using clean reference
    snr_input = snr_db(clean, noisy)
    
    # === WIENER SMOOTH FILTER ===
    start_time = time.time()
    wiener_output = wiener_smooth(
        noisy,
        sr=16000,
        n_fft=1024,
        hop_length=256,
        alpha=0.98,
        noise_percentile=20.0
    )
    wiener_time = time.time() - start_time

    # Calculate SNR for Wiener output using clean reference
    snr_wiener = snr_db(clean, wiener_output)
    
    results['wiener'] = {
        'output': wiener_output,
        'improvement_percent': calculate_improvement(snr_input, snr_wiener),
        'performance': calculate_performance(snr_wiener),
        'time_seconds': round(wiener_time, 3)
    }
    
    # === MMSE-LSA FILTER ===
    start_time = time.time()
    mmse_output = mmse_lsa(
        noisy,
        sr=16000,
        n_fft=1024,
        hop_length=256,
        alpha=0.98,
        noise_percentile=20.0
    )
    mmse_time = time.time() - start_time

    snr_mmse = snr_db(clean, mmse_output)
    
    results['mmse'] = {
        'output': mmse_output,
        'improvement_percent': calculate_improvement(snr_input, snr_mmse),
        'performance': calculate_performance(snr_mmse),
        'time_seconds': round(mmse_time, 3)
    }
    
    # === BEST FILTER ===
    # Compare Wiener Smooth and MMSE-LSA, select the better one
    start_time = time.time()
    
    # Select the filter with better SNR
    if snr_wiener > snr_mmse:
        best_output = wiener_output
        best_method = "wiener_smooth"
        snr_best = snr_wiener
        best_time = wiener_time
    else:
        best_output = mmse_output
        best_method = "mmse_lsa"
        snr_best = snr_mmse
        best_time = mmse_time
    
    results['best'] = {
        'output': best_output,
        'improvement_percent': calculate_improvement(snr_input, snr_best),
        'performance': calculate_performance(snr_best),
        'time_seconds': round(best_time, 3),
        'selected_method': best_method  # Track which filter was selected
    }
    
    # Save processed file (combined as best result)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    file_basename = Path(clean_path).stem
    # Lưu file enhance (processed) với timestamp
    processed_file_path = output_path / f"{file_basename}_processed_{timestamp}.wav"
    save_audio_file(best_output, str(processed_file_path))

    results['original_path'] = clean_path
    results['processed_path'] = str(processed_file_path)
    results['noisy_path'] = noisy_path

    return results
