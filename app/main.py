import os
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from decouple import config
from pathlib import Path

# SIMPLE app initialization - no complex config classes
app = FastAPI(title="Public Speaking Coach v4")

# MOUNT STATIC FILES FIRST (fix v3 mounting order issue)
app.mount("/static", StaticFiles(directory="static"), name="static")

# SIMPLE template setup
templates = Jinja2Templates(directory="templates")

# SIMPLE environment loading - no Pydantic BaseSettings
DEBUG = config("DEBUG", default=True, cast=bool)
DATABASE_URL = config("DATABASE_URL", default="sqlite:///./app.db")

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.get("/")
def hello():
    return {"message": "Hello World - V4 Working!", "debug": DEBUG}

@app.get("/health")  
def health():
    return {"status": "healthy", "version": "v4", "env_loaded": DATABASE_URL is not None}

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
            return {"error": "Invalid file type"}

        # Save file to uploads directory
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        return {"filename": file.filename, "status": "uploaded"}
    except Exception as e:
        return {"error": str(e)}

# SIMPLE startup - no complex initialization
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)