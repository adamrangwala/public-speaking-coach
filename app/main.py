import os
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from decouple import config
import sqlite3
import subprocess
import json

# App initialization
app = FastAPI(title="Public Speaking Coach v4")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")

# Configuration
DEBUG = config("DEBUG", default=True, cast=bool)
DATABASE_URL = config("DATABASE_URL", default="sqlite:///./app.db")
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Database setup
def init_db():
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            filesize INTEGER NOT NULL,
            upload_date TEXT NOT NULL,
            notes TEXT DEFAULT '',
            analysis_data TEXT DEFAULT '{}'
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Helper functions
def save_video_metadata(filename, filepath, filesize):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO videos (filename, filepath, filesize, upload_date) VALUES (?, ?, ?, ?)",
        (filename, str(filepath), filesize, datetime.now().isoformat())
    )
    conn.commit()
    video_id = cursor.lastrowid
    conn.close()
    return video_id

def get_all_videos():
    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos ORDER BY upload_date DESC")
    videos = cursor.fetchall()
    conn.close()
    return videos

def get_video(video_id: int):
    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
    video = cursor.fetchone()
    conn.close()
    return video

def update_video_notes(video_id: int, notes: str):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE videos SET notes = ? WHERE id = ?",
        (notes, video_id)
    )
    conn.commit()
    conn.close()

def update_analysis_data(video_id: int, analysis_data: str):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE videos SET analysis_data = ? WHERE id = ?",
        (analysis_data, video_id)
    )
    conn.commit()
    conn.close()

def analyze_speech(video_path: str):
    """Basic speech analysis function (placeholder implementation)"""
    try:
        # In a real implementation, this would use a speech processing library
        # For now, return mock analysis data
        return {
            "clarity_score": 85,
            "words_per_minute": 120,
            "filler_words": 12,
            "feedback": "Your speech was clear overall. Try to reduce filler words."
        }
    except Exception as e:
        return {
            "error": str(e),
            "feedback": "Analysis failed. Please try again."
        }

# Routes
@app.get("/")
def hello():
    return {"message": "Hello World - V4 Working!", "debug": DEBUG}

@app.get("/health")
def health():
    return {"status": "healthy", "version": "v4", "db_connected": True}

@app.get("/page-test")
def landing_page(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/upload")
def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Validate file type
        allowed_types = ['.mp4', '.mov', '.avi', '.webm']
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_types:
            raise HTTPException(400, "Invalid file type")

        # Save file
        file_path = UPLOAD_DIR / file.filename
        file_size = 0
        with open(file_path, "wb") as buffer:
            content = await file.read()
            file_size = len(content)
            buffer.write(content)

        # Save metadata
        video_id = save_video_metadata(file.filename, file_path, file_size)

        return {
            "id": video_id,
            "filename": file.filename,
            "size": file_size,
            "status": "uploaded"
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/videos")
def list_videos(request: Request):
    videos = get_all_videos()
    return templates.TemplateResponse("videos.html", {
        "request": request,
        "videos": videos
    })

@app.get("/video/{video_id}")
def view_video(request: Request, video_id: int):
    video = get_video(video_id)
    if not video:
        raise HTTPException(404, "Video not found")
    return templates.TemplateResponse("video_view.html", {
        "request": request,
        "video": video
    })

@app.get("/analysis/{video_id}")
def view_analysis(request: Request, video_id: int):
    try:
        video = get_video(video_id)
        if not video:
            raise HTTPException(404, "Video not found")
        
        # Safely get analysis data
        analysis_data = {}
        if 'analysis_data' in video.keys():
            try:
                analysis_data = json.loads(video['analysis_data'] or '{}')
            except json.JSONDecodeError:
                analysis_data = {}
        
        if not analysis_data:
            analysis_data = analyze_speech(video['filepath'])
            update_analysis_data(video_id, json.dumps(analysis_data))
        
        return templates.TemplateResponse("analysis.html", {
            "request": request,
            "video": video,
            "analysis": analysis_data
        })
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {str(e)}")

@app.get("/notes/{video_id}")
def view_notes(request: Request, video_id: int):
    video = get_video(video_id)
    if not video:
        raise HTTPException(404, "Video not found")
    return templates.TemplateResponse("notes.html", {
        "request": request,
        "video": video
    })

@app.post("/notes/{video_id}")
def save_notes(video_id: int, notes: str = Form(...)):
    update_video_notes(video_id, notes)
    return {"status": "updated", "video_id": video_id}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)