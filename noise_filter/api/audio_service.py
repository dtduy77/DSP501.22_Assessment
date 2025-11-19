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
    # Calculate absolute improvement in dB
    improvement_db = snr_after - snr_before
    
    # If input SNR is very low or negative, use absolute improvement
    if abs(snr_before) < 1:
        return round(improvement_db * 10, 2)  # Scale for better percentage
    
    # Otherwise calculate percentage improvement
    improvement = ((snr_after - snr_before) / abs(snr_before)) * 100
    return round(improvement, 2)


def calculate_snr_improvement(original, enhanced):
    """Calculate SNR improvement between original and enhanced signal"""
    # Estimate noise as the difference between original and enhanced
    noise_estimate = original - enhanced
    
    # Calculate power of signal and noise
    signal_power = np.mean(enhanced ** 2)
    noise_power = np.mean(noise_estimate ** 2) + 1e-12
    
    # Calculate SNR in dB
    snr = 10 * np.log10(signal_power / noise_power)
    return snr


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
    
    # If no noise reference provided, use last 1 second as noise
    if noise_ref_path is None:
        sr = 16000
        noise_ref = noisy[-sr:]  # Last 1 second
    else:
        noise_ref = load_wav(noise_ref_path)
    
    results = {}
    
    # Calculate baseline SNR (original noisy signal)
    # Estimate noise from noise reference
    noise_power = np.mean(noise_ref ** 2) + 1e-12
    signal_power = np.mean(noisy ** 2)
    snr_input = 10 * np.log10(signal_power / noise_power)
    
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
    
    # Ensure same length as input
    min_len = min(len(noisy), len(wiener_output))
    wiener_output = wiener_output[:min_len]
    noisy_aligned = noisy[:min_len]
    
    # Calculate SNR for Wiener output
    snr_wiener = calculate_snr_improvement(noisy_aligned, wiener_output)
    
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
    
    # Ensure same length as input
    min_len = min(len(noisy), len(mmse_output))
    mmse_output = mmse_output[:min_len]
    
    snr_mmse = calculate_snr_improvement(noisy_aligned, mmse_output)
    
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
        combined_output = wiener_output
        combined_method = "wiener_smooth"
        snr_combined = snr_wiener
    else:
        combined_output = mmse_output
        combined_method = "mmse_lsa"
        snr_combined = snr_mmse
    
    combined_time = time.time() - start_time
    
    results['combined'] = {
        'output': wiener_output,
        'improvement_percent': calculate_improvement(snr_input, snr_combined),
        'performance': calculate_performance(snr_combined),
        'time_seconds': round(combined_time, 3),
        'selected_method': combined_method  # Track which filter was selected
    }
    
    # Save processed file (combined as best result)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    file_basename = Path(file_path).stem
    processed_file_path = output_path / f"{file_basename}_processed1.wav"
    save_audio_file(combined_output, str(processed_file_path))
    
    results['original_path'] = file_path
    results['processed_path'] = str(processed_file_path)
    
    return results
