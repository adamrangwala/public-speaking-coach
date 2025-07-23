import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from decouple import config

# SIMPLE app initialization - no complex config classes
app = FastAPI(title="Public Speaking Coach v4")

# MOUNT STATIC FILES FIRST (fix v3 mounting order issue)
app.mount("/static", StaticFiles(directory="static"), name="static")

# SIMPLE template setup
templates = Jinja2Templates(directory="templates")

# SIMPLE environment loading - no Pydantic BaseSettings
DEBUG = config("DEBUG", default=True, cast=bool)
DATABASE_URL = config("DATABASE_URL", default="sqlite:///./app.db")

@app.get("/")
def hello():
    return {"message": "Hello World - V4 Working!", "debug": DEBUG}

@app.get("/health")  
def health():
    return {"status": "healthy", "version": "v4", "env_loaded": DATABASE_URL is not None}

# Add template route
@app.get("/page-test")
def landing_page(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

# SIMPLE startup - no complex initialization
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)