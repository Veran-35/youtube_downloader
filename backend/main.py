import os, re, uuid, shutil
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_DURASI = 20 * 60
MAX_LIST = 10
BASE = "/tmp/downloads"
os.makedirs(BASE, exist_ok=True)
YT = re.compile(r"^https?://(www\.|m\.)?(youtube\.com|youtu\.be)/")
batches = {}


class PreviewReq(BaseModel):
    url: str


class BatchReq(BaseModel):
    urls: list[str]
    format: str = "mp3"


def validasi_url(url):
    if not YT.match(url):
        raise ValueError("Bukan link YouTube")
    path = urlparse(url).path
    if path.startswith(("/playlist", "/channel", "/c/", "/@", "/user/")):
        raise ValueError("Link playlist/channel tidak didukung")


def cek_video(url):
    validasi_url(url)
    opts = {
        "quiet": True,
        "noplaylist": True,
        "playlist_items": "1",
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        d = ydl.extract_info(url, download=False)

    if not d:
        raise ValueError("Video tidak ditemukan")
    if d.get("_type") == "playlist":
        raise ValueError("Link playlist tidak didukung")
    if (d.get("duration") or 0) > MAX_DURASI:
        raise ValueError("Durasi lebih dari 20 menit")

    return {"url": url, "title": d["title"], "duration": d["duration"]}


@app.post("/preview")
def preview(req: PreviewReq):
    try:
        return cek_video(req.url)
    except Exception as e:
        raise HTTPException(400, str(e))


def proses_batch(bid):
    b = batches[bid]
    folder = f"{BASE}/{bid}"
    os.makedirs(folder, exist_ok=True)
    opts = {
        "quiet": True,
        "noplaylist": True,
        "playlist_items": "1",
        "outtmpl": f"{folder}/%(title).80s.%(ext)s",
        "match_filter": yt_dlp.utils.match_filter_func(f"duration <= {MAX_DURASI}"),
    }
    if b["format"] == "mp3":
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
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
    urls = list(dict.fromkeys(req.urls))
    if not urls or len(urls) > MAX_LIST:
        raise HTTPException(400, f"Isi 1-{MAX_LIST} link")
    if req.format not in ("mp3", "mp4"):
        raise HTTPException(400, "Format tidak valid")
    for u in urls:
        try:
            validasi_url(u)
        except ValueError as e:
            raise HTTPException(400, str(e))
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
    
    uvicorn.run(app, host="0.0.0.0", port=8000)