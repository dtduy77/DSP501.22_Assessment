# pages/history.py
import streamlit as st
import requests
import pandas as pd
from sidebar import render_sidebar

st.set_page_config(page_title="Lịch sử", layout="wide")

# ==================== SIDEBAR ====================
render_sidebar()

# ==================== MAIN ====================
st.title("Lịch sử xử lý")
st.markdown("**Click vào tên bài hát để xem chi tiết**")

API_URL = "http://localhost:8000/file"  # Thay bằng domain thật khi deploy

@st.cache_data(ttl=15, show_spinner=False)
def fetch_history_from_api():
    try:
        response = requests.get(API_URL, headers={"Accept": "application/json"}, timeout=10)
        if response.status_code == 200:
            return response.json(), "api"
    except Exception as e:
        st.error(f"Lỗi kết nối API: {e}")
    return None, None

# 1. Try API first
data, source = fetch_history_from_api()

# 2. Fallback to session_state
if data is None:
    if "history" in st.session_state and st.session_state.history:
        data = st.session_state.history[::-1]
        source = "local"
    else:
        st.info("Chưa có lịch sử nào. Hãy xử lý file trước!")
        st.stop()

# Convert to DataFrame
df = pd.DataFrame(data)

if "id" not in df.columns:
    st.error("Dữ liệu không có trường 'id'")
    st.stop()

# Parse timestamp
if "date_process" in df.columns:
    df["timestamp"] = pd.to_datetime(df["date_process"], utc=True)
else:
    df["timestamp"] = pd.NaT

# Sort newest first
df = df.sort_values("timestamp", ascending=False).reset_index(drop=True)
df["date_process_display"] = df["timestamp"].dt.strftime("%d/%m/%Y %H:%M:%S")

# Source info
st.caption(f"Tổng cộng **{len(df)}** bản ghi (nguồn: {source})")

# ==================== CLICKABLE SONG NAME ====================
def make_clickable(song_name, row_id):
    return f'<a href="/detail?selected_id={row_id}" target="_self" style="color:#1E90FF; text-decoration:none; font-weight:600;">{song_name or "Không tên"}</a>'

df["Tên bài hát"] = df.apply(
    lambda row: make_clickable(row["song_name"], row["id"]),
    axis=1
)

# ==================== DISPLAY COLUMNS ====================
display_df = df.copy()
display_df["ID"] = df["id"]  # Thêm cột ID
display_df["Thời gian xử lý"] = df["date_process_display"]

# Reorder columns exactly as you want
columns_order = ["ID", "Tên bài hát", "Thời gian xử lý"]
if "uploaded_filename" in df.columns:
    display_df["File gốc"] = df["uploaded_filename"]
    columns_order.insert(2, "File gốc")  # Insert after song name if exists

final_df = display_df[columns_order]

# ==================== RENDER TABLE ====================
st.markdown(
    final_df.to_html(escape=False, index=False),
    unsafe_allow_html=True
)

# ==================== REFRESH BUTTON ====================
col1, col2 = st.columns([1, 6])
with col1:
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()