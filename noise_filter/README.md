
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
python run_wiener.py
```

➡ Output: `results/wiener_output.wav`

---

### wiener_smooth Filter

```
python run_wiener_smooth.py
```

➡ Output: `results/wiener_smooth_output_1.wav`




