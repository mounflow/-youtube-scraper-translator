"""
YouTube Video Processor - FastAPI Backend
Commercial-grade task queue API with SSE streaming
"""

import asyncio
import json
import os
import re
import sys
import uuid
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# ─────────────────────────── App Setup ────────────────────────────

app = FastAPI(title="YouTube Video Processor API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ROOT = Path(__file__).parent
MAIN_PY_PATH = PROJECT_ROOT / "main.py"
OUTPUT_DIR = PROJECT_ROOT / "output"

# ─────────────────────────── Task Model ────────────────────────────

class TaskStatus(str, Enum):
    PENDING  = "pending"
    RUNNING  = "running"
    SUCCESS  = "success"
    FAILED   = "failed"
    CANCELED = "canceled"


class Task:
    def __init__(self, task_id: str, title: str, url: str, options: dict):
        self.id: str = task_id
        self.title: str = title
        self.url: str = url
        self.options: dict = options
        self.status: TaskStatus = TaskStatus.PENDING
        self.created_at: str = datetime.now().isoformat()
        self.started_at: Optional[str] = None
        self.finished_at: Optional[str] = None
        self.progress: float = 0.0
        self.current_step: str = ""
        self.logs: List[str] = []
        self.output_file: Optional[str] = None
        self._process: Optional[asyncio.subprocess.Process] = None
        # Event is created lazily inside an async context
        self._log_event: Optional[asyncio.Event] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "progress": self.progress,
            "current_step": self.current_step,
            "output_file": self.output_file,
            "log_count": len(self.logs),
        }

    def _get_log_event(self) -> asyncio.Event:
        """Lazily create asyncio.Event inside async context."""
        if self._log_event is None:
            self._log_event = asyncio.Event()
        return self._log_event

    def add_log(self, line: str):
        # 限制单条日志长度，防止SSE数据过大
        max_line_length = 2000
        if len(line) > max_line_length:
            line = line[:max_line_length] + "... [truncated]"

        self.logs.append(line)
        # Keep only last 500 lines to reduce memory usage
        if len(self.logs) > 500:
            self.logs = self.logs[-500:]
        # Signal waiting SSE consumers
        if self._log_event is not None:
            self._log_event.set()


# In-memory task store
tasks: Dict[str, Task] = {}

# ─────────────────────────── API Models ────────────────────────────

class SearchRequest(BaseModel):
    query: str
    duration_min: int = 60
    duration_max: int = 7200
    max_results: int = 8
    no_filter: bool = False
    cookies_file: str = "cookies.txt"


class CreateTaskRequest(BaseModel):
    title: str
    url: str
    thumbnail: str = ""
    style: str = "premium"
    dub: bool = False
    voice: str = "zh-CN-YunxiNeural"
    cookies_file: str = "cookies.txt"
    hardware_accel: bool = True
    smart_split: bool = True
    no_optimize: bool = False
    subtitle_lang: str = "en"  # 字幕语言选项


class BatchActionRequest(BaseModel):
    task_ids: List[str]
    action: str  # "start" | "delete"


# ─────────────────────────── Helpers ───────────────────────────────

def _format_duration(seconds) -> str:
    if not seconds:
        return "0:00"
    s = int(seconds)
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    if h:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"


def _format_views(count) -> str:
    if not count:
        return "—"
    n = int(count)
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


async def _run_task(task: Task):
    """Execute the processing pipeline for a task."""
    # Ensure log event created inside async context
    task._get_log_event()
    task.status = TaskStatus.RUNNING
    task.started_at = datetime.now().isoformat()
    task.progress = 0
    task.add_log(f"[{task.started_at}] Task started: {task.title}")

    opts = task.options
    cmd = [
        sys.executable, "-u", str(MAIN_PY_PATH),
        "-u", task.url,
        "-y",
        "--style", opts.get("style", "premium"),
    ]
    if opts.get("dub"):
        cmd += ["--dub", "--voice", opts.get("voice", "zh-CN-YunxiNeural")]
    if opts.get("cookies_file"):
        cmd += ["-c", opts["cookies_file"]]
    if opts.get("smart_split"):
        cmd.append("--audio-sync")
    if opts.get("no_optimize"):
        cmd.append("--no-optimize")
    if opts.get("subtitle_lang"):
        cmd += ["--subtitle-lang", opts["subtitle_lang"]]

    # Windows: create new process group so we can kill child processes too
    kwargs = {}
    if sys.platform == "win32":
        import subprocess
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(PROJECT_ROOT),
            **kwargs,
        )
        task._process = proc

        ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            decoded = line.decode("utf-8", errors="ignore").strip()
            clean = ANSI_ESCAPE.sub("", decoded)
            if not clean:
                continue

            task.add_log(clean)

            # Parse progress percentage
            pct = re.search(r"(\d+(?:\.\d+)?)%", clean)
            if pct:
                task.progress = min(float(pct.group(1)), 99.0)

            # Parse step
            if "Step 1" in clean or "Downloading" in clean:
                task.current_step = "download"
            elif "Step 2" in clean or "Step 3" in clean or "Validating" in clean:
                task.current_step = "subtitle"
            elif "Step 4" in clean or "Translating" in clean or "Translation" in clean:
                task.current_step = "translate"
            elif "Step 5" in clean or "Step 6" in clean or "Burn" in clean or "FFmpeg" in clean:
                task.current_step = "burn"
            elif "Dubbing" in clean or "TTS" in clean:
                task.current_step = "dub"

        await proc.wait()
        task._process = None

        if proc.returncode == 0:
            task.status = TaskStatus.SUCCESS
            task.progress = 100
            task.current_step = "done"
            # Try to find output file
            out_files = sorted(OUTPUT_DIR.glob("*.mp4"), key=lambda f: f.stat().st_mtime, reverse=True)
            if out_files:
                task.output_file = out_files[0].name
            task.add_log(f"[DONE] Processing finished successfully.")
        else:
            task.status = TaskStatus.FAILED
            task.current_step = "failed"
            print(f"DEBUG: Process exited with code {proc.returncode}", file=sys.stderr)
            print(f"Task options: {opts}", file=sys.stderr)
            task.add_log(f"[ERROR] Process exited with code {proc.returncode}")

    except asyncio.CancelledError:
        task.status = TaskStatus.CANCELED
        task.add_log("[CANCELED] Task was canceled.")
        if task._process:
            try:
                if sys.platform == "win32":
                    import subprocess
                    subprocess.call(["taskkill", "/F", "/T", "/PID", str(task._process.pid)])
                else:
                    task._process.kill()
            except Exception:
                pass
    except Exception as e:
        task.status = TaskStatus.FAILED
        err_msg = traceback.format_exc()
        # 保存详细错误日志到文件（带时间戳，不覆盖）
        import time
        error_log_path = PROJECT_ROOT / "logs" / f"error_{task.id[:8]}_{int(time.time())}.log"
        error_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(error_log_path, "w", encoding="utf-8") as f:
            f.write(f"Task ID: {task.id}\n")
            f.write(f"Task Title: {task.title}\n")
            f.write(f"Task URL: {task.url}\n")
            f.write(f"Task Options: {task.options}\n")
            f.write(f"Error Time: {datetime.now().isoformat()}\n")
            f.write("=" * 80 + "\n")
            f.write(err_msg)
        task.add_log(f"[ERROR] Exception ({type(e).__name__}): {e}")
        task.add_log(f"[ERROR] Detailed log saved to: logs/error_{task.id[:8]}_{int(time.time())}.log")
    finally:
        task.finished_at = datetime.now().isoformat()
        # Notify any waiting SSE streams
        if task._log_event:
            task._log_event.set()


# ──────────────────────────── Endpoints ────────────────────────────

@app.post("/api/search")
def search_videos(req: SearchRequest):
    """Search YouTube videos and return structured results."""
    try:
        import sys
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))
        from search import search_videos as search_yt

        raw_results, _ = search_yt(
            req.query,
            max_results=req.max_results,
            duration_min=req.duration_min,
            duration_max=req.duration_max,
            upload_date=None if req.no_filter else "now-30days",
            cookies_file=req.cookies_file if req.cookies_file else None,
            no_filter=req.no_filter,
        )

        results = []
        for vid in raw_results:
            url = vid.get("url", "")
            vid_id = vid.get("id") or (url.split("v=")[1].split("&")[0] if "v=" in url else "")
            thumbnail = (
                vid.get("thumbnail")
                or (f"https://img.youtube.com/vi/{vid_id}/hqdefault.jpg" if vid_id else "")
            )
            results.append({
                "id": vid_id,
                "title": vid.get("title", "Unknown"),
                "url": url,
                "duration": _format_duration(vid.get("duration", 0)),
                "duration_sec": vid.get("duration", 0),
                "views": _format_views(vid.get("view_count", 0)),
                "thumbnail": thumbnail,
                "channel": vid.get("channel", "Unknown"),
                "upload_date": vid.get("upload_date", ""),
                "description": vid.get("description", ""),
            })
        return {"status": "success", "results": results}

    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/tasks")
def list_tasks():
    """Return all tasks in the queue."""
    return {
        "tasks": [t.to_dict() for t in tasks.values()],
        "counts": {
            "total": len(tasks),
            "pending": sum(1 for t in tasks.values() if t.status == TaskStatus.PENDING),
            "running": sum(1 for t in tasks.values() if t.status == TaskStatus.RUNNING),
            "success": sum(1 for t in tasks.values() if t.status == TaskStatus.SUCCESS),
            "failed": sum(1 for t in tasks.values() if t.status == TaskStatus.FAILED),
        }
    }


@app.post("/api/tasks")
def create_task(req: CreateTaskRequest):
    """Create a new task (does NOT start it)."""
    task_id = str(uuid.uuid4())
    task = Task(
        task_id=task_id,
        title=req.title,
        url=req.url,
        options={
            "style": req.style,
            "dub": req.dub,
            "voice": req.voice,
            "cookies_file": req.cookies_file,
            "hardware_accel": req.hardware_accel,
            "smart_split": req.smart_split,
            "no_optimize": req.no_optimize,
            "subtitle_lang": req.subtitle_lang,
        }
    )
    task.options["thumbnail"] = req.thumbnail
    tasks[task_id] = task
    return {"status": "created", "task": task.to_dict()}


@app.post("/api/tasks/{task_id}/start")
async def start_task(task_id: str):
    """Start a specific pending task."""
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status == TaskStatus.RUNNING:
        return {"status": "already_running", "task": task.to_dict()}
    if task.status in (TaskStatus.SUCCESS, TaskStatus.FAILED):
        # Reset for re-run
        task.status = TaskStatus.PENDING
        task.logs = []
        task.progress = 0
        task.output_file = None

    asyncio.create_task(_run_task(task))
    return {"status": "started", "task": task.to_dict()}


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete (and cancel if running) a task."""
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status == TaskStatus.RUNNING and task._process:
        try:
            task._process.kill()
        except Exception:
            pass
        task.status = TaskStatus.CANCELED
    del tasks[task_id]
    return {"status": "deleted", "id": task_id}


@app.post("/api/tasks/batch")
async def batch_action(req: BatchActionRequest):
    """Perform batch start or delete on a list of task IDs."""
    results = []
    for tid in req.task_ids:
        if req.action == "start":
            task = tasks.get(tid)
            if task and task.status in (TaskStatus.PENDING, TaskStatus.FAILED, TaskStatus.CANCELED):
                if task.status != TaskStatus.PENDING:
                    task.status = TaskStatus.PENDING
                    task.logs = []
                    task.progress = 0
                asyncio.create_task(_run_task(task))
                results.append({"id": tid, "result": "started"})
            else:
                results.append({"id": tid, "result": "skipped"})
        elif req.action == "delete":
            task = tasks.get(tid)
            if task:
                if task.status == TaskStatus.RUNNING and task._process:
                    try:
                        task._process.kill()
                    except Exception:
                        pass
                del tasks[tid]
                results.append({"id": tid, "result": "deleted"})
            else:
                results.append({"id": tid, "result": "not_found"})
    return {"status": "ok", "results": results}


@app.get("/api/tasks/{task_id}/stream")
async def stream_task_logs(task_id: str):
    """SSE stream for a task's real-time log output."""
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    async def event_gen():
        sent_index = 0
        log_event = task._get_log_event()
        heartbeat_count = 0  # 心跳计数器

        # Stream all buffered + new logs
        while True:
            # 批量发送日志，每批最多50条，减少前端渲染压力
            batch_count = 0
            while sent_index < len(task.logs) and batch_count < 50:
                line = task.logs[sent_index]
                sent_index += 1
                batch_count += 1
                data = {
                    "type": "log",
                    "line": line,
                    "status": task.status.value,
                    "progress": task.progress,
                    "step": task.current_step,
                }
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

            # 每3次循环发送一次心跳（原来每2秒，现在约6秒）
            heartbeat_count += 1
            if heartbeat_count >= 3:
                heartbeat_count = 0
                status_data = {
                    "type": "status",
                    "status": task.status.value,
                    "progress": task.progress,
                    "step": task.current_step,
                    "output_file": task.output_file,
                }
                yield f"data: {json.dumps(status_data)}\n\n"

            if task.status in (TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELED):
                break

            # Wait for new logs (2s timeout for heartbeats)
            # Clear before waiting so we don't miss rapid-fire events
            log_event.clear()
            try:
                await asyncio.wait_for(log_event.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                pass

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.get("/api/tasks/{task_id}")
def get_task(task_id: str):
    """Get a single task details including logs."""
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    d = task.to_dict()
    # 只返回最近100条日志，减少内存占用和传输数据量
    d["logs"] = task.logs[-100:]
    return d


# 自动清理已完成任务的定时器
_cleanup_task: Optional[asyncio.Task] = None

async def cleanup_completed_tasks():
    """定期清理已完成的任务，释放内存"""
    global _cleanup_task
    while True:
        await asyncio.sleep(60)  # 每60秒检查一次
        try:
            completed_statuses = {TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELED}
            to_delete = []
            for task_id, task in tasks.items():
                if task.status in completed_statuses:
                    # 超过5分钟的任务清理掉
                    if task.finished_at:
                        from datetime import datetime
                        finished_time = datetime.fromisoformat(task.finished_at)
                        elapsed = (datetime.now() - finished_time).total_seconds()
                        if elapsed > 300:  # 5分钟
                            to_delete.append(task_id)

            for task_id in to_delete:
                del tasks[task_id]
                print(f"Cleaned up completed task: {task_id[:8]}")
        except Exception as e:
            print(f"Cleanup error: {e}")


@app.get("/api/files/output")
def list_output_files():
    """List output video files."""
    if not OUTPUT_DIR.exists():
        return {"files": []}
    files = []
    for f in sorted(OUTPUT_DIR.glob("*.mp4"), key=lambda x: x.stat().st_mtime, reverse=True):
        stat = f.stat()
        files.append({
            "name": f.name,
            "size_mb": round(stat.st_size / 1024 / 1024, 1),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    return {"files": files[:50]}


# ─────────────────────────── Static files + entry ──────────────────

@app.on_event("startup")
async def startup_event():
    """服务器启动时初始化"""
    global _cleanup_task
    # 启动后台清理任务
    _cleanup_task = asyncio.create_task(cleanup_completed_tasks())
    print("Server started with auto-cleanup enabled")


if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=3617)
