# file: run_mmse_stsa_stable.py

from utils.audio_io import load_wav, save
from utils.metrics import snr_db
from filter.mmse_stsa_stable import mmse_stsa_stable

# ==============================
# 1. LOAD
# ==============================
clean = load_wav("data/music_clean_1.wav")
noisy = load_wav("data/music_noisy_1.wav")

min_len = min(len(clean), len(noisy))
clean = clean[:min_len]
noisy = noisy[:min_len]

# ==============================
# 2. MMSE-STSA (stable)
# ==============================
enhanced = mmse_stsa_stable(
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
save("results/mmse_stsa_stable_output_1.wav", enhanced)
print("DONE → results/mmse_stsa_stable_output_1.wav")