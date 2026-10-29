import { useEffect, useState, useRef } from "react";
import "./App.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
const MAX_LIST = 10;
const menit = (d) =>
  `${Math.floor(d / 60)} :${String(d % 60).padStart(2, "0")}`;

const LABEL = {
  waiting: "Menunggu",
  downloading: "Mengunduh…",
  done: "Selesai",
  failed: "Gagal",
};
export default function App() {
  const [input, setInput] = useState("");
  const [items, setItems] = useState([]); // {url, title, duration}
  const [format, setFormat] = useState("mp3");
  const [error, setError] = useState("");
  const [adding, setAdding] = useState(false);
  const [batchId, setBatchId] = useState(null);
  const [batch, setBatch] = useState(null);
  const timer = useRef(null);

  const berjalan = batch && batch.status === "processing";
  const selesai = batch && batch.status === "done";

  async function tambah(e) {
    e.preventDefault();
    const url = input.trim();
    if (!url) return;
    setError("");
    if (items.some((i) => i.url === url))
      return setError("Link ini sudah ada di daftar.");
    if (items.length >= MAX_LIST)
      return setError(`Maksimal ${MAX_LIST} link per unduhan.`);

    setAdding(true);
    try {
      const res = await fetch(`${API}/preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Link tidak bisa dipakai.");
      if (!data || !data.title) throw new Error("Data video tidak valid.");
      setItems((prev) => [...prev, data]);
      setInput("");
    } catch (err) {
      setError(
        err.message === "Failed to fetch"
          ? "Tidak bisa terhubung ke server."
          : err.message,
      );
    } finally {
      setAdding(false);
    }
  }

  function hapus(url) {
    setItems((prev) => prev.filter((i) => i.url !== url));
  }

  async function mulai() {
    setError("");
    try {
      const res = await fetch(`${API}/batch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ urls: items.map((i) => i.url), format }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Gagal memulai unduhan.");
      setBatch({
        status: "processing",
        items: items.map((i) => ({ url: i.url, status: "waiting" })),
      });
      setBatchId(data.batch_id);
    } catch (err) {
      setError(err.message);
    }
  }

  // Cek progres tiap 2 detik selama batch berjalan
  useEffect(() => {
    if (!batchId) return;
    const cek = async () => {
      try {
        const res = await fetch(`${API}/batch/${batchId}`);
        if (!res.ok) throw new Error("Batch tidak ditemukan.");
        const data = await res.json();
        setBatch(data);
        if (data.status === "done") clearInterval(timer.current);
      } catch (err) {
        clearInterval(timer.current);
        setError(err.message);
      }
    };
    cek();
    timer.current = setInterval(cek, 2000);
    return () => clearInterval(timer.current);
  }, [batchId]);

  function ulang() {
    setBatch(null);
    setBatchId(null);
    setItems([]);
  }

  const judul = (url) => items.find((i) => i.url === url)?.title || url;
  const total = batch?.items.length || 0;
  const selesaiCount =
    batch?.items.filter((i) => i.status === "done" || i.status === "failed")
      .length || 0;
  const persen = total ? Math.round((selesaiCount / total) * 100) : 0;

  return (
    <main className="app">
      <header>
        <h1>Unduh dari YouTube</h1>
        <p>
          Tempel link, kumpulkan dalam daftar, lalu unduh sekaligus. Video
          maksimal 20 menit.
        </p>
      </header>

      {!batch && (
        <>
          <form className="tambah" onSubmit={tambah}>
            <input
              type="url"
              placeholder="https://www.youtube.com/watch?v=…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              aria-label="Link YouTube"
            />
            <button type="submit" disabled={adding || !input.trim()}>
              {adding ? "Mengecek…" : "Tambah ke daftar"}
            </button>
          </form>

          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}

          <section className="daftar" aria-live="polite">
            <div className="daftar-kepala">
              <h2>Daftar unduhan</h2>
              <span>
                {items.length}/{MAX_LIST}
              </span>
            </div>

            {items.length === 0 ? (
              <p className="kosong">
                Belum ada link. Tempel link YouTube di atas untuk memulai.
              </p>
            ) : (
              <ul>
                {items.map((i) => (
                  <li key={i.url}>
                    <div className="info">
                      <strong>{i.title}</strong>
                      <small>{menit(i.duration)} menit</small>
                    </div>
                    <button
                      className="hapus"
                      onClick={() => hapus(i.url)}
                      aria-label={`Hapus ${i.title}`}
                    >
                      Hapus
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="aksi">
            <div className="format" role="radiogroup" aria-label="Format">
              {["mp3", "mp4"].map((f) => (
                <button
                  key={f}
                  role="radio"
                  aria-checked={format === f}
                  className={format === f ? "aktif" : ""}
                  onClick={() => setFormat(f)}
                >
                  {f === "mp3" ? "Audio (MP3)" : "Video (MP4)"}
                </button>
              ))}
            </div>
            <button
              className="utama"
              disabled={items.length === 0}
              onClick={mulai}
            >
              Unduh {items.length > 0 ? `${items.length} item` : "semua"}
            </button>
          </section>
        </>
      )}

      {batch && (
        <section className="progres" aria-live="polite">
          <div className="daftar-kepala">
            <h2>{selesai ? "Unduhan siap" : "Sedang diproses"}</h2>
            <span>
              {selesaiCount}/{total}
            </span>
          </div>
          <div
            className="bar"
            role="progressbar"
            aria-valuenow={persen}
            aria-valuemin="0"
            aria-valuemax="100"
          >
            <div style={{ width: `${persen}%` }} />
          </div>

          <ul>
            {batch.items.map((i) => (
              <li key={i.url}>
                <div className="info">
                  <strong>{judul(i.url)}</strong>
                </div>
                <span className={`status ${i.status}`}>{LABEL[i.status]}</span>
              </li>
            ))}
          </ul>

          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}

          {selesai && (
            <div className="aksi">
              <a
                className="utama"
                href={`${API}/batch/${batchId}/zip`}
                download
              >
                Unduh file ZIP
              </a>
              <button className="sekunder" onClick={ulang}>
                Mulai baru
              </button>
            </div>
          )}
          {berjalan && (
            <p className="catatan">Jangan tutup halaman ini sampai selesai.</p>
          )}
        </section>
      )}
    </main>
  );
}
