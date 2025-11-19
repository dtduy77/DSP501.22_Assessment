# file: filter/wiener_smooth.py

import numpy as np
import librosa

SR = 16000
N_FFT = 1024
HOP = 256


def wiener_smooth(
    noisy: np.ndarray,
    sr: int = SR,
    n_fft: int = N_FFT,
    hop_length: int = HOP,
    alpha: float = 0.98,          # decision-directed factor
    noise_percentile: float = 20  # dùng percentile để ước lượng PSD nhiễu
) -> np.ndarray:
    """
    Wiener Smoothing Filter:
    - Dùng decision-directed prior SNR (Ephraim-Malah)
    - Gain dạng Wiener-like: G = ξ / (1 + ξ)
    - Noise PSD được ước lượng bằng percentile (minimum-statistics approx)
    """

    eps = 1e-12

    # ===== 1. STFT =====
    Y = librosa.stft(noisy, n_fft=n_fft, hop_length=hop_length)
    Y_mag = np.abs(Y)
    Y_phase = np.angle(Y)
    Y_pow = Y_mag ** 2
    n_freq, n_frames = Y_pow.shape

    # ===== 2. Ước lượng PSD noise bằng percentile (minimum statistics) =====

    noise_psd = np.percentile(Y_pow, noise_percentile, axis=1, keepdims=True)
    noise_psd = np.maximum(noise_psd, eps)

    # ===== 3. Khởi tạo SNR =====
    prior_snr = np.zeros_like(Y_pow)
    post_snr = np.zeros_like(Y_pow)
    G = np.zeros_like(Y_mag)

    # Giới hạn SNR để tránh bùng nổ
    POST_SNR_MAX = 40.0   # ~16 dB
    PRIOR_SNR_MAX = 40.0  # ~16 dB
    G_MIN = 0.05

    # ===== 4. Vòng lặp từng frame =====
    for t in range(n_frames):
        # Posterior SNR γ = |Y|^2 / λ_d
        post_t = Y_pow[:, t:t+1] / (noise_psd + eps)
        post_t = np.clip(post_t, 0.0, POST_SNR_MAX)

        if t == 0:
            # Frame đầu: prior ≈ max(γ - 1, 0)
            prior_t = np.maximum(post_t - 1.0, 0.0)
        else:
            # Decision-directed:
            # ξ_t = α * |G_{t-1}|^2 * γ_{t-1} + (1-α) * max(γ_t - 1, 0)
            prior_t = (
                alpha * (G[:, t-1:t] ** 2) * post_snr[:, t-1:t]
                + (1.0 - alpha) * np.maximum(post_t - 1.0, 0.0)
            )

        prior_t = np.clip(prior_t, 0.0, PRIOR_SNR_MAX)

        # Gain Wiener-like: G = ξ / (1 + ξ)
        G_t = prior_t / (1.0 + prior_t + eps)

        # Dọn NaN / Inf nếu có
        G_t = np.nan_to_num(G_t, nan=1.0, posinf=1.0, neginf=G_MIN)

        # Giới hạn gain
        G_t = np.clip(G_t, G_MIN, 1.0)

        # Lưu lại
        G[:, t:t+1] = G_t
        post_snr[:, t:t+1] = post_t
        prior_snr[:, t:t+1] = prior_t

    # ===== 5. Áp dụng gain & ISTFT =====
    S_hat = G * Y_mag * np.exp(1j * Y_phase)
    enhanced = librosa.istft(S_hat, hop_length=hop_length)

    enhanced = enhanced[:len(noisy)]
    enhanced = enhanced / (np.max(np.abs(enhanced)) + eps)

    return enhanced
