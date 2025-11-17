from utils.audio_io import load_wav, save
from utils.metrics import snr_db
from filter.wiener_filter import wiener_filter_spectral

# ==============================
# 1️ LOAD FILE
# ==============================
clean = load_wav("data/music_clean.wav")
noisy = load_wav("data/music_noisy.wav")
noise_ref = load_wav("data/music_noise.wav")

# Đồng bộ chiều dài
min_len = min(len(clean), len(noisy))
clean = clean[:min_len]
noisy = noisy[:min_len]


# ==============================
# 2️ WIENER FILTER
# ==============================
enhanced = wiener_filter_spectral(noisy, noise_ref)

# ==============================
# 3️ HIỂN THỊ SNR
# ==============================
print("SNR input :", snr_db(clean, noisy))
print("SNR Wiener:", snr_db(clean, enhanced))

# ==============================
# 4️SAVE
# ==============================
save("results/wiener_output.wav", enhanced)
print("DONE → results/wiener_output.wav")
