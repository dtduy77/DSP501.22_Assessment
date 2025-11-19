# file: filter/mmse_lsa.py

import numpy as np
import librosa
import scipy.special as sp  # Cần cái này để tính hàm mũ tích phân

SR = 16000
N_FFT = 1024
HOP = 256

def mmse_lsa(
    noisy: np.ndarray,
    sr: int = SR,
    n_fft: int = N_FFT,
    hop_length: int = HOP,
    alpha: float = 0.98,          # Decision-directed factor
    noise_percentile: float = 20  
) -> np.ndarray:
    """
    MMSE-LSA (Log-Spectral Amplitude) Estimator:
    - Tối ưu hóa sai số trên miền Logarit (gần với thính giác người hơn).
    - Công thức Gain: G = (xi / (1+xi)) * exp(0.5 * integral_exponential(v))
    - Cho kết quả tự nhiên hơn, ít residual noise hơn Wiener.
    """

    eps = 1e-12

    # ===== 1. STFT =====
    Y = librosa.stft(noisy, n_fft=n_fft, hop_length=hop_length)
    Y_mag = np.abs(Y)
    Y_phase = np.angle(Y)
    Y_pow = Y_mag ** 2
    n_freq, n_frames = Y_pow.shape

    # ===== 2. Ước lượng PSD noise (Minimum Statistics) =====

    noise_psd = np.percentile(Y_pow, noise_percentile, axis=1, keepdims=True)
    noise_psd = np.maximum(noise_psd, eps)

    # ===== 3. Khởi tạo biến =====
    prior_snr = np.zeros_like(Y_pow)
    post_snr = np.zeros_like(Y_pow)
    G = np.zeros_like(Y_mag)
    
    # Các hằng số giới hạn để thuật toán ổn định
    G_MIN = 0.05 # -26dB gain floor
    
    # ===== 4. Vòng lặp xử lý từng frame =====
    for t in range(n_frames):
        # --- a. Posterior SNR (gamma) ---
        current_pow = Y_pow[:, t:t+1]
        post_t = current_pow / (noise_psd + eps)
        post_t = np.clip(post_t, 0.0, 100.0) # Clip trần để tránh tràn số

        # --- b. A Priori SNR (xi) - Decision Directed ---
        if t == 0:
            prior_t = np.maximum(post_t - 1.0, 0.0)
        else:
            # Công thức Decision-Directed kinh điển
            prior_t = (
                alpha * (G[:, t-1:t] ** 2) * post_snr[:, t-1:t]
                + (1.0 - alpha) * np.maximum(post_t - 1.0, 0.0)
            )
        
        prior_t = np.maximum(prior_t, eps)

        # --- c. Tính Gain theo công thức LSA ---
        # v = (xi / (1+xi)) * gamma
        v = (prior_t / (1.0 + prior_t)) * post_t
        v = np.maximum(v, eps) # Tránh log(0)

        # Công thức Gain LSA:
        # G_lsa = (xi / (1+xi)) * exp(0.5 * exp1(v))
        # exp1 là Exponential Integral E1(x)
        
        # Tính thành phần hàm mũ tích phân (Exponential Integral)
        # Scipy sp.exp1(v) chính là E1(v)
        exp_integral = sp.exp1(v)
        
        # Ghép công thức
        gain_lsa = (prior_t / (1.0 + prior_t)) * np.exp(0.5 * exp_integral)

        # --- d. Giới hạn Gain và lưu lại ---
        gain_lsa = np.nan_to_num(gain_lsa, nan=G_MIN, posinf=1.0, neginf=G_MIN)
        gain_lsa = np.clip(gain_lsa, G_MIN, 1.0)
        
        G[:, t:t+1] = gain_lsa
        post_snr[:, t:t+1] = post_t # Lưu gamma cho frame sau

    # ===== 5. Tái tạo (ISTFT) =====
    S_hat = G * Y_mag * np.exp(1j * Y_phase)
    enhanced = librosa.istft(S_hat, hop_length=hop_length)
    
    # Cắt và chuẩn hóa
    enhanced = enhanced[:len(noisy)]
    max_val = np.max(np.abs(enhanced))
    if max_val > 0:
        enhanced = enhanced / max_val

    return enhanced