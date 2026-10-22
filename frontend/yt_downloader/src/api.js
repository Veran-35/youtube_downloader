// Ubah sesuai alamat backend FastAPI kamu
export const API_BASE = "http://localhost:8000";

export async function fetchVideoInfo(url) {
  const res = await fetch(`${API_BASE}/api/info?url=${encodeURIComponent(url)}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Gagal mengambil info video. Coba lagi.");
  }
  return res.json();
}

export function buildDownloadUrl(url, mediaType, quality) {
  const params = new URLSearchParams({
    url,
    media_type: mediaType,
    quality,
  });
  return `${API_BASE}/api/download?${params}`;
}