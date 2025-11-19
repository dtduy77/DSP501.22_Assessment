import numpy as np
import librosa

SR = 16000
N_FFT = 1024
HOP = 256

def wiener_filter_no_ref(noisy, sr=SR, beta=0.5, noise_percentile=20):
    """
    Wiener Filter không cần noise_ref.
    Noise PSD được ước lượng từ chính noisy bằng Minimum-Statistics (percentile).
    """

    eps = 1e-12

    # ===== 1. STFT =====
    Y = librosa.stft(noisy, n_fft=N_FFT, hop_length=HOP)
    Y_mag = np.abs(Y)
    Y_phase = np.angle(Y)
    Y_power = Y_mag ** 2

    # ===== 2. Noise PSD estimation bằng percentile =====
    # Lấy 20th percentile ở mỗi frequency bin
    noise_psd = np.percentile(Y_power, noise_percentile, axis=1, keepdims=True)
    noise_psd = np.maximum(noise_psd, eps)

    # ===== 3. Wiener Gain =====
    SNR_est = np.maximum(Y_power / (noise_psd + eps) - 1, 0)
    G = (SNR_est / (SNR_est + 1 + eps)) ** beta

    # Chặn giá trị gain để không gây méo
    G = np.clip(G, 0.02, 1.0)

    # ===== 4. Apply Gain =====
    X_hat = G * Y_mag
    S_hat = X_hat * np.exp(1j * Y_phase)

    # ===== 5. ISTFT =====
    enhanced = librosa.istft(S_hat, hop_length=HOP)
    enhanced = enhanced / (np.max(np.abs(enhanced)) + eps)

    return enhanced
