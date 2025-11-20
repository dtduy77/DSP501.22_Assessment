# pages/detail.py
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Chi Tiết Xử Lý - Audio Denoiser", layout="wide")

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
orig_url = f"{API_BASE}{result.get('original_file')}" if result.get("original_file") else None
proc_url = f"{API_BASE}{result.get('processed_file')}" if result.get("processed_file") else None

c1, c2 = st.columns(2)

with c1:
    st.subheader("🔊 Bản gốc (có tiếng ồn)")
    if orig_url:
        st.audio(orig_url, format="audio/wav")
    else:
        st.warning("Không có file gốc")

with c2:
    st.subheader("✨ Bản đã xử lý")
    if proc_url:
        st.audio(proc_url, format="audio/wav")
        # Download button
        try:
            dl = requests.get(proc_url)
            if dl.status_code == 200:
                st.download_button(
                    label="Tải file sạch",
                    data=dl.content,
                    file_name=f"cleaned_{song_name}",
                    mime="audio/wav",
                    use_container_width=True
                )
        except:
            pass  # fail silently
    else:
        st.error("Không tìm thấy file đã xử lý")

# ==================== COMPARISON TABLE (NO HIGHLIGHT) ====================
st.markdown("### Bảng So Sánh Các Thuật Toán")

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
            "Thuật toán": method.replace("_", " ").replace("-", " ").title(),
            "Cải thiện (%)": f"{imp:+.2f}%",
            "Hiệu suất": round(perf, 3),
            "Thời gian": f"{time_sec:.2f}s",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)