import librosa
import soundfile as sf
import numpy as np
from pathlib import Path

SR = 16000

def load_wav(path, sr=SR):
    x, _ = librosa.load(path, sr=sr, mono=True)
    x = x / (np.max(np.abs(x)) + 1e-9)
    return x

def mix_clean_noise(clean, noise, snr_db=0):
    if len(noise) < len(clean):
        rep = int(np.ceil(len(clean)/len(noise)))
        noise = np.tile(noise, rep)

    noise = noise[:len(clean)]

    P_clean = np.mean(clean**2)
    P_noise = np.mean(noise**2)

    k = np.sqrt(P_clean / (P_noise * 10**(snr_db/10)))
    noisy = clean + noise * k

    noisy = noisy / (np.max(np.abs(noisy)) + 1e-9)

    return noisy, noise * k, clean

def load_and_mix(clean_path="data/clean.wav",
                 noise_path="data/noise.wav",
                 snr_db=0):

    clean = load_wav(clean_path)
    noise = load_wav(noise_path)

    noisy, noise_scaled, clean = mix_clean_noise(clean, noise, snr_db)

    return clean, noise_scaled, noisy

def save(path, wav, sr=SR):
    Path(path).parent.mkdir(exist_ok=True)
    sf.write(path, wav, sr)
