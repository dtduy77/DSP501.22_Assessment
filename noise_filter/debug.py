import acoustid
import os

# THAY KEY MỚI CỦA BẠN VÀO ĐÂY
API_KEY = "lYB2wKOO5Q" 

# Đường dẫn file nhạc CHUẨN (nhạc MP3 hoặc WAV gốc tải từ mạng, không phải file đã lọc)
file_test = "results/music.mp3" 

def debug_system():
    if not os.path.exists("fpcalc.exe"):
        print("❌ Thiếu file fpcalc.exe")
        return

    print(f"🔍 Đang đọc file: {file_test}")
    
    try:
        # 1. Test lấy Fingerprint
        duration, fingerprint = acoustid.fingerprint_file(file_test)
        
        print(f"✅ Độ dài: {duration}s")
        print(f"✅ Fingerprint (Độ dài chuỗi): {len(fingerprint)}")
        
        # Kiểm tra xem fingerprint có dữ liệu không
        if len(fingerprint) < 100:
            print("❌ LỖI NGHIÊM TRỌNG: Fingerprint quá ngắn!")
            print("👉 Nguyên nhân: File âm thanh bị lỗi codec hoặc file rỗng (toàn silence).")
            print("👉 Giải pháp: Dùng phần mềm convert file đó sang MP3 chuẩn rồi thử lại.")
            return

        print("👉 Fingerprint OK. Đang gửi lên Server...")

        # 2. Test API
        response = acoustid.lookup(API_KEY, fingerprint, duration)
        
        # In toàn bộ phản hồi từ server để xem lỗi gì
        print("\n===== PHẢN HỒI TỪ SERVER =====")
        print(response) 
        
        if response.get('status') != 'ok':
            print("\n❌ LỖI API: Key sai hoặc Server từ chối.")
            
    except Exception as e:
        print(f"\n❌ LỖI PYTHON: {e}")

if __name__ == "__main__":
    debug_system()