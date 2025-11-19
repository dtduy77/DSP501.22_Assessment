# file: run_wiener_smooth.py

from utils.audio_io import load_wav, save
from utils.metrics import snr_db
from filter.wiener_smooth_filter import wiener_smooth

# ==============================
# 1. LOAD
# ==============================
clean = load_wav("data/music_clean_1.wav")
noisy = load_wav("data/music_noisy_1.wav")

min_len = min(len(clean), len(noisy))
clean = clean[:min_len]
noisy = noisy[:min_len]

# ==============================
# 2. WIENER SMOOTH
# ==============================
enhanced = wiener_smooth(
    noisy,
    sr=16000,
    n_fft=1024,
    hop_length=256,
    alpha=0.98,
    noise_percentile=20.0,  # có thể thử 10–30
)

# ==============================
# 3. SNR
# ==============================
print("SNR input :", snr_db(clean, noisy))
print("SNR MMSE  :", snr_db(clean, enhanced))

# ==============================
# 4. SAVE
# ==============================
save("results/wiener_smooth_output_1.wav", enhanced)
print("DONE → results/wiener_smooth_output_1.wav")