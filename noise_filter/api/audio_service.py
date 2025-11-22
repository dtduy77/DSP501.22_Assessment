import os
import librosa
import numpy as np
import time
import soundfile as sf
from pathlib import Path
import sys
import shutil

# Add parent directory to path to import filters and utilities
# Thao tác này đảm bảo Python tìm thấy các module như filter.wiener_smooth_filter
sys.path.append(str(Path(__file__).parent.parent))
from detect.detect_song import detect_song

from filter.wiener_smooth_filter import wiener_smooth
from filter.mmse_lsa import mmse_lsa
from utils.audio_io import load_wav
from utils.metrics import snr_db

SR = 16000  # Tần số lấy mẫu mặc định


# ==========================================================
# 1. HÀM TẠO NHIỄU (ADD NOISE)
# ==========================================================
def add_white_noise(clean_path, snr_db=20, sr=SR):
    """
    Tạo tín hiệu nhiễu trắng từ tín hiệu sạch (clean_path).
    Lưu tín hiệu nhiễu TẠM THỜI vào thư mục uploads/ để sử dụng trong quá trình xử lý.
    """
    clean_path_obj = Path(clean_path)
    current_dir = Path(__file__).parent

    # Đảm bảo thư mục uploads tồn tại
    uploads_dir = current_dir.parent / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # Tạo tên file nhiễu có timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    noisy_filename = f"{clean_path_obj.stem}_noisy_{timestamp}{clean_path_obj.suffix}"
    noisy_path = str(uploads_dir / noisy_filename)

    # Load clean audio
    music, _ = librosa.load(clean_path, sr=sr, mono=True)
    L = len(music)

    # Generate white noise (noise gaussian N(0,1))
    white = np.random.randn(L)

    # Scale noise theo SNR
    P_music = np.mean(music**2)
    P_noise = np.mean(white**2)
    k = np.sqrt(P_music / (P_noise * 10 ** (snr_db / 10)))
    white_scaled = white * k

    # Tạo noisy signal
    noisy = music + white_scaled
    # Chuẩn hóa về mức tối đa ±1
    noisy /= np.max(np.abs(noisy))

    # Save noisy file vào thư mục uploads/
    sf.write(noisy_path, noisy, sr)

    return noisy_path


# ==========================================================
# 2. HÀM TÍNH TOÁN VÀ ĐÁNH GIÁ
# ==========================================================


def calculate_improvement(snr_before, snr_after):
    """Calculate improvement percentage"""
    improvement = ((snr_after - snr_before) / abs(snr_before)) * 100
    return round(improvement, 2)


def calculate_performance(snr_after):
    """Calculate performance score (normalized 0-1)"""
    min_snr = -10
    max_snr = 30
    performance = (snr_after - min_snr) / (max_snr - min_snr)
    performance = max(0, min(1, performance))
    return round(performance, 2)


def save_audio_file(audio_data, output_path, sr=SR):
    """Save audio data to file"""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    sf.write(output_path, audio_data, sr)
    return output_path


def process_audio_file(
    clean_path: str, output_dir: str, snr_for_noise: float = 20, sr: int = SR
):
    """
    Tạo tín hiệu nhiễu từ clean_path, xử lý bằng Wiener/MMSE-LSA,
    và lưu lại file nhiễu, file đã lọc vào RESULTS_DIR.

    clean_path: Đường dẫn tới file sạch (file vừa được upload vào uploads/).
    output_dir: Thư mục results/.
    """
    song_name = None
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. TẠO FILE NHIỄU VÀ LƯU TẠM VÀO UPLOADS/
    noisy_path_in_uploads = add_white_noise(clean_path, snr_db=snr_for_noise, sr=sr)

    # 2. LOAD LẠI DỮ LIỆU ĐỂ XỬ LÝ
    clean = load_wav(clean_path)  # Tải file sạch (từ uploads/)
    noisy = load_wav(noisy_path_in_uploads)  # Tải file nhiễu (từ uploads/)

    # Align lengths
    min_len_eval = min(len(clean), len(noisy))
    clean = clean[:min_len_eval]
    noisy = noisy[:min_len_eval]

    results = {}
    snr_input = snr_db(clean, noisy)

    # --- WIENER SMOOTH FILTER ---
    start_time = time.time()
    wiener_output = wiener_smooth(
        noisy, sr=SR, n_fft=1024, hop_length=256, alpha=0.98, noise_percentile=20.0
    )
    wiener_time = time.time() - start_time
    snr_wiener = snr_db(clean, wiener_output)
    results["wiener"] = {
        "output": wiener_output,
        "improvement_percent": calculate_improvement(snr_input, snr_wiener),
        "performance": calculate_performance(snr_wiener),
        "time_seconds": round(wiener_time, 3),
    }

    # --- MMSE-LSA FILTER ---
    start_time = time.time()
    mmse_output = mmse_lsa(
        noisy, sr=SR, n_fft=1024, hop_length=256, alpha=0.98, noise_percentile=20.0
    )
    mmse_time = time.time() - start_time
    snr_mmse = snr_db(clean, mmse_output)
    results["mmse"] = {
        "output": mmse_output,
        "improvement_percent": calculate_improvement(snr_input, snr_mmse),
        "performance": calculate_performance(snr_mmse),
        "time_seconds": round(mmse_time, 3),
    }

    # --- BEST FILTER ---
    if snr_wiener > snr_mmse:
        best_output = wiener_output
        best_time = wiener_time
    else:
        best_output = mmse_output
        best_time = mmse_time

    snr_best = max(snr_wiener, snr_mmse)  # Tính lại SNR của bộ lọc tốt nhất
    results["best"] = {
        "output": best_output,
        "improvement_percent": calculate_improvement(snr_input, snr_best),
        "performance": calculate_performance(snr_best),
        "time_seconds": round(best_time, 3),
        "selected_method": "wiener_smooth" if snr_wiener > snr_mmse else "mmse_lsa",
    }

    # 3. LƯU TRỮ VÀ SAO LƯU FILE VÀO RESULTS/
    file_basename = Path(clean_path).stem

    # a) REMOVED: Không copy file CLEAN vào results/ (Nó ở lại clean_path trong uploads/)

    # b) Lưu file đã lọc (processed) vào results/
    processed_file_path = output_path / f"{file_basename}_processed_{timestamp}.wav"
    save_audio_file(best_output, str(processed_file_path))

    # Lấy tên bài hát bằng detect_song trên file enhance (processed)
    
    # processed_file_path đã là đường dẫn tuyệt đối, không cần join thêm
    result = detect_song(str(processed_file_path))

    # c) COPY file nhiễu (NOISY) từ uploads/ sang results/
    noisy_file_path_in_results = output_path / f"{file_basename}_noisy_{timestamp}.wav"
    shutil.copy2(noisy_path_in_uploads, noisy_file_path_in_results)

    # 4. CẬP NHẬT RESULTS DICTIONARY
    # results['clean_path'] chứa đường dẫn GỐC (trong uploads/)
    results["clean_path"] = clean_path
    results["processed_path"] = str(processed_file_path)
    results["noisy_path"] = str(noisy_file_path_in_results)
    # Đảm bảo song_name luôn là string hợp lệ
    if result and result.get('success', False):
        results['song_name'] = f"{result['title']} - {result['artist']}"
    else:
        results['song_name'] = result.get('message', 'Unknown Song') if result else 'Detection Failed'
    # 5. DỌN DẸP
    # Xóa file nhiễu tạm thời trong uploads/ (File sạch GỐC ở lại)
    Path(noisy_path_in_uploads).unlink(missing_ok=True)

    return results
