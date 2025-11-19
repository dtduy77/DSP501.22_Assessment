# Audio Noise Filtering API

API lọc nhiễu âm thanh sử dụng **Wiener Smooth** và **MMSE-LSA** filters.

---

## ⚡ Quick Start

### 1. Cài đặt
```bash
pip install -r requirement.txt
```

### 2. Chạy API
```bash
cd noise_filter
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Mở trình duyệt
```
http://localhost:8000/docs
```

**Xong!** Bạn đã có thể upload file WAV và xử lý ngay trên giao diện Swagger.

---

## 📖 Hướng dẫn chi tiết

### Cài đặt môi trường (khuyên dùng)

**Với Python venv:**
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac
pip install -r requirement.txt
```

**Với uv (nhanh hơn):**
```bash
uv venv .venv
.venv\Scripts\activate
uv pip install -r requirement.txt
```

### Chạy API Server

```bash
cd noise_filter
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Truy cập:**
- Swagger UI (test API): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- API: http://localhost:8000

### Chạy bộ lọc độc lập (không cần API)

**Wiener Smooth:**
```bash
cd noise_filter
python run_wiener_smooth.py
```

**MMSE-LSA:**
```bash
cd noise_filter
python run_mmse_lsa.py
```

Kết quả lưu trong thư mục `results/`

---

## 🎯 Sử dụng API

### Endpoint 1: Xử lý file âm thanh

**POST** `/file/process`

**Cách dùng:**
1. Vào http://localhost:8000/docs
2. Click vào **POST /file/process**
3. Click **Try it out**
4. Chọn file WAV cần xử lý
5. Click **Execute**

**Response:**
```json
{
  "id": 1,
  "song_name": "audio.wav",
  "original_file": "/audio/uploads/audio.wav",
  "processed_file": "/audio/results/audio_processed.wav",
  "file_size_kb": 123.4,
  "date_process": "2025-11-19T21:30:00",
  "comparison": {
    "wiener_smooth": {
      "improvement_percent": 22.5,
      "performance": 0.83,
      "time_seconds": 0.45
    },
    "mmse_lsa": {
      "improvement_percent": 25.8,
      "performance": 0.87,
      "time_seconds": 0.52
    },
    "best": {
      "improvement_percent": 25.8,
      "performance": 0.87,
      "time_seconds": 0.001
    }
  }
}
```

### Endpoint 2: Xem chi tiết theo ID

**GET** `/file/{id}`

Ví dụ: http://localhost:8000/file/1

### Endpoint 3: Lịch sử xử lý

**GET** `/file`

Xem tất cả file đã xử lý

---

## 🌐 Chia sẻ với người khác

### Cách 1: Dùng ngrok (Nhanh - cho demo)

```bash
# Terminal 1: Chạy server
cd noise_filter
uvicorn api.main:app --port 8000

# Terminal 2: Chạy ngrok
ngrok http 8000
```

**Lần đầu sử dụng ngrok:**
1. Tải tại: https://ngrok.com/download
2. Đăng ký tài khoản miễn phí
3. Lấy authtoken: https://dashboard.ngrok.com/get-started/your-authtoken
4. Chạy: `ngrok config add-authtoken YOUR_TOKEN`
5. Chạy: `ngrok http 8000`

→ Sẽ có link public: `https://xxxx.ngrok-free.app`

### Cách 2: Mạng LAN (cùng wifi)

```bash
# Lấy IP của máy
ipconfig  # Windows → tìm IPv4: 192.168.x.x

# Chạy server
cd noise_filter
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

→ Người khác truy cập: `http://192.168.x.x:8000/docs`

---

## 📁 Cấu trúc Project

```
DSP501.22_Assessment/
│
├── README.md                    # Hướng dẫn này
├── requirement.txt              # Dependencies
│
└── noise_filter/
    │
    ├── api/                     # 🌐 REST API
    │   ├── main.py              # Endpoints
    │   ├── models.py            # Request/Response schemas
    │   ├── database.py          # SQLite database
    │   └── audio_service.py     # Logic xử lý audio
    │
    ├── filter/                  # 🎵 Bộ lọc
    │   ├── wiener_smooth_filter.py
    │   └── mmse_lsa.py
    │
    ├── utils/                   # 🛠️ Utilities
    │   ├── audio_io.py
    │   └── metrics.py
    │
    ├── data/                    # 📂 Test data
    ├── results/                 # 📂 Kết quả xử lý
    ├── uploads/                 # 📂 File upload
    │
    ├── run_wiener_smooth.py     # Chạy Wiener độc lập
    └── run_mmse_lsa.py          # Chạy MMSE-LSA độc lập
```

---

## 🔬 Bộ lọc

### 1. Wiener Smooth Filter
- **Thuật toán:** Decision-directed prior SNR (Ephraim-Malah)
- **Đặc điểm:** Nhanh, hiệu quả, smooth với α=0.98
- **Công thức gain:** `G = ξ / (1 + ξ)`

### 2. MMSE-LSA Filter
- **Thuật toán:** Log-Spectral Amplitude Estimator
- **Đặc điểm:** Tối ưu trên miền logarit (gần thính giác người)
- **Công thức gain:** `G = (ξ/(1+ξ)) × exp(0.5 × E1(v))`

### 3. Best Filter
- Tự động so sánh SNR của 2 bộ lọc
- Chọn bộ lọc cho kết quả tốt hơn
- Thời gian ≈ 0 (chỉ so sánh)

---

## 📊 Metrics

| Metric | Ý nghĩa | Công thức |
|--------|---------|-----------|
| **improvement_percent** | % cải thiện SNR | `((SNR_after - SNR_before) / \|SNR_before\|) × 100` |
| **performance** | Điểm hiệu suất (0-1) | `(SNR - SNR_min) / (SNR_max - SNR_min)` |
| **time_seconds** | Thời gian xử lý | Đo bằng `time.time()` |

---

## 🆘 Khắc phục sự cố

### Lỗi: `ModuleNotFoundError`
```bash
pip install -r requirement.txt
```

### Lỗi: `Port 8000 already in use`
```bash
# Đổi sang port khác
uvicorn api.main:app --port 8001
```

### Lỗi: `No module named 'api'`
```bash
# Đảm bảo đang ở đúng thư mục
cd noise_filter
uvicorn api.main:app --reload
```

### API không truy cập được từ máy khác
```bash
# Đảm bảo dùng --host 0.0.0.0
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Kiểm tra firewall Windows (cho phép port 8000)
```

---

## 🧪 Test nhanh

### Test với cURL:
```bash
curl -X POST "http://localhost:8000/file/process" \
  -F "file=@path/to/audio.wav"
```

### Test với Python:
```python
import requests

url = "http://localhost:8000/file/process"
files = {"file": open("audio.wav", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

---

## 📦 Dependencies

- **numpy** - Tính toán mảng
- **scipy** - Xử lý tín hiệu (exp1)
- **librosa** - STFT/iSTFT
- **soundfile** - Đọc/ghi WAV
- **matplotlib** - Visualization
- **fastapi** - Web framework
- **uvicorn** - ASGI server
- **sqlalchemy** - Database ORM
- **pydantic** - Data validation

---

## 👨‍💻 Phát triển thêm

### Thêm bộ lọc mới:
1. Tạo file trong `filter/` (VD: `my_filter.py`)
2. Import trong `api/audio_service.py`
3. Thêm vào hàm `process_audio_file()`

### Thay đổi database:
- File SQLite: `noise_filter/audio_processing.db`
- Models: `api/database.py`

### Tùy chỉnh CORS:
- File: `api/main.py`
- Thay `allow_origins=["*"]` thành domain cụ thể

---

## 📄 License

MIT License

## 🔗 Links

- **GitHub:** https://github.com/dtduy77/DSP501.22_Assessment
- **Issues:** https://github.com/dtduy77/DSP501.22_Assessment/issues

---

**Made with ❤️ for DSP501.22**