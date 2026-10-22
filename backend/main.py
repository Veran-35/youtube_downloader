import os
import re
import glob
import uuid
from typing import Literal

import yt_dlp
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI(title="YouTube Downloader API", version="1.0.0")

# Sesuaikan dengan origin frontend kamu
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

YOUTUBE_REGEX = re.compile(
    r"^(https?://)?(www\.)?(youtube\.com/(watch\?v=|shorts/|live/)|youtu\.be/)[\w-]+"
)


def validate_url(url: str) -> str:
    url = url.strip()
    if not YOUTUBE_REGEX.match(url):
        raise HTTPException(status_code=400, detail="URL YouTube tidak valid.")
    return url


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()[:120]


def cleanup(paths: list[str]):
    """Hapus file sementara setelah response terkirim."""
    for p in paths:
        try:
            if os.path.exists(p):
                os.remove(p)
        except OSError:
            pass


@app.get("/")
def root():
    return {"status": "ok", "service": "YouTube Downloader API"}


@app.get("/api/info")
def get_info(url: str = Query(..., description="URL video YouTube")):
    """Ambil metadata video: judul, thumbnail, durasi, daftar kualitas."""
    url = validate_url(url)

    opts = {"quiet": True, "no_warnings": True, "noplaylist": True}

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError:
        raise HTTPException(
            status_code=404,
            detail="Video tidak ditemukan atau tidak dapat diakses (mungkin private/age-restricted).",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    qualities = sorted(
        {f["height"] for f in info.get("formats", []) if f.get("height")},
        reverse=True,
    )

    return {
        "id": info.get("id"),
        "title": info.get("title"),
        "uploader": info.get("uploader") or info.get("channel"),
        "thumbnail": info.get("thumbnail"),
        "duration": info.get("duration"),  # detik
        "view_count": info.get("view_count"),
        "qualities": qualities,  # contoh: [1080, 720, 480, 360, 240, 144]
    }


@app.get("/api/download")
def download(
    background_tasks: BackgroundTasks,
    url: str = Query(..., description="URL video YouTube"),
    media_type: Literal["video", "audio"] = Query("video"),
    quality: str = Query("720", description="144/360/480/720/1080/best"),
):
    """Download video/audio di server, lalu kirim filenya ke client."""
    url = validate_url(url)

    if media_type == "audio":
        format_spec = "bestaudio/best"
    elif quality == "best":
        format_spec = "bestvideo+bestaudio/best"
    else:
        format_spec = (
            f"bestvideo[height<={quality}]+bestaudio"
            f"/best[height<={quality}]/best"
        )

    job = uuid.uuid4().hex[:10]  # hindari bentrok nama file saat concurrent

    opts = {
        "format": format_spec,
        "outtmpl": os.path.join(DOWNLOAD_DIR, f"{job}_%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 30,
    }
    if media_type == "video":
        opts["merge_output_format"] = "mp4"
    else:
        opts["postprocessors"] = [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
        ]

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mendownload: {e}")

    # Cari file hasil akhir (ekstensi bisa berubah setelah merge/konversi)
    base = os.path.join(DOWNLOAD_DIR, f"{job}_{info['id']}")
    matches = glob.glob(f"{base}.*")
    final_files = [m for m in matches if not re.search(r"\.f\d+\.", os.path.basename(m))]
    candidates = final_files or matches
    if not candidates:
        raise HTTPException(status_code=500, detail="File hasil download tidak ditemukan.")

    filepath = max(candidates, key=os.path.getsize)
    ext = os.path.splitext(filepath)[1].lstrip(".")
    safe_title = sanitize_filename(info.get("title") or info["id"])

    background_tasks.add_task(cleanup, matches)

    return FileResponse(
        filepath,
        media_type="audio/mpeg" if media_type == "audio" else "video/mp4",
        filename=f"{safe_title}.{ext}",
    )

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)