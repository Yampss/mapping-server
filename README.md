# Dance Movement Analysis Server

A cloud-based AI/ML server that processes dance videos for body pose and movement analysis. The server detects 33 body keypoints, overlays skeleton visualization, and provides detailed movement analytics through a REST API.


## Requirements

### System Requirements
- Python 3.10+
- Docker & Docker Compose (for containerized deployment)
- 2GB+ RAM
- 10GB+ disk space

### Python Dependencies
See `requirements.txt` for complete list. Main dependencies:
- opencv-python==4.8.1.78
- mediapipe==0.10.21
- numpy==1.24.3
- fastapi==0.104.1
- uvicorn[standard]==0.24.0

## Quick Start

### Option 1: Local Development (without Docker)

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Run the API server**
```bash
python api_server.py
```

The server will be available at `http://localhost:8000`

3. **Test with a video**
```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "video=@your_dance_video.mp4"
```

### Option 2: Docker (Recommended)

1. **Build and run with Docker Compose**
```bash
docker-compose up -d
```

2. **Check status**
```bash
docker-compose ps
docker logs -f dance-analysis-server
```

3. **Test the API**
```bash
curl http://localhost:8000/health
```

4. **Stop the server**
```bash
docker-compose down
```

## API Documentation

### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information and available endpoints |
| `/health` | GET | Health check status |
| `/api/v1/analyze` | POST | Upload and analyze video |
| `/api/v1/status/{job_id}` | GET | Check job status |
| `/api/v1/download/{job_id}` | GET | Download analyzed video (overlay) |
| `/api/v1/results/{job_id}` | GET | Get analysis results (JSON) |
| `/api/v1/jobs` | GET | List all jobs |
| `/api/v1/jobs/{job_id}` | DELETE | Delete job |

### Interactive API Documentation

FastAPI provides automatic interactive documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`


## Configuration

Default settings can be adjusted in `api_server.py`:

```python
# Storage directories
UPLOAD_DIR = "/tmp/uploads"
OUTPUT_DIR = "/tmp/outputs"
RESULTS_DIR = "/tmp/results"

# Detection parameters
min_detection_confidence = 0.5  # Lower = more detections, more false positives
min_tracking_confidence = 0.5   # Lower = less smooth, more responsive
```

## Testing

### Run Unit Tests

```bash
python test_dance_analyzer.py
```

### Test with Coverage

```bash
pytest test_dance_analyzer.py --cov=dance_analyzer --cov-report=html
```


## Performance

### Processing Speed
- 5-second video (150 frames): ~10-15 seconds
- 30-second video (900 frames): ~60-90 seconds
- 60-second video (1800 frames): ~120-180 seconds

Speed depends on:
- CPU cores and clock speed
- Video resolution (720p vs 1080p)
- Detection confidence thresholds

### Detection Accuracy
- Good lighting + clear visibility: 90-98% detection rate
- Moderate lighting: 80-90% detection rate
- Dim lighting or occlusions: 70-85% detection rate

---


