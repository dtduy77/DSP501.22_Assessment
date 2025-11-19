# file: run_mmse_lsa.py

from utils.audio_io import load_wav, save
from utils.metrics import snr_db
from filter.mmse_lsa import mmse_lsa

# ==============================
# 1. LOAD
# ==============================
clean = load_wav("data/music_clean_1.wav")
noisy = load_wav("data/music_noisy_1.wav")

min_len = min(len(clean), len(noisy))
clean = clean[:min_len]
noisy = noisy[:min_len]

# ==============================
# 2. MMSE - LSA (Log-Spectral Amplitude)
# ==============================
# Lưu ý: LSA lọc nhạc tốt hơn nên mình để percentile thấp (10) để giữ chi tiết
enhanced = mmse_lsa(
    noisy,
    sr=16000,
    n_fft=1024,
    hop_length=256,
    alpha=0.98,
    noise_percentile=20.0
)

# ==============================
# 3. SNR
# ==============================
print("SNR input :", snr_db(clean, noisy))
print("SNR LSA   :", snr_db(clean, enhanced))

# ==============================
# 4. SAVE
# ==============================
save("results/lsa_output_1.wav", enhanced)
print("DONE → results/lsa_output_1.wav")