# DSP501.22_Assessment — Audio Denoiser

This repository contains a complete demo for audio noise reduction: a FastAPI backend that runs several denoising filters (Wiener, MMSE-LSA, etc.) and a Streamlit frontend for uploading audio, running processing, visualizing results (spectrum & waveform), and browsing history.

Contents
--------
- `frontend/` — Streamlit UI (upload, playback, visualization, history)
- `backend/` — Noise filtering API (FastAPI) and processing scripts
- `song/`, `data/`, `results/`, etc. — example or outputs

This README combines setup and usage for both frontend and backend to make it easy to get the whole system running locally.

Quick links
-----------
- Frontend (Streamlit): `frontend/app.py`
- Backend API (FastAPI): `backend/noise_filter/api/main.py` (depending on branch)

Prerequisites
-------------
- Python 3.8+ (3.11 recommended)
- pip

Recommended workflow
--------------------
1. Create and activate a virtual environment
2. Install backend dependencies and start the API
3. Install frontend dependencies and run Streamlit

1) Create virtual environment
------------------------------
Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\activate
```

macOS / Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

2) Backend setup & run (noise_filter)
------------------------------------
There are two backend folders in this repository depending on versions: `backend/noise_filter/`. Use the one that matches your local layout. The API uses FastAPI + uvicorn.

Install backend dependencies (from the appropriate folder):

```powershell
cd backend\noise_filter
pip install -r requirement.txt
cd ..\..\backendv2\noise_filter
pip install -r requirement.txt
```

If the project provides a `requirements.txt` in the root `backend/` folder, you can also install from there.

Chromaprint (optional, for song detection)
----------------------------------------
The backend can detect songs using Chromaprint (`fpcalc`). For Windows there is a helper script in the backend README to download `fpcalc.exe`. If you need song detection, place `fpcalc.exe` in the noise_filter folder and set your AcoustID API key in `.env`.

Run the API server
------------------

```powershell
cd backend\noise_filter
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Open: `http://localhost:8000/docs` to view API docs.

API endpoints (high level)
--------------------------
- `POST /file/process` — upload a WAV file and process it. Returns JSON metadata with `original_file`, `processed_file`, `comparison`, `date_process`, etc.
- `GET /file` — list processed files (history)
- `GET /file/{id}` — details for a processed file

Example response from `/file/process`:

```json
{
  "id": 1,
  "song_name": "Example Song",
  "original_file": "/audio/uploads/example.wav",
  "processed_file": "/audio/results/example_processed.wav",
  "file_size_kb": 123.4,
  "date_process": "2025-11-19T21:30:00",
  "comparison": { ... }
}
```

3) Frontend setup & run (Streamlit)
-----------------------------------
The frontend is implemented with Streamlit and lives in `frontend/`.

Install frontend dependencies:

```powershell
cd frontend
pip install -r requirements.txt
pip install streamlit pandas numpy matplotlib scipy requests
```

Run the Streamlit app:

```powershell
cd frontend
streamlit run app.py
```

Open: `http://localhost:8501` (default)

How the frontend works
----------------------
- Upload a WAV (or MP3 if `pydub`+`ffmpeg` installed) using the file uploader
- The app converts MP3 → WAV in-memory (if needed) and sends WAV bytes to `API_URL` (default: `http://localhost:8000/file/process`)
- Backend returns processed file paths and comparison metrics
- Frontend displays side-by-side audio players, frequency spectrum (FFT), waveform plots, and a comparison table
- History and Detail pages are implemented under `frontend/pages/`

Project structure (important files)
-----------------------------------

```
DSP501.22_Assessment/
├── frontend/
│   ├── app.py
│   ├── sidebar.py
│   └── pages/
│       ├── history.py
│       └── detail.py
├── backend/
│   └── noise_filter/
│       ├── api/
│       │   └── main.py
│       ├── filter/
│       ├── utils/
│       ├── uploads/
│       └── results/
└── README.md
```

Troubleshooting
---------------

- "Lỗi kết nối server": Ensure backend is running on `http://localhost:8000` and not blocked by firewall. Start with:

```powershell
cd backend\noise_filter
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

- Missing Python package errors: Install dependencies from the appropriate `requirements.txt` or run `pip install <package>`.

- Files not found for plotting (frontend expects backend `results/` paths): Verify `add_noisy_suffix()` and `base_dir` in `frontend/app.py` point to the correct backend results directory (sometimes backend folder is `backend`).

Notes on configuration
----------------------
- API URL in frontend is set by `API_URL` variable in `frontend/app.py` (and similar in `pages/detail.py` / `pages/history.py`). Change it to your deployed backend URL when needed.
- If deploying Streamlit publicly, set the backend URL in `.streamlit/secrets.toml` or environment variables and avoid hardcoding.

Development & contribution
--------------------------
- Add new filters: create a module in `noise_filter/filter/` and register/use it in the backend audio service.
- Improve frontend visualizations: update `frontend/app.py` or `pages/detail.py`.
- Run individual filter scripts in `noise_filter/` to test algorithms without API (e.g. `run_wiener_smooth.py`).

Quick testing
-------------
Test backend with cURL:

```bash
curl -X POST "http://localhost:8000/file/process" -F "file=@path/to/audio.wav"
```

Test backend with Python:

```python
import requests
files = {"file": open("audio.wav","rb")}
print(requests.post("http://localhost:8000/file/process", files=files).json())
```

License & Author
----------------
MIT License — part of **DSP501.22_Assessment** by @dtduy77

---