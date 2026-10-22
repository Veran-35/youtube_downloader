import { useState } from "react";
import { fetchVideoInfo, buildDownloadUrl } from "./api";
import "./App.css";

function formatDuration(total) {
  if (!total) return "";
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = Math.floor(total % 60);
  return [h, m, s].map((v) => String(v).padStart(2, "0")).join(":");
}

function formatViews(n) {
  return n ? `${n.toLocaleString("id-ID")}x ditonton` : "";
}

export default function App() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [video, setVideo] = useState(null);
  const [error, setError] = useState("");
  const [mediaType, setMediaType] = useState("video");
  const [quality, setQuality] = useState("720");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url.trim() || loading) return;
    setLoading(true);
    setError("");
    setVideo(null);
    try {
      const data = await fetchVideoInfo(url.trim());
      setVideo(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) setUrl(text.trim());
    } catch {
      /* izin clipboard ditolak — abaikan */
    }
  };

  const handleDownload = () => {
    setDownloading(true);
    const link = document.createElement("a");
    link.href = buildDownloadUrl(url.trim(), mediaType, quality);
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => setDownloading(false), 8000);
  };

  return (
    <div className="app">
      <header>
        <div className="logo">
          <span className="play">▶</span>
          YT<span>Downloader</span>
        </div>
        <p className="tagline">
          Download video &amp; audio YouTube tanpa login — cukup tempel linknya.
        </p>
      </header>

      <main className="card">
        <form className="url-form" onSubmit={handleSubmit}>
          <input
            type="url"
            placeholder="https://www.youtube.com/watch?v=..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
          />
          <button type="button" className="btn-ghost" onClick={handlePaste}>
            📋 Tempel
          </button>
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Memproses..." : "Cek Video"}
          </button>
        </form>

        {error && <div className="error">⚠️ {error}</div>}

        {video && (
          <div className="preview">
            <div className="thumb-row">
              <img src={video.thumbnail} alt={video.title} />
              <div className="meta">
                <h2>{video.title}</h2>
                <p>
                  {[video.uploader, formatDuration(video.duration), formatViews(video.view_count)]
                    .filter(Boolean)
                    .join(" • ")}
                </p>
              </div>
            </div>

            <div className="options">
              <div className="toggle">
                <button
                  type="button"
                  className={mediaType === "video" ? "active" : ""}
                  onClick={() => setMediaType("video")}
                >
                  🎬 Video (MP4)
                </button>
                <button
                  type="button"
                  className={mediaType === "audio" ? "active" : ""}
                  onClick={() => setMediaType("audio")}
                >
                  🎵 Audio (MP3)
                </button>
              </div>

              {mediaType === "video" && (
                <select value={quality} onChange={(e) => setQuality(e.target.value)}>
                  <option value="best">Kualitas terbaik</option>
                  <option value="1080">1080p (Full HD)</option>
                  <option value="720">720p (HD)</option>
                  <option value="480">480p</option>
                  <option value="360">360p</option>
                </select>
              )}

              <button
                className="btn-primary download-btn"
                onClick={handleDownload}
                disabled={downloading}
              >
                {downloading ? "⏳ Mempersiapkan file..." : "⬇️ Download Sekarang"}
              </button>

              {downloading && (
                <p className="hint">
                  Server sedang memproses video. File akan otomatis terunduh sebentar lagi…
                </p>
              )}
            </div>
          </div>
        )}
      </main>

      <footer>
        Dibuat dengan React + FastAPI • Gunakan secara bijak &amp; sesuai ketentuan YouTube.
      </footer>
    </div>
  );
}