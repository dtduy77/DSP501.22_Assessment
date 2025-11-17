import numpy as np

def snr_db(clean, enhanced):
    clean = clean[:len(enhanced)]
    noise_res = enhanced - clean
    p_clean = np.mean(clean**2)
    p_noise = np.mean(noise_res**2) + 1e-12
    return 10 * np.log10(p_clean / p_noise)
