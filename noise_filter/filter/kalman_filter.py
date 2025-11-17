import numpy as np
import librosa

SR = 16000
N_FFT = 1024
HOP = 256
EPS = 1e-9
ALPHA = 0.96      

def spectral_kalman(noisy, noise_ref, sr=SR):
    # STFT
    Y = librosa.stft(noisy, n_fft=N_FFT, hop_length=HOP)
    Y_mag = np.abs(Y)
    Y_phase = np.angle(Y)
    
    # Estimate observation noise (R) - noise variance
    N = librosa.stft(noise_ref, n_fft=N_FFT, hop_length=HOP)
    R = np.mean(np.abs(N)**2, axis=1, keepdims=True)  # Observation noise variance
    
    # Process noise (Q) - speech dynamics uncertainty
    Q = 0.01 * R  # Small process noise (10% of observation noise)
    
    num_bins, num_frames = Y_mag.shape
    
    # Initialize
    X_est = np.zeros_like(Y_mag)
    P = np.ones((num_bins, num_frames)) * R  # Initial uncertainty
    
    for t in range(num_frames):
        Y_t = Y_mag[:, t]
        
        # ===== PREDICT =====
        if t == 0:
            X_pred = Y_t
            P_pred = P[:, 0]
        else:
            # State transition: X[t] = α * X[t-1] + process_noise
            X_pred = ALPHA * X_est[:, t-1]
            P_pred = (ALPHA**2) * P[:, t-1] + Q.squeeze()  # Add process noise Q, not R!
        
        # ===== KALMAN GAIN =====
        # K = P_pred * H^T / (H * P_pred * H^T + R)
        # With H=I: K = P_pred / (P_pred + R)
        K = P_pred / (P_pred + R.squeeze())
        
        # ===== UPDATE =====
        # Innovation: Y_t - H * X_pred = Y_t - X_pred
        innovation = Y_t - X_pred
        X_est[:, t] = X_pred + K * innovation
        P[:, t] = (1 - K) * P_pred  # Update covariance
    
    # Reconstruct
    S_hat = X_est * np.exp(1j * Y_phase)
    enhanced = librosa.istft(S_hat, hop_length=HOP)
    enhanced /= np.max(np.abs(enhanced)) + EPS
    return enhanced