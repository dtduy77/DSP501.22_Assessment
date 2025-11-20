import streamlit as st

def render_sidebar():
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/48/headphones.png")
        st.title("Audio Denoiser")
        st.markdown("**Xử lý tiếng ồn & cải thiện chất lượng âm thanh**")
        st.markdown("---")
        st.page_link("app.py", label="Xử lí âm thanh", icon="📃")
        st.page_link("pages/history.py", label="Lịch sử", icon="🔁")
        st.markdown("---")
       
