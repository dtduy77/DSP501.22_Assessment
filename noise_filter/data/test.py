import librosa
import soundfile as sf
import numpy as np

SR = 16000

def load(path):
    x, _ = librosa.load(path, sr=SR, mono=True)
    return x / (np.max(np.abs(x)) + 1e-9)

music = load("music_clean.wav")   
noise = load("music_noise.wav")  


if len(noise) < len(music):
    noise = np.tile(noise, int(np.ceil(len(music)/len(noise))))
noise = noise[:len(music)]

# Chỉnh mức SNR
SNR_DB = 10
P_music = np.mean(music**2)
P_noise = np.mean(noise**2)
k = np.sqrt(P_music / (P_noise * 10**(SNR_DB/10)))
noise_scaled = noise * k

noisy = music + noise_scaled
noisy /= np.max(np.abs(noisy))

sf.write("music_noisy.wav", noisy, SR)
sf.write("music_noise_scaled.wav", noise_scaled, SR)

print(" DONE → đã tạo music_noisy + noise_scaled")

