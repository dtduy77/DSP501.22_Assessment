
Cài đặt (Setup)

. Cài đặt công cụ `fpcalc` (Bắt buộc)

Thư viện cần file thực thi `fpcalc` để trích xuất vân tay âm thanh.

1.  Truy cập: [AcoustID Downloads](https://acoustid.org/chromaprint).
2.  Tải xuống phiên bản **Windows (x86\_64)** dạng file **`.zip`**.
3.  Giải nén và copy file **`fpcalc.exe`** vào **thư mục gốc** của dự án (cùng cấp với file `run_detect_song.py`).

> **Lưu ý:** Nếu thiếu file này, chương trình sẽ báo lỗi và không thể hoạt động.

-----

## Cấu hình Bảo mật (Configuration)

Để bảo vệ API Key, hệ thống sử dụng biến môi trường thay vì hardcode trong source code.

1.  Đăng ký API Key miễn phí tại: [AcoustID Applications](https://acoustid.org/new-application).
2.  Tạo một file tên **`.env`** tại thư mục gốc dự án.
3.  Thêm nội dung sau vào file `.env`:

<!-- end list -->

```env
API_KEY=your_actual_api_key_here
```

*(Thay `your_actual_api_key_here` bằng key bạn vừa nhận được)*.

*(Chỉ detect được nhạc có bản quyền)*.

----




Tạo môi trường ảo bằng `uv`

```
uv venv .venv
```

### Kích hoạt môi trường

**Windows (PowerShell)**

```
.venv\Scripts\activate
```

**Linux / macOS**

```
source .venv/bin/activate
```

---

 Cài dependency

```
uv pip install -r requirements.txt
```



Chạy từng bộ lọc

###  Wiener Filter

```
python run_mmse_lsa.py
```

➡ Output: `results/lsa_output.wav`

---

### wiener_smooth Filter

```
python run_wiener_smooth.py
```

➡ Output: `results/wiener_smooth_output_1.wav`




🛠 Cài đặt (Setup)

. Cài đặt công cụ `fpcalc` (Bắt buộc)

Thư viện cần file thực thi `fpcalc` để trích xuất vân tay âm thanh.

1.  Truy cập: [AcoustID Downloads](https://acoustid.org/chromaprint).
2.  Tải xuống phiên bản **Windows (x86\_64)** dạng file **`.zip`**.
3.  Giải nén và copy file **`fpcalc.exe`** vào **thư mục gốc** của dự án (cùng cấp với file `run_detect_song.py`).

> ⚠️ **Lưu ý:** Nếu thiếu file này, chương trình sẽ báo lỗi và không thể hoạt động.

-----

## 🔐 Cấu hình Bảo mật (Configuration)

Để bảo vệ API Key, hệ thống sử dụng biến môi trường thay vì hardcode trong source code.

1.  Đăng ký API Key miễn phí tại: [AcoustID Applications](https://acoustid.org/new-application).
2.  Tạo một file tên **`.env`** tại thư mục gốc dự án.
3.  Thêm nội dung sau vào file `.env`:

<!-- end list -->

```env
API_KEY=your_actual_api_key_here
```

*(Thay `your_actual_api_key_here` bằng key bạn vừa nhận được)*.

*(Chỉ detect được nhạc có bản quyền)*.

-----