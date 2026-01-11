"""
API Server for YouTube Scraper & Translator.
Provides endpoints for searching, downloading, and monitoring tasks.
"""
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict
from enum import Enum
import uuid
from datetime import datetime
from pathlib import Path
import os
import subprocess
import time as time_module

# Import core logic
from search import search_videos
from download import download_video
from burn import burn_subtitles
from config import DOWNLOADS_DIR, OUTPUT_DIR

app = FastAPI(title="YouTube Scraper & Translator API")

# Enable CORS for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory dictionary to store task progress (simplified for this demo)
TASKS: Dict[str, Dict] = {}


# --- Data Models ---

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class SubtitlePosition(str, Enum):
    BOTTOM = "bottom"
    TOP = "top"
    MID = "mid"

class SubtitleConfig(BaseModel):
    font_color: str = "#FFFFFF"
    position: SubtitlePosition = SubtitlePosition.BOTTOM
    languages: List[str] = ["zh", "en"]
    font_size: int = 40

class DownloadRequest(BaseModel):
    url: HttpUrl
    style: Optional[SubtitleConfig] = None
    cookies_file: Optional[str] = None # Or handle upload

class SearchResult(BaseModel):
    title: str
    url: str
    duration: str
    upload_date: str
    views: str
    description: str
    thumbnail_url: str # To be added to search.py if not present

class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    message: str
    progress: float
    result_path: Optional[str] = None


# --- Helper Functions ---


def hex_to_ass_color(hex_color: str) -> str:
    """Convert HEX #RRGGBB to ASS &HBBGGRR."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        r, g, b = hex_color[:2], hex_color[2:4], hex_color[4:]
        return f"&H{b}{g}{r}"
    return "&HFFFFFF"

def run_pipeline(task_id: str, request: DownloadRequest):
    TASKS[task_id]["status"] = TaskStatus.RUNNING
    TASKS[task_id]["progress"] = 0.1
    TASKS[task_id]["message"] = "Downloading video..."
    
    try:
        # Define callback to update global task state
        def update_progress(pct: float, msg: str):
            TASKS[task_id]["progress"] = pct
            TASKS[task_id]["message"] = msg
            
        update_progress(0.05, "Starting download...")
        
        # Check if cookies file exists
        cookies_path = "cookies.txt" if Path("cookies.txt").exists() else None
        
        paths = download_video(
            url=str(request.url),
            download_subs=True,
            cookies_file=cookies_path,
            progress_callback=update_progress
        )
        
        if not paths:
            raise Exception("Download failed")
            
        video_path = paths['video']
        sub_path = paths.get('subtitle')
        
        # Check if subtitles were downloaded
        if not sub_path and not Path(str(video_path).rsplit('.', 1)[0] + '.en.srt').exists():
             # Fallback logic if subtitle key is missing but file exists...
             pass

        TASKS[task_id]["progress"] = 0.6
        TASKS[task_id]["message"] = "Processing subtitles (Burning)..."

        # 2. Burn Subtitles
        # Construct style dict for burn.py (Mapped to ASS format)
        style_args = None
        if request.style:
            # Map API params to ASS style keys
            # Alignment: 2=Bottom Center, 8=Top Center, 5=Middle Center
            alignment_map = {
                SubtitlePosition.BOTTOM: '2',
                SubtitlePosition.TOP: '8',
                SubtitlePosition.MID: '5'
            }
            
            style_args = {
                "PrimaryColour": hex_to_ass_color(request.style.font_color),
                "FontSize": request.style.font_size,
                "Alignment": alignment_map.get(request.style.position, '2'),
            }

        output_path = burn_subtitles(
            video_path=video_path,
            subtitle_path=sub_path,
            style=style_args 
        )
        
        if output_path:
            TASKS[task_id]["status"] = TaskStatus.COMPLETED
            TASKS[task_id]["progress"] = 1.0
            TASKS[task_id]["message"] = "Done"
            TASKS[task_id]["result_path"] = str(output_path)
        else:
            raise Exception("Burning failed")

    except Exception as e:
        TASKS[task_id]["status"] = TaskStatus.FAILED
        TASKS[task_id]["message"] = str(e)


# --- Endpoints ---

class SearchResponse(BaseModel):
    items: List[SearchResult]
    latency: float

@app.post("/api/search", response_model=SearchResponse)
def search_endpoint(
    query: str, 
    max_results: int = 10,
    duration_min: int = 0,
    duration_max: int = 3600,
    upload_date: str = "now-30days"
):
    import search
    
    results, latency = search.search_videos(
        query=query, 
        max_results=max_results, 
        duration_min=duration_min,
        duration_max=duration_max,
        upload_date=upload_date,
        no_filter=False 
    )
    
    mapped_results = []
    for r in results:
        thumb = r.get('thumbnail') or f"https://img.youtube.com/vi/{r['id']}/hqdefault.jpg"
        mapped_results.append(SearchResult(
            title=r.get('title', 'Unknown'),
            url=r.get('url', ''),
            duration=r.get('duration_formatted', '0:00'),
            views=str(r.get('view_count', 0)),
            upload_date=r.get('upload_date', 'Unknown'),
            description=r.get('description', ''),
            thumbnail_url=thumb
        ))
        
    return SearchResponse(items=mapped_results, latency=latency)


@app.post("/api/tasks", response_model=TaskResponse)
def create_task(request: DownloadRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    TASKS[task_id] = {
        "task_id": task_id,
        "status": TaskStatus.PENDING,
        "message": "Queued",
        "progress": 0.0,
        "created_at": datetime.now()
    }
    
    background_tasks.add_task(run_pipeline, task_id, request)
    
    return TASKS[task_id]


@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: str):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    return TASKS[task_id]

@app.get("/api/tasks")
def list_tasks():
    return list(TASKS.values())

def _shutdown_server():
    """Helper to kill processes."""
    time_module.sleep(1) # Give time for response to send
    
    # Kill Streamlit (blind attempts)
    subprocess.run("taskkill /F /IM streamlit.exe", shell=True, capture_output=True)
    
    # Kill Self
    pid = os.getpid()
    subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)

@app.post("/api/shutdown")
def shutdown_endpoint(background_tasks: BackgroundTasks):
    background_tasks.add_task(_shutdown_server)
    return {"message": "System shutting down..."}
