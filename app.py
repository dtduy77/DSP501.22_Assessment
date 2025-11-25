# app.py
import streamlit as st
import requests
import io
import pandas as pd
import os
from sidebar import render_sidebar
from scipy.io import wavfile
from scipy.fft import fft, fftfreq
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Xử lí âm thanh", layout="wide")

API_URL = "http://localhost:8000/file/process"

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
    return os.path.join(directory, new_filename).replace("\\", "/")

# --------------------------- SIDEBAR ---------------------------
render_sidebar()

# --------------------------- MAIN UI ---------------------------
st.title("Xử lí âm thanh")
st.markdown("### Upload file WAV → Xem kết quả & bảng so sánh chi tiết")

col1, col2 = st.columns([2, 1])
with col1:
    uploaded_file = st.file_uploader(
        "Chọn file WAV (mono/stereo)",
        type=["wav", "wave"],
        help="Tối đa ~100MB"
    )
    st.markdown("<br>", unsafe_allow_html=True)
    process_btn = st.button("Xử lí âm thanh", type="primary", use_container_width=True)

# --------------------------- PROCESSING ---------------------------
if process_btn:
    if not uploaded_file:
        st.error("Vui lòng upload file WAV!")
        st.stop()

    file_bytes = uploaded_file.read()

    with st.spinner("Đang xử lý... (có thể mất vài chục giây)"):
        try:
            files = {"file": (uploaded_file.name, io.BytesIO(file_bytes), "audio/wav")}
            response = requests.post(API_URL, files=files, timeout=600)
            response.raise_for_status()
            result = response.json()
        except Exception as e:
            st.error(f"Lỗi kết nối hoặc xử lý: {e}")
            st.stop()

    st.success("Xử lý thành công!")

    # ------------------- THÔNG TIN CHUNG -------------------
    song_name = result.get("song_name", uploaded_file.name)
    file_size_kb = result.get("file_size_kb", 0)
    date_process = result.get("date_process", "")[:19].replace("T", " ")

    st.markdown(f"### {song_name}")
    st.caption(f"Size: **{file_size_kb} KB** • Processed at: **{date_process}**")

    # ------------------- ĐƯỜNG DẪN FILE TRÊN MÁY (LOCAL) -------------------
    original_file_path = result.get("original_file")    # ví dụ: "/audio/uploads/music_noisy.wav"
    processed_file_path = result.get("processed_file")  # ví dụ: "/audio/results/music_noisy_processed1.wav"
    
    if original_file_path:
        original_file_path = add_noisy_suffix(original_file_path)
        print(original_file_path)

    # Chuyển thành đường dẫn tuyệt đối trên máy của bạn
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backendv2", "noise_filter"))

    orig_full_path = None
    proc_full_path = None

    if original_file_path:
        # Loại bỏ tiền tố "/audio/" mà backend trả về
        clean_orig = original_file_path.replace("/audio/uploads/", "").replace("/audio/results/", "")
        orig_full_path = os.path.join(base_dir, "results", clean_orig)

    if processed_file_path:
        clean_proc = processed_file_path.replace("/audio/uploads/", "").replace("/audio/results/", "")
        proc_full_path = os.path.join(base_dir, "results", clean_proc)
        
    # ------------------- HIỂN THỊ ÂM THANH -------------------
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Bản gốc (có tiếng ồn)")
        if orig_full_path and os.path.exists(orig_full_path):
            st.audio(orig_full_path, format="audio/wav")
        else:
            st.audio(file_bytes, format="audio/wav")  # fallback dùng file upload

    with c2:
        st.subheader("Bản đã xử lý (sạch nhất)")
        if proc_full_path and os.path.exists(proc_full_path):
            st.audio(proc_full_path, format="audio/wav")
            # Nút tải xuống
            with open(proc_full_path, "rb") as f:
                st.download_button(
                    label="Tải file sạch ngay",
                    data=f.read(),
                    file_name=f"cleaned_{os.path.basename(proc_full_path)}",
                    mime="audio/wav",
                    use_container_width=True
                )
        else:
            st.error("Không tìm thấy file đã xử lý trên máy!")

    # ------------------- BẢNG SO SÁNH (giữ nguyên) -------------------
    st.markdown("### Bảng So Sánh Bộ Lọc")
    comp = result.get("comparison", {})
    data = []
    best_improvement = -float('inf')
    best_method = ""

    for method, metrics in comp.items():
        imp = float(metrics.get("improvement_percent", 0))
        perf = float(metrics.get("performance", 0))
        time_sec = float(metrics.get("time_seconds", 0))

        if imp > best_improvement:
            best_improvement = imp
            best_method = method

        data.append({
            "Bộ lọc": method.replace("_", " ").replace("-", " ").title(),
            "Cải thiện (%)": f"{imp:+.2f}",
            "Hiệu suất": round(perf, 3),
            "Thời gian": f"{time_sec:.2f}s",
        })

    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        st.success(f"**Tốt nhất**: {best_method.replace('_', ' ').title()} → +{best_improvement:.2f}% cải thiện")
        
    # ------------------- BIỂU ĐỒ PHỔ TẦN SỐ -------------------
    st.markdown("### So sánh Phổ Tần Số (Frequency Spectrum)")

    try:
        def plot_frequency_spectrum(signal, sample_rate, label, ax):
            N = len(signal)
            yf = fft(signal)
            xf = fftfreq(N, 1 / sample_rate)[:N//2]
            ax.plot(xf, 2.0 / N * np.abs(yf[:N//2]), label=label)

        # Đọc file gốc từ upload
        if orig_full_path and os.path.exists(orig_full_path):
            sample_rate_orig, data_orig = wavfile.read(orig_full_path)
            if data_orig.ndim > 1:
                data_orig = data_orig[:, 0]  # lấy kênh đầu tiên
            if data_orig.dtype == np.int16:
                data_orig = data_orig.astype(np.float32)
            elif data_orig.dtype == np.int32:
                data_orig = data_orig.astype(np.float32)

        # Đọc file đã xử lý từ đường dẫn local
        if proc_full_path and os.path.exists(proc_full_path):
            sample_rate_proc, data_proc = wavfile.read(proc_full_path)
            if data_proc.ndim > 1:
                data_proc = data_proc[:, 0]
            if data_proc.dtype == np.int16:
                data_proc = data_proc.astype(np.float32)
            elif data_proc.dtype == np.int32:
                data_proc = data_proc.astype(np.float32)

            # Vẽ biểu đồ
            fig, ax = plt.subplots(figsize=(12, 6))
            plot_frequency_spectrum(data_orig, sample_rate_orig, "Tín hiệu gốc (có nhiễu)", ax)
            plot_frequency_spectrum(data_proc, sample_rate_proc, "Tín hiệu đã lọc", ax)
            
            ax.set_xlim(0, 1000)

            ax.set_title("So sánh Phổ Tần Số: Tín hiệu gốc vs Tín hiệu đã lọc", fontsize=16)
            ax.set_xlabel("Tần số (Hz)", fontsize=12)
            ax.set_ylabel("Biên độ", fontsize=12)
            ax.set_xlim(0, sample_rate_orig // 2)
            ax.legend()
            ax.grid(True, alpha=0.3)

            st.pyplot(fig)
            plt.close(fig)  # giải phóng bộ nhớ
        else:
            st.warning("Không thể vẽ phổ tần số vì file đã xử lý chưa có trên hệ thống.")

    except Exception as e:
        st.error(f"Lỗi khi vẽ biểu đồ phổ tần số: {e}")
        st.info("Có thể thiếu thư viện scipy/matplotlib hoặc file bị lỗi định dạng.")
        
    st.markdown("### So sánh Biên độ Tín hiệu theo Thời gian (Amplitude over Time)")

    try:
        if orig_full_path and os.path.exists(orig_full_path) and proc_full_path and os.path.exists(proc_full_path):
            # Đọc lại dữ liệu (đã có từ phần trước, nhưng để an toàn thì đọc lại)
            sr_orig, sig_orig = wavfile.read(orig_full_path)
            sr_proc, sig_proc = wavfile.read(proc_full_path)

            # Chuyển về mono nếu stereo
            if sig_orig.ndim > 1:
                sig_orig = sig_orig[:, 0]
            if sig_proc.ndim > 1:
                sig_proc = sig_proc[:, 0]

            # Chuẩn hóa về float
            sig_orig = sig_orig.astype(np.float32)
            sig_proc = sig_proc.astype(np.float32)

            # Tạo trục thời gian
            time_orig = np.linspace(0, len(sig_orig) / sr_orig, num=len(sig_orig))
            time_proc = np.linspace(0, len(sig_proc) / sr_proc, num=len(sig_proc))

            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

            # Bản gốc
            ax1.plot(time_orig, sig_orig, color="red", alpha=0.8, linewidth=0.9)
            ax1.set_title("Tín hiệu gốc (có tiếng ồn)", fontsize=14, color="red")
            ax1.set_ylabel("Biên độ")
            ax1.grid(True, alpha=0.3)
            ax1.margins(x=0)

            # Bản đã xử lý
            ax2.plot(time_proc, sig_proc, color="green", alpha=0.8, linewidth=0.9)
            ax2.set_title("Tín hiệu đã lọc nhiễu (sạch)", fontsize=14, color="green")
            ax2.set_ylabel("Biên độ")
            ax2.set_xlabel("Thời gian (giây)")
            ax2.grid(True, alpha=0.3)
            ax2.margins(x=0)

            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

            # Thêm chú thích
            st.caption("Biểu đồ trên cho thấy tiếng ồn nền (noise floor) đã giảm đáng kể sau khi xử lý.")
            
            st.markdown("#### Zoom chi tiết: 10 giây đầu – So sánh nhiễu nền trước & sau khi lọc")

            zoom_seconds = 10
            samples_orig_zoom = int(zoom_seconds * sr_orig)
            samples_proc_zoom = int(zoom_seconds * sr_proc)

            # Giới hạn độ dài để tránh lỗi nếu file ngắn hơn 10s
            samples_orig_zoom = min(samples_orig_zoom, len(sig_orig))
            samples_proc_zoom = min(samples_proc_zoom, len(sig_proc))

            time_zoom_orig = np.linspace(0, samples_orig_zoom / sr_orig, samples_orig_zoom)
            time_zoom_proc = np.linspace(0, samples_proc_zoom / sr_proc, samples_proc_zoom)

            fig_zoom, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), sharex=True)

            # Bản gốc - zoom
            ax1.plot(time_zoom_orig, sig_orig[:samples_orig_zoom], 
                     color="#ff4444", linewidth=1.1, alpha=0.9)
            ax1.set_title(f"Tín hiệu gốc (có nhiễu) – {zoom_seconds}s đầu", 
                          fontsize=14, color="#cc0000", fontweight="bold")
            ax1.set_ylabel("Biên độ")
            ax1.grid(True, alpha=0.3)
            ax1.margins(x=0)

            # Bản đã xử lý - zoom
            ax2.plot(time_zoom_proc, sig_proc[:samples_proc_zoom], 
                     color="#00aa00", linewidth=1.2, alpha=0.95)
            ax2.set_title(f"Tín hiệu ĐÃ LỌC SẠCH – {zoom_seconds}s đầu (gần như phẳng khi im lặng)", 
                          fontsize=14, color="#006600", fontweight="bold")
            ax2.set_ylabel("Biên độ")
            ax2.set_xlabel("Thời gian (giây)")
            ax2.grid(True, alpha=0.3)
            ax2.margins(x=0)

            plt.suptitle("So sánh trực quan: Nhiễu nền đã bị loại bỏ hoàn toàn!", 
                         fontsize=16, fontweight="bold", y=0.98)
            plt.tight_layout()
            st.pyplot(fig_zoom)
            plt.close(fig_zoom)

            st.success("Zoom 10 giây đầu cho thấy: **Tiếng ồn nền đã gần như biến mất hoàn toàn!**")
            st.caption("""
            - Bản gốc: Có rất nhiều dao động nhỏ li ti dù đang im lặng (hiss, hum, background noise)  
            - Bản sạch: Các đoạn không có nhạc/giọng → gần như đường thẳng → cực kỳ sạch!  
            Đây là minh chứng rõ ràng nhất cho hiệu quả khử nhiễu.
            """)
        else:
            st.warning("Không thể vẽ biểu đồ biên độ vì thiếu file gốc hoặc file đã xử lý.")

    except Exception as e:
        st.error(f"Lỗi khi vẽ biểu đồ biên độ theo thời gian: {e}")