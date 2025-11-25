# pages/detail.py
import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.fft import fft, fftfreq
import io
import os

st.set_page_config(page_title="Chi Tiết Xử Lý", layout="wide")

# ==================== GET ID FROM URL ====================
query_params = st.query_params
selected_id = query_params.get("selected_id")

if not selected_id:
    st.error("Không tìm thấy ID file. Vui lòng chọn từ trang Lịch sử.")
    st.stop()

try:
    file_id = int(selected_id)
except ValueError:
    st.error("ID không hợp lệ.")
    st.stop()

# ==================== FETCH FROM API ====================
API_BASE = "http://localhost:8000"  # Thay khi deploy
API_URL = f"{API_BASE}/file/{file_id}"

def add_noisy_suffix(filepath: str) -> str:
    """
    Convert: /audio/uploads/music_clean.wav
          → /audio/uploads/music_clean_noisy.wav
    """
    if not filepath or not filepath.endswith(".wav"):
        return filepath
    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    name, ext = os.path.splitext(filename)
    new_filename = f"{name}_noisy{ext}"
    return os.path.join(directory, new_filename).replace("\\", "/").replace("/audio/uploads/", "/audio/results/")

with st.spinner(f"Đang tải chi tiết ID {file_id}..."):
    try:
        response = requests.get(API_URL, timeout=15)
        if response.status_code != 200:
            st.error(f"Không tìm thấy file (HTTP {response.status_code})")
            st.stop()
        result = response.json()
    except Exception as e:
        st.error(f"Lỗi kết nối server: {e}")
        st.stop()

# ==================== BASIC INFO ====================
song_name = result.get("song_name", "Không tên")
file_size_kb = result.get("file_size_kb", 0)
date_process = result.get("date_process", "")[:19].replace("T", " ") if result.get("date_process") else "Không rõ"

st.markdown(f"# {song_name}")
st.caption(f"**ID:** {result.get('id')} • **Size:** {file_size_kb:,} KB • **Processed at:** {date_process}")

# ==================== AUDIO (direct from backend) ====================
orig_url = f"{API_BASE}{add_noisy_suffix(result.get('original_file'))}" if result.get("original_file") else None
proc_url = f"{API_BASE}{result.get('processed_file')}" if result.get("processed_file") else None
print(add_noisy_suffix(result.get('original_file')))
c1, c2 = st.columns(2)

with c1:
    st.subheader("Bản gốc (có tiếng ồn)")
    if orig_url:
        st.audio(orig_url, format="audio/wav")
    else:
        st.warning("Không có file gốc")

with c2:
    st.subheader("Bản đã xử lý")
    if proc_url:
        st.audio(proc_url, format="audio/wav")
        # Download button
        try:
            dl = requests.get(proc_url, timeout=30)
            if dl.status_code == 200:
                st.download_button(
                    label="Tải file sạch",
                    data=dl.content,
                    file_name=f"cleaned_{song_name}.wav",
                    mime="audio/wav",
                    use_container_width=True
                )
        except:
            st.warning("Không thể tải file để download.")
    else:
        st.error("Không tìm thấy file đã xử lý")

# ==================== COMPARISON TABLE ====================
st.markdown("### Bảng So Sánh Các Bộ Lọc")

comparison = result.get("comparison", {})
if not comparison:
    st.info("Chưa có dữ liệu so sánh.")
else:
    rows = []
    for method, metrics in comparison.items():
        imp = float(metrics.get("improvement_percent", 0))
        perf = float(metrics.get("performance", 0))
        time_sec = float(metrics.get("time_seconds", 0))

        rows.append({
            "Bộ lọc": method.replace("_", " ").replace("-", " ").title(),
            "Cải thiện (%)": f"{imp:+.2f}%",
            "Hiệu suất": round(perf, 3),
            "Thời gian": f"{time_sec:.2f}s",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

# ==================== BIỂU ĐỒ PHỔ TẦN SỐ (MỚI) ====================
st.markdown("### So sánh Phổ Tần Số (Frequency Spectrum)")

if not orig_url or not proc_url:
    st.warning("Cần cả hai file gốc và đã xử lý để vẽ biểu đồ.")
else:
    with st.spinner("Đang tải và phân tích tín hiệu âm thanh..."):
        try:
            # Tải dữ liệu WAV từ URL
            orig_resp = requests.get(orig_url, timeout=30)
            proc_resp = requests.get(proc_url, timeout=30)

            if orig_resp.status_code != 200 or proc_resp.status_code != 200:
                st.error("Không thể tải file âm thanh để phân tích phổ tần số.")
            else:
                # Đọc WAV từ bytes
                orig_bytes = io.BytesIO(orig_resp.content)
                proc_bytes = io.BytesIO(proc_resp.content)

                sample_rate_orig, data_orig = wavfile.read(orig_bytes)
                sample_rate_proc, data_proc = wavfile.read(proc_bytes)

                # Chuẩn hóa dữ liệu về mono + float32
                if data_orig.ndim > 1:
                    data_orig = data_orig[:, 0]
                if data_proc.ndim > 1:
                    data_proc = data_proc[:, 0]

                # Ép kiểu để tính FFT
                data_orig = data_orig.astype(np.float32)
                data_proc = data_proc.astype(np.float32)

                # Hàm vẽ phổ tần số
                def plot_spectrum(signal, sr, label, ax):
                    N = len(signal)
                    yf = fft(signal)
                    xf = fftfreq(N, 1 / sr)[:N//2]
                    ax.plot(xf, 2.0 / N * np.abs(yf[:N//2]), label=label, linewidth=1.5)

                fig, ax = plt.subplots(figsize=(13, 6))
                plot_spectrum(data_orig, sample_rate_orig, "Tín hiệu gốc (có nhiễu)", ax)
                plot_spectrum(data_proc, sample_rate_proc, "Tín hiệu đã lọc", ax)

                ax.set_title("So sánh Phổ Tần Số: Trước & Sau khi khử nhiễu", fontsize=16, fontweight="bold")
                ax.set_xlabel("Tần số (Hz)", fontsize=12)
                ax.set_ylabel("Biên độ", fontsize=12)
                ax.set_xlim(0, min(sample_rate_orig, sample_rate_proc) // 2)
                ax.set_ylim(0, None)
                ax.legend(fontsize=11)
                ax.grid(True, alpha=0.3)

                st.pyplot(fig)
                plt.close(fig)

                st.success("Phổ tần số được vẽ thành công! Bạn có thể thấy nhiễu cao tần đã giảm đáng kể.")

        except Exception as e:
            st.error(f"Lỗi khi phân tích phổ tần số: {e}")
            st.info("Có thể file WAV bị lỗi định dạng hoặc quá lớn để xử lý trực tiếp.")
            
st.markdown("### So sánh Biên độ Tín hiệu theo Thời gian (Waveform)")

if not orig_url or not proc_url:
    st.warning("Cần cả hai file để vẽ biểu đồ biên độ theo thời gian.")
else:
    with st.spinner("Đang vẽ biểu đồ dạng sóng (waveform)..."):
        try:
            # Dùng lại dữ liệu đã tải ở phần trên (tối ưu bộ nhớ)
            # Nếu chưa tải thì tải lại (an toàn)
            if 'orig_resp' not in locals() or 'proc_resp' not in locals():
                orig_resp = requests.get(orig_url, timeout=30)
                proc_resp = requests.get(proc_url, timeout=30)

            orig_bytes = io.BytesIO(orig_resp.content)
            proc_bytes = io.BytesIO(proc_resp.content)

            sr_o, sig_o = wavfile.read(orig_bytes)
            sr_p, sig_p = wavfile.read(proc_bytes)

            # Chuyển về mono
            if sig_o.ndim > 1:
                sig_o = sig_o[:, 0]
            if sig_p.ndim > 1:
                sig_p = sig_p[:, 0]

            sig_o = sig_o.astype(np.float32)
            sig_p = sig_p.astype(np.float32)

            # Tạo trục thời gian
            t_o = np.linspace(0, len(sig_o) / sr_o, len(sig_o))
            t_p = np.linspace(0, len(sig_p) / sr_p, len(sig_p))

            # Tạo figure với 2 subplot dọc
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

            # Bản gốc (có nhiễu) - màu đỏ nhạt
            ax1.plot(t_o, sig_o, color="#ff4444", linewidth=0.8, alpha=0.9)
            ax1.set_title("Tín hiệu gốc (có tiếng ồn) – Dạng sóng đầy đủ", fontsize=14, color="#cc0000")
            ax1.set_ylabel("Biên độ")
            ax1.grid(True, alpha=0.3)
            ax1.margins(x=0)

            # Bản đã xử lý (sạch) - màu xanh lá
            ax2.plot(t_p, sig_p, color="#00aa00", linewidth=0.9, alpha=0.9)
            ax2.set_title("Tín hiệu đã khử nhiễu – Sạch hơn, ít gợn hơn", fontsize=14, color="#006600", fontweight="bold")
            ax2.set_ylabel("Biên độ")
            ax2.set_xlabel("Thời gian (giây)")
            ax2.grid(True, alpha=0.3)
            ax2.margins(x=0)

            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

            # Thêm chú thích hữu ích
            st.caption("""
            **Quan sát:**  
            - Ở bản gốc: bạn sẽ thấy nhiều dao động nhỏ li ti (noise floor cao) ngay cả khi không có nhạc.  
            - Ở bản sạch: các đoạn im lặng gần như phẳng, chỉ còn lại nhạc cụ/giọng hát rõ ràng → lọc nhiễu thành công!
            """)

            # Bonus: Zoom vào 10 giây đầu để thấy rõ hơn
            st.markdown("#### Zoom chi tiết 10 giây đầu (thấy rõ nhiễu bị loại bỏ)")

            zoom_sec = 10.0
            idx_o = int(zoom_sec * sr_o)
            idx_p = int(zoom_sec * sr_p)

            fig_zoom, (ax1z, ax2z) = plt.subplots(2, 1, figsize=(14, 6), sharex=True)

            ax1z.plot(t_o[:idx_o], sig_o[:idx_o], color="#ff6666", linewidth=1)
            ax1z.set_title(f"Tín hiệu gốc – {zoom_sec}s đầu (có nhiễu nền rõ rệt)", color="red")
            ax1z.set_ylabel("Biên độ")
            ax1z.grid(True, alpha=0.3)

            ax2z.plot(t_p[:idx_p], sig_p[:idx_p], color="#00cc00", linewidth=1)
            ax2z.set_title(f"Tín hiệu đã lọc – {zoom_sec}s đầu (gần như phẳng khi im lặng)", color="green", fontweight="bold")
            ax2z.set_ylabel("Biên độ")
            ax2z.set_xlabel("Thời gian (giây)")
            ax2z.grid(True, alpha=0.3)

            plt.tight_layout()
            st.pyplot(fig_zoom)
            plt.close(fig_zoom)

            st.success("Biểu đồ dạng sóng cho thấy hiệu quả khử nhiễu cực kỳ rõ ràng!")

        except Exception as e:
            st.error(f"Lỗi khi vẽ biểu đồ biên độ theo thời gian: {e}")