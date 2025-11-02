# Dance Movement Analysis Server

A cloud-based AI/ML server that processes dance videos for body pose and movement analysis using MediaPipe and OpenCV. The server detects 33 body keypoints, overlays skeleton visualization, and provides detailed movement analytics through a REST API.

## Features

- **Pose Detection**: Real-time body keypoint detection using MediaPipe Pose (BlazePose model)
- **Dual Video Output**: 
  - Original video with skeleton overlay
  - Skeleton-only video on black background
- **REST API**: FastAPI-based endpoints for video upload and analysis
- **Asynchronous Processing**: Background job processing for efficient handling
- **Containerized**: Docker support for easy deployment
- **Cloud-Ready**: Deployment scripts for GCP Compute Engine
- **Comprehensive Analytics**: Movement statistics, detection rates, and keypoint data

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

### Usage Examples

#### 1. Upload a video for analysis

```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "video=@dance.mp4" \
  -F "min_detection_confidence=0.5" \
  -F "min_tracking_confidence=0.5"
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Video uploaded successfully. Analysis started.",
  "result_url": "/api/v1/status/550e8400-e29b-41d4-a716-446655440000"
}
```

#### 2. Check job status

```bash
curl "http://localhost:8000/api/v1/status/550e8400-e29b-41d4-a716-446655440000"
```

**Response (processing):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "created_at": "2025-11-02T10:30:00"
}
```

**Response (completed):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "created_at": "2025-11-02T10:30:00",
  "completed_at": "2025-11-02T10:32:45",
  "results": {
    "total_frames": 1373,
    "detected_frames": 1373,
    "detection_rate": 100.0,
    "fps": 30,
    "resolution": [720, 1280]
  },
  "output_video_url": "/api/v1/download/550e8400-e29b-41d4-a716-446655440000"
}
```

#### 3. Download analyzed videos

```bash
# Download overlay version (original + skeleton)
curl -O "http://localhost:8000/api/v1/download/550e8400-e29b-41d4-a716-446655440000"

# Get JSON results
curl "http://localhost:8000/api/v1/results/550e8400-e29b-41d4-a716-446655440000"
```

### Python Example

```python
import requests
import time

# Upload video
url = "http://localhost:8000/api/v1/analyze"
files = {"video": open("dance.mp4", "rb")}
data = {"min_detection_confidence": 0.5}

response = requests.post(url, files=files, data=data)
job_id = response.json()["job_id"]
print(f"Job ID: {job_id}")

# Poll for completion
status_url = f"http://localhost:8000/api/v1/status/{job_id}"
while True:
    status = requests.get(status_url).json()
    print(f"Status: {status['status']}")
    
    if status["status"] == "completed":
        break
    elif status["status"] == "failed":
        print(f"Error: {status.get('error')}")
        exit(1)
    
    time.sleep(5)

# Download result
download_url = f"http://localhost:8000/api/v1/download/{job_id}"
result = requests.get(download_url)
with open("analyzed_dance.mp4", "wb") as f:
    f.write(result.content)

print("Analysis complete! Video saved as analyzed_dance.mp4")
```

## Output Files

When processing a video, the system generates TWO output videos:

1. **Overlay Version** (`output.mp4`)
   - Original video with skeleton overlay
   - Shows dancer with pose landmarks drawn on top

2. **Skeleton-Only Version** (`output_skeleton_only.mp4`)
   - Skeleton dancing on black background
   - Shows only the detected pose without original video

Both files are available for download via the API.

## Architecture

```
┌─────────────────┐
│  Client/User    │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌────────────────┐
│   FastAPI      │
│   API Server   │
└────────┬───────┘
         │ Async Tasks
         ▼
┌────────────────┐
│ Dance Analyzer │
│  (MediaPipe +  │
│    OpenCV)     │
└────────┬───────┘
         │
         ▼
┌────────────────┐
│  Video Output  │
│  1. Overlay    │
│  2. Skeleton   │
└────────────────┘
```

## MediaPipe Pose Detection

The system uses Google's MediaPipe Pose (BlazePose) model which detects 33 body landmarks:

- Face: nose, eyes, ears, mouth
- Torso: shoulders, hips
- Arms: elbows, wrists, hands
- Legs: knees, ankles, feet

Each landmark includes:
- `x, y, z`: 3D coordinates (normalized 0-1)
- `visibility`: Confidence score (0-1)

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

## Cloud Deployment

See `DEPLOYMENT_INSTRUCTIONS.md` for detailed deployment guide to:
- Google Cloud Platform (GCP) Compute Engine
- AWS EC2
- Other cloud providers

Quick GCP deployment:

```bash
# 1. Create VM instance
gcloud compute instances create dance-analysis-vm \
    --machine-type=e2-medium \
    --zone=us-central1-a \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=20GB

# 2. Upload files
gcloud compute scp --recurse \
  dance_analyzer.py api_server.py requirements.txt \
  Dockerfile docker-compose.yml deploy_gcp.sh \
  dance-analysis-vm:~/dance-analysis-server/ \
  --zone=us-central1-a

# 3. Deploy
gcloud compute ssh dance-analysis-vm --zone=us-central1-a
cd ~/dance-analysis-server
chmod +x deploy_gcp.sh
./deploy_gcp.sh
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

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs dance-analysis-server

# Verify port availability
netstat -tulpn | grep 8000
```

### Low detection rate
- Ensure good lighting in videos
- Check that person is clearly visible and not too far from camera
- Try adjusting confidence parameters (lower for more detections)

### Out of memory
- Reduce video resolution before uploading
- Process shorter video segments
- Increase instance memory (for cloud deployments)

## File Structure

```
dance-analysis-server/
├── dance_analyzer.py           # Core pose detection & analysis
├── api_server.py              # FastAPI REST API server
├── test_dance_analyzer.py     # Unit tests
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker container definition
├── docker-compose.yml         # Docker Compose configuration
├── deploy_gcp.sh             # GCP deployment script
├── .dockerignore             # Docker build exclusions
├── .gitignore                # Git exclusions
├── README.md                 # This file
└── DEPLOYMENT_INSTRUCTIONS.md # Deployment guide
```

## License

MIT License

## Credits

- MediaPipe by Google
- OpenCV
- FastAPI by Sebastián Ramírez

## Support

For issues and questions:
- Check the troubleshooting section above
- Review API documentation at `/docs`
- Check logs: `docker logs dance-analysis-server`

---

**Built for dance movement analysis and pose estimation**

