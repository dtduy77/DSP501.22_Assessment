# app.py
import streamlit as st
import requests
import io
import pandas as pd
import os
from sidebar import render_sidebar

st.set_page_config(page_title="Audio Denoiser Pro", layout="wide")

API_URL = "http://localhost:8000/file/process"

# --------------------------- SIDEBAR ---------------------------
render_sidebar()

# --------------------------- MAIN UI ---------------------------
st.title("Process File")
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

    # Chuyển thành đường dẫn tuyệt đối trên máy của bạn
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "noise_filter"))

    orig_full_path = None
    proc_full_path = None

    if original_file_path:
        # Loại bỏ tiền tố "/audio/" mà backend trả về
        clean_orig = original_file_path.replace("/audio/uploads/", "").replace("/audio/results/", "")
        orig_full_path = os.path.join(base_dir, "uploads", clean_orig)

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
    st.markdown("### Bảng So Sánh Thuật Toán")
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
            "Thuật toán": method.replace("_", " ").replace("-", " ").title(),
            "Cải thiện (%)": f"{imp:+.2f}",
            "Hiệu suất": round(perf, 3),
            "Thời gian": f"{time_sec:.2f}s",
        })

    if data:
        df = pd.DataFrame(data)
        st.dataframe(df.style.highlight_max(subset=["Cải thiện (%)"]), use_container_width=True)
        st.success(f"**Tốt nhất**: {best_method.replace('_', ' ').title()} → +{best_improvement:.2f}% cải thiện")