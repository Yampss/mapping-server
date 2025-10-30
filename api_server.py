

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import os
import uuid
import shutil
import logging
from datetime import datetime
import json

from dance_analyzer import analyze_dance_video

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Dance Movement Analysis API",
    description="API for analyzing dance movements in videos using pose estimation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_DIR = "/tmp/uploads"
OUTPUT_DIR = "/tmp/outputs"
RESULTS_DIR = "/tmp/results"

# Create directories if they don't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# In-memory storage for analysis jobs (in production, use Redis or database)
analysis_jobs = {}


class AnalysisRequest(BaseModel):
    """Request model for analysis parameters"""
    min_detection_confidence: Optional[float] = 0.5
    min_tracking_confidence: Optional[float] = 0.5


class AnalysisResponse(BaseModel):
    """Response model for analysis results"""
    job_id: str
    status: str
    message: str
    result_url: Optional[str] = None


class JobStatus(BaseModel):
    """Model for job status"""
    job_id: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    results: Optional[dict] = None
    output_video_url: Optional[str] = None
    error: Optional[str] = None


def cleanup_old_files(directory: str, max_age_hours: int = 24):
    """Clean up files older than specified hours"""
    try:
        current_time = datetime.now().timestamp()
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getmtime(filepath)
                if file_age > (max_age_hours * 3600):
                    os.remove(filepath)
                    logger.info(f"Cleaned up old file: {filename}")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


async def process_video_analysis(
    job_id: str,
    input_path: str,
    output_path: str,
    min_detection_confidence: float,
    min_tracking_confidence: float
):
    """Background task to process video analysis"""
    try:
        logger.info(f"Starting analysis for job {job_id}")
        
        # Update job status
        analysis_jobs[job_id]['status'] = 'processing'
        
        # Perform analysis
        results = analyze_dance_video(
            input_path,
            output_path,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        # Save results to file
        results_path = os.path.join(RESULTS_DIR, f"{job_id}_results.json")
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Update job status
        analysis_jobs[job_id].update({
            'status': 'completed',
            'completed_at': datetime.now().isoformat(),
            'results': results,
            'output_video_path': output_path,
            'results_path': results_path
        })
        
        logger.info(f"Analysis completed for job {job_id}")
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}")
        analysis_jobs[job_id].update({
            'status': 'failed',
            'completed_at': datetime.now().isoformat(),
            'error': str(e)
        })


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Dance Movement Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/api/v1/analyze",
            "status": "/api/v1/status/{job_id}",
            "download": "/api/v1/download/{job_id}",
            "results": "/api/v1/results/{job_id}",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_jobs": len([j for j in analysis_jobs.values() if j['status'] == 'processing'])
    }


@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def analyze_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    min_detection_confidence: float = 0.5,
    min_tracking_confidence: float = 0.5
):
    
    # Validate file type
    allowed_extensions = ['.mp4', '.avi', '.mov', '.MP4', '.AVI', '.MOV']
    file_ext = os.path.splitext(video.filename)[1]
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded file
    input_filename = f"{job_id}_input{file_ext}"
    input_path = os.path.join(UPLOAD_DIR, input_filename)
    
    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)
        
        logger.info(f"Video uploaded for job {job_id}: {video.filename}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {e}")
    
    # Prepare output path
    output_filename = f"{job_id}_output.mp4"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    # Create job record
    analysis_jobs[job_id] = {
        'job_id': job_id,
        'status': 'queued',
        'created_at': datetime.now().isoformat(),
        'input_filename': video.filename,
        'input_path': input_path,
        'output_path': output_path
    }
    
    # Start background processing
    background_tasks.add_task(
        process_video_analysis,
        job_id,
        input_path,
        output_path,
        min_detection_confidence,
        min_tracking_confidence
    )
    
    # Clean up old files
    background_tasks.add_task(cleanup_old_files, UPLOAD_DIR)
    background_tasks.add_task(cleanup_old_files, OUTPUT_DIR)
    background_tasks.add_task(cleanup_old_files, RESULTS_DIR)
    
    return AnalysisResponse(
        job_id=job_id,
        status="queued",
        message="Video uploaded successfully. Analysis started.",
        result_url=f"/api/v1/status/{job_id}"
    )


@app.get("/api/v1/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = analysis_jobs[job_id]
    
    response = JobStatus(
        job_id=job_id,
        status=job['status'],
        created_at=job['created_at'],
        completed_at=job.get('completed_at'),
        results=job.get('results'),
        error=job.get('error')
    )
    
    if job['status'] == 'completed':
        response.output_video_url = f"/api/v1/download/{job_id}"
    
    return response


@app.get("/api/v1/download/{job_id}")
async def download_video(job_id: str):
    
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = analysis_jobs[job_id]
    
    if job['status'] != 'completed':
        raise HTTPException(
            status_code=400,
            detail=f"Analysis not completed. Current status: {job['status']}"
        )
    
    output_path = job.get('output_path')
    
    if not output_path or not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Output video not found")
    
    return FileResponse(
        output_path,
        media_type="video/mp4",
        filename=f"analyzed_{job_id}.mp4"
    )


@app.get("/api/v1/results/{job_id}")
async def get_results(job_id: str):
    
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = analysis_jobs[job_id]
    
    if job['status'] != 'completed':
        raise HTTPException(
            status_code=400,
            detail=f"Analysis not completed. Current status: {job['status']}"
        )
    
    results_path = job.get('results_path')
    
    if not results_path or not os.path.exists(results_path):
        # Return inline results if file not found
        return job.get('results', {})
    
    return FileResponse(
        results_path,
        media_type="application/json",
        filename=f"results_{job_id}.json"
    )


@app.delete("/api/v1/jobs/{job_id}")
async def delete_job(job_id: str):
    
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = analysis_jobs[job_id]
    
    # Delete files
    for path_key in ['input_path', 'output_path', 'results_path']:
        path = job.get(path_key)
        if path and os.path.exists(path):
            try:
                os.remove(path)
                logger.info(f"Deleted file: {path}")
            except Exception as e:
                logger.error(f"Error deleting file {path}: {e}")
    
    # Remove from jobs dictionary
    del analysis_jobs[job_id]
    
    return {"message": f"Job {job_id} deleted successfully"}


@app.get("/api/v1/jobs")
async def list_jobs():
    
    jobs_list = []
    for job_id, job in analysis_jobs.items():
        jobs_list.append({
            'job_id': job_id,
            'status': job['status'],
            'created_at': job['created_at'],
            'input_filename': job.get('input_filename')
        })
    
    return {
        "total_jobs": len(jobs_list),
        "jobs": jobs_list
    }


if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
