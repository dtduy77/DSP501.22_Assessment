import numpy as np
import matplotlib.pyplot as plt
import librosa
import soundfile as sf

FILE = "music_noisy.wav"     
SR   = 16000                     

# ===========================
# 1️ LOAD AUDIO
# ===========================
x, sr = librosa.load(FILE, sr=SR, mono=True)
N = len(x)

print(f"Loaded: {FILE}")
print(f"   Length  : {N/sr:.2f} sec")
print(f"   Samples : {N}")
print(f"   SR      : {sr} Hz")

# ===========================
# 2️ FFT
# ===========================
X = np.fft.rfft(x)                         
freqs = np.fft.rfftfreq(N, 1/sr)           
mag = np.abs(X)                           

# ===========================
# 3️ VẼ DẠNG SÓNG + PHỔ
# ===========================
plt.figure(figsize=(14,8))

# ----- Waveform -----
plt.subplot(2,1,1)
plt.plot(x, linewidth=0.7)
plt.title("Waveform (Noisy)")
plt.xlabel("Samples")
plt.ylabel("Amplitude")

# ----- Magnitude Spectrum -----
plt.subplot(2,1,2)
plt.semilogy(freqs, mag + 1e-9)            
plt.title("FFT Magnitude Spectrum")
plt.xlabel("Frequency (Hz)")
plt.ylabel("|X(f)| (log scale)")
plt.xlim([0, sr/2])                        

plt.tight_layout()
plt.show()
