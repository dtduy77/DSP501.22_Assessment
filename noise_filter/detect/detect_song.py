import acoustid
import os
from collections import defaultdict
from dotenv import load_dotenv  

load_dotenv() 

# Key của bạn
API_KEY =os.getenv("API_KEY")

def detect_song(audio_path):
    """
    Hàm nhận diện bài hát sử dụng thuật toán VOTING (Bầu chọn)
    Để loại bỏ các kết quả ngẫu nhiên có điểm cao nhưng sai.
    """
    if not os.path.exists(audio_path):
        print(f"File không tồn tại: {audio_path}")
        return

    if not os.path.exists("fpcalc.exe"):
        print("Thiếu file 'fpcalc.exe'.")
        return

    print(f"Đang phân tích: {os.path.basename(audio_path)}...")
    
    try:
        duration, fingerprint = acoustid.fingerprint_file(audio_path)
        response = acoustid.lookup(API_KEY, fingerprint, duration)
    except Exception as e:
        print(f"Lỗi: {e}")
        return

    if not response or not response.get('results'):
        print("Không tìm thấy bài hát nào.")
        return

    # --- THUẬT TOÁN VOTING ---
    # Thay vì lấy điểm cao nhất, ta cộng dồn điểm cho từng bài hát xuất hiện
    song_votes = defaultdict(float)
    song_metadata = {} # Lưu thông tin nghệ sĩ để in ra sau

    for result in response['results']:
        score = result.get("score", 0)
        if score < 0.5: continue # Bỏ qua kết quả rác

        for recording in result.get("recordings", []):
            title = recording.get("title", "Unknown")
            
            # Lấy tên nghệ sĩ
            artists = [a["name"] for a in recording.get("artists", [])]
            artist_str = ", ".join(artists) if artists else "Unknown"
            
            # Key để bầu chọn là "Tên bài hát - Tên nghệ sĩ"
            # (Để tránh nhầm bài cùng tên nhưng khác người hát)
            unique_key = f"{title} || {artist_str}"
            
            # Cộng dồn điểm (Score càng cao thì phiếu bầu càng nặng)
            song_votes[unique_key] += score
            
            # Lưu lại metadata để dùng khi in kết quả
            song_metadata[unique_key] = {
                "title": title,
                "artist": artist_str,
                "last_score": score # Lưu điểm của lần xuất hiện cuối
            }

    # Tìm bài hát có tổng điểm cao nhất
    if song_votes:
        best_song_key = max(song_votes, key=song_votes.get)
        winner = song_metadata[best_song_key]
        total_vote_score = song_votes[best_song_key]

        print(f"BÀI HÁT: {winner['title'].upper()}")
        print(f"NGHỆ SĨ: {winner['artist']}")
        print(f"ĐỘ TIN CẬY (VOTE): {total_vote_score:.2f} điểm")
        print(f"(Dựa trên điểm khớp gốc: {winner['last_score']*100:.1f}%)")
    else:
        print("Có tín hiệu nhưng không đủ dữ liệu để kết luận.")

    print("\n===================================")