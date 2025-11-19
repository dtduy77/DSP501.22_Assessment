import librosa
import numpy as np
import soundfile as sf

SR = 16000

def load(path):
    x, _ = librosa.load(path, sr=SR, mono=True)
    return x

# ========= LOAD CLEAN MUSIC =========
music = load("music_clean_1.wav")
L = len(music)

# ========= GENERATE WHITE NOISE =========
white = np.random.randn(L)   # noise gaussian N(0,1)

# ========= SCALE THEO SNR MUỐN ============ 
SNR_DB = 20

P_music = np.mean(music**2)
P_noise = np.mean(white**2)
k = np.sqrt(P_music / (P_noise * 10**(SNR_DB/10)))

white_scaled = white * k

# ========= TẠO NOISY SIGNAL =========
noisy = music + white_scaled
noisy /= np.max(np.abs(noisy))

# ========= SAVE =========
sf.write("music_noisy_1.wav", noisy, SR)
sf.write("noise_white.wav", white_scaled, SR)

print("DONE → music_noisy_1.wav (white noise)")