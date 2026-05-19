import os
import yt_dlp
import uuid
import httpx
from config import DOWNLOAD_DIR, DATA_DIR

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

COOKIES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cookies.txt")

PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://pipedapi.r4fo.com",
    "https://pipedapi.adminforge.de",
    "https://api.piped.projectsegfau.lt",
]


def _log(msg: str):
    print(f"[youtube] {msg}")


def _find_downloaded_file():
    for f in os.listdir(DOWNLOAD_DIR):
        p = os.path.join(DOWNLOAD_DIR, f)
        if os.path.isfile(p):
            return p
    return None


def _get_video_id(url: str) -> str:
    if "youtu.be" in url:
        return url.split("/")[-1].split("?")[0]
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    return url


async def _try_piped(url: str, quality: str = "audio"):
    video_id = _get_video_id(url)
    for base in PIPED_INSTANCES:
        try:
            _log(f"Trying piped: {base}")
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.get(f"{base}/streams/{video_id}")
                if r.status_code != 200:
                    continue
                data = r.json()
                if not data.get("videoStreams") and not data.get("audioStreams"):
                    continue

                title = data.get("title", "YouTube Video")

                if quality == "audio":
                    audio_streams = [s for s in data.get("audioStreams", []) if s.get("url")]
                    if not audio_streams:
                        continue
                    best = max(audio_streams, key=lambda s: s.get("bitrate", 0))
                    dl_url = best["url"]
                    ext = ".m4a" if "m4a" in best.get("mimeType", "") else ".webm"
                else:
                    video_streams = [s for s in data.get("videoStreams", []) if s.get("url") and not s.get("videoOnly")]
                    if not video_streams:
                        video_streams = [s for s in data.get("videoStreams", []) if s.get("url")]
                    if not video_streams:
                        continue
                    if quality == "1080p":
                        target = "1080p"
                    elif quality == "720p":
                        target = "720p"
                    else:
                        target = "720p"
                    best = max(video_streams, key=lambda s: s.get("resolution", "0") == target)
                    dl_url = best["url"]
                    ext = ".mp4" if "mp4" in best.get("mimeType", "") else ".webm"

                filename = f"{uuid.uuid4()}{ext}"
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                async with httpx.AsyncClient(timeout=300) as dl_client:
                    r2 = await dl_client.get(dl_url, follow_redirects=True)
                    if r2.status_code == 200:
                        with open(filepath, "wb") as f:
                            f.write(r2.content)
                        _log(f"SUCCESS via piped ({base})")
                        return filepath, title
        except Exception as e:
            _log(f"piped {base} failed: {e}")
    return None, None


async def _try_invidious(url: str, quality: str = "audio"):
    video_id = _get_video_id(url)
    instances = [
        "https://vid.puffyan.us",
        "https://invidious.fdn.fr",
        "https://inv.tux.pizza",
    ]
    for base in instances:
        try:
            _log(f"Trying invidious: {base}")
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.get(f"{base}/api/v1/videos/{video_id}")
                if r.status_code != 200:
                    continue
                data = r.json()
                if "formatStreams" not in data:
                    continue
                title = data.get("title", "YouTube Video")

                if quality == "audio":
                    audio_streams = [s for s in data.get("adaptiveFormats", []) if s.get("type", "").startswith("audio")]
                    if not audio_streams:
                        continue
                    best = audio_streams[0]
                    dl_url = best.get("url", "")
                    if not dl_url:
                        continue
                else:
                    video_streams = [s for s in data.get("formatStreams", []) if s.get("url")]
                    if not video_streams:
                        continue
                    best = video_streams[0]
                    dl_url = best.get("url", "")
                    if not dl_url:
                        continue

                filename = f"{uuid.uuid4()}.mp4"
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                async with httpx.AsyncClient(timeout=300) as dl_client:
                    r2 = await dl_client.get(dl_url, follow_redirects=True)
                    if r2.status_code == 200:
                        with open(filepath, "wb") as f:
                            f.write(r2.content)
                        _log(f"SUCCESS via invidious ({base})")
                        return filepath, title
        except Exception as e:
            _log(f"invidious {base} failed: {e}")
    return None, None


async def _try_cobalt(url: str):
    _log("Trying cobalt API...")
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(
                "https://api.cobalt.tools/api/json",
                json={"url": url},
                headers={"Accept": "application/json"},
            )
            data = r.json()
            dl_url = data.get("url", "")
            if not dl_url:
                return None, None
            r2 = await client.get(dl_url, follow_redirects=True, timeout=120)
            if r2.status_code == 200:
                filename = f"{uuid.uuid4()}.mp4"
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(r2.content)
                _log("SUCCESS via cobalt")
                return filepath, "YouTube Video"
    except Exception as e:
        _log(f"cobalt failed: {e}")
    return None, None


def _has_cookies() -> bool:
    return os.path.exists(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 0


async def _try_ytdlp(url: str, quality: str = "audio"):
    formats = ["best[ext=mp4]/best", "worst/best"]
    if quality == "audio":
        formats = ["bestaudio[ext=m4a]/bestaudio/best", "worstaudio/best"]
    clients = ["android_embedded", "android", "web", "tv", "ios", "web_creator", "music"]
    cookies = _has_cookies()
    for client in clients:
        for fmt in formats:
            try:
                _log(f"Trying yt-dlp client={client} fmt={fmt}{' (with cookies)' if cookies else ''}")
                opts = {
                    "format": fmt,
                    "outtmpl": os.path.join(DOWNLOAD_DIR, f"{uuid.uuid4()}.%(ext)s"),
                    "quiet": True,
                    "no_warnings": True,
                    "extractor_args": {"youtube": {"player_client": [client]}},
                }
                if cookies:
                    opts["cookiefile"] = COOKIES_FILE
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    file_path = ydl.prepare_filename(info)
                    if os.path.exists(file_path):
                        _log(f"SUCCESS via yt-dlp client={client} fmt={fmt}")
                        return file_path, info.get("title", "video")
                    found = _find_downloaded_file()
                    if found:
                        _log(f"SUCCESS via yt-dlp client={client} fmt={fmt}")
                        return found, info.get("title", "video")
            except Exception as e:
                _log(f"yt-dlp client={client} fmt={fmt} failed: {e}")
    return None, None


async def _try_ytdlp_ga(url: str, quality: str = "audio"):
    _log("Trying ytdl.ga API...")
    endpoints = [
        "https://ytdl.ga/handler.php",
        "https://najemi.cz/ytdl/handler.php",
    ]
    for endpoint in endpoints:
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                r = await client.get(endpoint, params={"url": url})
                if r.status_code != 200:
                    _log(f"ytdl.ga {endpoint} returned {r.status_code}")
                    continue
                data = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
                if isinstance(data, dict):
                    dl_url = data.get("url") or data.get("download") or data.get("link")
                else:
                    dl_url = str(data).strip()
                if not dl_url or dl_url == url:
                    continue
                ext = ".mp4"
                if quality == "audio":
                    ext = ".mp3"
                filename = f"{uuid.uuid4()}{ext}"
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                r2 = await client.get(dl_url, follow_redirects=True, timeout=120)
                if r2.status_code == 200:
                    with open(filepath, "wb") as f:
                        f.write(r2.content)
                    _log(f"SUCCESS via ytdl.ga ({endpoint})")
                    return filepath, "YouTube Video"
        except Exception as e:
            _log(f"ytdl.ga {endpoint} failed: {e}")
    return None, None


async def get_video_info(url: str):
    video_id = _get_video_id(url)
    for base in PIPED_INSTANCES:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.get(f"{base}/streams/{video_id}")
                if r.status_code == 200:
                    data = r.json()
                    return {
                        "title": data.get("title", "Unknown"),
                        "duration": data.get("duration", 0),
                        "thumbnail": data.get("thumbnailUrl", ""),
                        "url": url,
                    }
        except Exception:
            continue
    return {"title": "YouTube Video", "duration": 0, "thumbnail": "", "url": url}


async def download_yt(url: str, quality: str = "audio"):
    _log(f"Starting download: url={url}, quality={quality}")

    if _has_cookies():
        result = await _try_ytdlp(url, quality)
        if result[0]:
            return result

    result = await _try_ytdlp_ga(url, quality)
    if result[0]:
        return result

    result = await _try_piped(url, quality)
    if result[0]:
        return result

    result = await _try_invidious(url, quality)
    if result[0]:
        return result

    result = await _try_cobalt(url)
    if result[0]:
        return result

    result = await _try_ytdlp(url, quality)
    if result[0]:
        return result

    _log("All methods failed")
    return None, None
