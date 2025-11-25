# Audio Denoiser Frontend

A modern **Streamlit-based web application** for audio denoising and noise reduction. Upload WAV files, process them through multiple filtering algorithms, and visualize the results with real-time frequency analysis.

## Features

### Core Functionality
- **File Upload**: Support for WAV formats (up to ~100MB)
- **Multi-Algorithm Processing**: Compare different noise filtering methods (MMSE-LSA, Wiener, etc.)
- **Real-time Audio Playback**: Listen to original and processed audio directly in the browser
- **Performance Metrics**: Detailed comparison table showing improvement %, execution time, and filter performance
- **Download Processed Audio**: One-click download of cleaned audio files

### Visualization & Analysis
- **Frequency Spectrum Analysis**: FFT-based frequency comparison (original vs. processed)
- **Waveform Visualization**: Full-duration amplitude-over-time graphs
- **Zoomed Detail View**: 10-second preview showing noise floor reduction in detail
- **Interactive Charts**: Matplotlib-powered interactive plots with grid and legends

### History & Dashboard
- **Processing History**: Browse all previously processed files
- **Detailed Records**: View individual processing details with metadata
- **Cached Data**: Quick access to past results with API fallback

## Project Structure

```
frontend/
├── app.py                    # Main processing page (upload → analyze → download)
├── sidebar.py                # Shared sidebar navigation component
├── pages/
│   ├── history.py            # History/Dashboard page with clickable records
│   └── detail.py             # Detailed view of individual processed files
└── README.md                 # This file
```

### File Descriptions

#### `app.py` (Main Page)
- Upload and process audio files
- Display comparison metrics across multiple algorithms
- Render frequency spectrum and waveform visualizations
- Download cleaned audio

**Key Sections:**
- File upload handler (lines 39–43)
- Audio playback UI (columns layout)
- Comparison metrics table
- Frequency spectrum plot (FFT analysis)
- Amplitude-over-time waveform with zoom capability

#### `sidebar.py` (Navigation)
- Shared Streamlit sidebar rendered on all pages
- Navigation links: Main page → History page
- Branding and app title

#### `pages/history.py` (History & Dashboard)
- Fetch processing history from backend API
- Display in sortable, clickable table (newest first)
- Click any song name to view detailed results
- Refresh button to reload cached data
- Fallback to local session storage if API unavailable

#### `pages/detail.py` (Detail Page)
- Query-param based URL routing (`?selected_id=<ID>`)
- Fetch individual file metadata and audio files
- Audio playback for original and processed versions
- Comparison metrics display
- Full-duration frequency spectrum and waveform
- Zoomed 10-second preview for visual noise reduction proof

## Getting Started

### Prerequisites
- **Python 3.8+**
- **Streamlit** (`pip install streamlit`)
- **Dependencies** (see requirements below)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/dtduy77/DSP501.22_Assessment.git
   cd frontend
   ```

2. **Create virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Running the App

```bash
# From the frontend directory
streamlit run app.py
```

The app will start on `http://localhost:8501` by default.

**Note:** Ensure the backend API is running on `http://localhost:8000/file/process` (configurable in code).

## Dependencies

```
streamlit>=1.28.0
pandas>=1.5.0
numpy>=1.23.0
matplotlib>=3.6.0
scipy>=1.9.0
requests>=2.28.0
```

Install all with:
```bash
pip install streamlit pandas numpy matplotlib scipy requests
```

## API Integration

### Backend Endpoint
- **URL:** `http://localhost:8000/file/process`
- **Method:** POST
- **Content-Type:** multipart/form-data
- **Input:** WAV audio file
- **Output (JSON):**
  ```json
  {
    "song_name": "Song Title",
    "original_file": "/audio/uploads/...",
    "processed_file": "/audio/results/...",
    "file_size_kb": 1024,
    "date_process": "2024-11-25T10:30:00",
    "comparison": {
      "filter_a": {
        "improvement_percent": 23.5,
        "performance": 0.85,
        "time_seconds": 0.5
      }
    }
  }
  ```

### History Endpoint
- **URL:** `http://localhost:8000/file`
- **Method:** GET
- **Output:** JSON array of processed files

### Detail Endpoint
- **URL:** `http://localhost:8000/file/{id}`
- **Method:** GET
- **Output:** Single file metadata + paths

## Usage Guide

### 1. **Process an Audio File**
   - Open `http://localhost:8501` (Main page)
   - Click "Chọn file WAV"
   - Upload a WAV file
   - Click "Xử lí âm thanh" (Process)
   - Wait for backend processing (may take several seconds)

### 2. **View Results**
   - Listen to original audio (with noise) and processed audio (clean)
   - Check "Bảng So Sánh Bộ Lọc" for performance metrics
   - Review frequency spectrum to see noise reduction visually
   - Check waveform visualization and zoom to spot noise floor reduction

### 3. **Download Cleaned Audio**
   - Click "Tải file sạch ngay" (Download cleaned file)
   - File downloads as `cleaned_<filename>.wav`

### 4. **Browse History**
   - Click "Lịch sử" (History) in the sidebar
   - View all processed files sorted by date
   - Click any song name to view detailed analysis
   - Use "🔄 Refresh" to reload latest records

## UI Components

### Main Page Sections
| Section | Purpose |
|---------|---------|
| Upload Panel | File selection and processing trigger |
| Audio Playback | Side-by-side original vs. processed audio |
| Metrics Table | Algorithm comparison (improvement %, performance, time) |
| Frequency Spectrum | FFT-based frequency domain visualization |
| Waveform | Time-domain amplitude graphs with zoom |

### Color Scheme
- **Original Audio (Noisy):** Red (#ff4444) – indicates presence of noise
- **Processed Audio (Clean):** Green (#00aa00) – indicates noise reduction
- **Accent Colors:** Blue (#1E90FF) for interactive elements

## Configuration

### API URL
Edit the `API_URL` variable in `app.py`, `detail.py`, or `history.py`:
```python
API_URL = "http://localhost:8000/file/process"
```

### File Size Limit
Modify the uploader help text or backend settings:
```python
uploaded_file = st.file_uploader(
    "...",
    help="Tối đa ~100MB"
)
```

### Cache TTL (History Page)
Adjust cache refresh interval in `history.py`:
```python
@st.cache_data(ttl=15, show_spinner=False)
```

## Data Flow

```
User Upload
    ↓
File Reader (WAV)
    ↓
Backend API Process
    ↓
API Returns Metadata + File Paths
    ↓
UI Renders Audio + Visualizations
    ↓
User Downloads or Views History
```

## Troubleshooting

### "Lỗi kết nối server"
- **Solution:** Ensure backend API is running on `http://localhost:8000`
  ```bash
  cd backend/noise_filter
  uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
  ```

### Files not found on disk (waveform/spectrum won't render)
- **Solution:** Check file paths in `add_noisy_suffix()` function
- Ensure backend is saving files to expected locations
- Verify `base_dir` path points to correct backend folder

### Page not updating after processing
- **Solution:** Click "Refresh" on History page to clear cache

## Development Notes

### Multi-Page Routing
Streamlit uses file paths for routing:
- `app.py` → `/` (home)
- `pages/history.py` → `/history`
- `pages/detail.py` → `/detail?selected_id=<ID>`

### Caching Strategy
- History data cached for 15 seconds (reduces API calls)
- Spectrum/waveform plots generated on-demand
- Audio files streamed directly from backend URLs

### Performance Considerations
- Large files (>100MB) may timeout (adjust `timeout=600`)
- FFT computation scales with file duration
- Consider downsampling for very long audio files

## License

This project is part of **DSP501.22_Assessment** by @dtduy77.

## Author

Developed with ❤️ for audio signal processing education.

---

**Questions or Issues?** Open an issue on GitHub or contact the maintainer.
