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

@app.get("/preview")
def preview(req: PreviewReq):
    try:
        return check_video(req.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def proses_batch(bid):
    b = batches[bid]
    folder =f'{BASE}/{bid}'
    os.makedirs(folder, exist_ok=True)
    opts={
        "quiet": True,
        "noplaylist": True,
        "outtmpl": f"{folder}/%(title).80s.%(ext)s",
        "match_filter": yt_dlp.utils.match_filter_func(f"duration <= {MAX_DURASI}"),
    }
    if b["format"] == "mp3":
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [{"key": "FFmpegExtractAudio",
                                   "preferredcodec": "mp3",
                                   "preferredquality": "192"}]
    else:
        opts["format"] = "best[height<=720]"

    for item in b["items"]:
        item["status"] = "downloading"
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([item["url"]])
            item["status"] = "done"
        except Exception:
            item["status"] = "failed"

    shutil.make_archive(folder, "zip", folder)
    shutil.rmtree(folder, ignore_errors=True)
    b["status"] = "done"

@app.post("/batch")
def buat_batch(req: BatchReq, bg: BackgroundTasks):
    urls = list(dict.fromkeys(req.urls))  # hapus duplikat
    if not urls or len(urls) > MAX_LIST:
        raise HTTPException(400, f"Isi 1-{MAX_LIST} link")
    if req.format not in ("mp3", "mp4"):
        raise HTTPException(400, "Format tidak valid")
    bid = uuid.uuid4().hex
    batches[bid] = {
        "status": "processing",
        "format": req.format,
        "items": [{"url": u, "status": "waiting"} for u in urls],
    }
    bg.add_task(proses_batch, bid)
    return {"batch_id": bid}

@app.get("/batch/{bid}")
def status_batch(bid: str):
    if bid not in batches:
        raise HTTPException(404, "Batch tidak ditemukan")
    return batches[bid]

@app.get("/batch/{bid}/zip")
def ambil_zip(bid: str):
    path = f"{BASE}/{bid}.zip"
    if bid not in batches or not os.path.exists(path):
        raise HTTPException(404, "File belum siap")
    return FileResponse(path, filename="download.zip")
    
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)