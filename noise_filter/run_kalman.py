from utils.audio_io import load_wav, save
from utils.metrics import snr_db
from filter.kalman_filter import spectral_kalman   
import numpy as np

# ==============================
# LOAD FILE
# ==============================
clean = load_wav("data/music_clean.wav")
noisy = load_wav("data/music_noisy.wav")
noise_ref = load_wav("data/music_noise.wav")


min_len = min(len(clean), len(noisy))
clean     = clean[:min_len]
noisy     = noisy[:min_len]



enhanced = spectral_kalman(noisy, noise_ref)

# ==============================
# HIỂN THỊ SNR
# ==============================
print("SNR input :", snr_db(clean, noisy))
print("SNR Kalman:", snr_db(clean, enhanced))

# ==============================
# SAVE
# ==============================
save("results/kalman_output.wav", enhanced)
print("DONE → results/kalman_output.wav")
