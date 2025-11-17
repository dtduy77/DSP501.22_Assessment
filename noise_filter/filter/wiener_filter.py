import numpy as np
import librosa

SR = 16000
N_FFT = 1024
HOP = 256

def wiener_filter_spectral(noisy, noise_ref, sr=SR):

    # ===== STFT =====
    Y = librosa.stft(noisy, n_fft=N_FFT, hop_length=HOP)
    Y_mag = np.abs(Y)
    Y_phase = np.angle(Y)

    # ===== PSD Noise =====
    N = librosa.stft(noise_ref, n_fft=N_FFT, hop_length=HOP)
    noise_psd = np.mean(np.abs(N)**2, axis=1, keepdims=True)

    # ===== Wiener Gain =====
    Y_power = Y_mag**2
    SNR_est = np.maximum(Y_power/(noise_psd + 1e-12) - 1, 0)
    G = SNR_est / (SNR_est + 1)

    # ===== Apply Gain =====
    X_hat = G * Y_mag
    S_hat = X_hat * np.exp(1j * Y_phase)

    enhanced = librosa.istft(S_hat, hop_length=HOP)
    enhanced = enhanced / (np.max(np.abs(enhanced)) + 1e-9)

    return enhanced
