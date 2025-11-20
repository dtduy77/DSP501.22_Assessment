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


def process_audio_file(file_path: str, output_dir: str, noise_ref_path: str = None):
    """
    Process audio file with all three methods
    Saves processed files and returns paths
    """
    # Load audio
    noisy = load_wav(file_path)

    # Load clean reference used for evaluation (test dataset)
    # Use absolute path relative to this file's location
    current_dir = Path(__file__).parent.parent
    clean_ref_path = current_dir / "data" / "music_clean_1.wav"
    clean = load_wav(str(clean_ref_path))

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
    
    file_basename = Path(file_path).stem
    processed_file_path = output_path / f"{file_basename}_processed1.wav"
    save_audio_file(best_output, str(processed_file_path))
    
    results['original_path'] = file_path
    results['processed_path'] = str(processed_file_path)
    
    return results
