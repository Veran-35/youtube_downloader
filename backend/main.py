import os, re ,uuid , shutil 
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware  
import yt_dlp


app = FastAPI(title="YouTube Downloader API", version="1.0.0")
MAX_DURASI = 20 * 60   # 20 menit
MAX_LIST = 10          # maks link per batch
BASE = "C:\Users\veran\Documents\code\project\miniproject\youtube_downloader\download"
os.makedirs(BASE, exist_ok=True)

YT = re.compile(r"^https?://(www\.|m\.)?(youtube\.com|youtu\.be)/")
batches = {}

class PreviewReq(BaseModel):
    url: str

class BatchReq(BaseModel):
    urls: list[str]
    format: str = "mp3"   # "mp3" atau "mp4"
# Sesuaikan dengan origin frontend kamu



app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def check_video(url):
    if not YT.match(url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    with yt_dlp.YoutubeDL() as ydl:
        d= ydl.extract_info(url, download=False)
        if (d.get("duration") or 0) > MAX_DURASI:
            raise HTTPException(status_code=400, detail="Video duration exceeds limit")

@app.get("/")
def root():
    return {"status": "ok", "service": "YouTube Downloader API"}



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)