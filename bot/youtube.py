import os
import yt_dlp
import uuid
import httpx
from config import DOWNLOAD_DIR, DATA_DIR

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

COOKIES_FILE = os.path.join(DATA_DIR, "cookies.txt")


def _log(msg: str):
    print(f"[youtube] {msg}")


def _find_downloaded_file():
    for f in os.listdir(DOWNLOAD_DIR):
        p = os.path.join(DOWNLOAD_DIR, f)
        if os.path.isfile(p):
            return p
    return None


def _ydl_opts(format_spec: str, player_client: str = "web"):
    opts = {
        "format": format_spec,
        "outtmpl": os.path.join(DOWNLOAD_DIR, f"{uuid.uuid4()}.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "extractor_args": {"youtube": {"player_client": [player_client]}},
    }
    if os.path.exists(COOKIES_FILE):
        opts["cookiefile"] = COOKIES_FILE
    return opts


def _try_ytdlp(url: str, format_spec: str, player_client: str = "web"):
    opts = _ydl_opts(format_spec, player_client)
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)
        if os.path.exists(file_path):
            return file_path, info.get("title", "video")
        found = _find_downloaded_file()
        if found:
            return found, info.get("title", "video")
    return None, None


async def _try_cobalt_api(url: str):
    _log("Trying cobalt.tools API...")
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            "https://api.cobalt.tools/api/json",
            json={"url": url, "vCodec": "h264", "vQuality": "720"},
            headers={"Accept": "application/json"},
        )
        data = r.json()
        if data.get("url"):
            _log(f"cobalt returned URL: {data['url']}")
            r2 = await client.get(data["url"], follow_redirects=True, timeout=120)
            if r2.status_code == 200:
                ext = ".mp4"
                filename = f"{uuid.uuid4()}{ext}"
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(r2.content)
                return filepath, "YouTube Video"
    return None, None


async def get_video_info(url: str):
    for client in ["web", "android", "tv", "ios"]:
        try:
            opts = _ydl_opts("best", client)
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    "title": info.get("title", "Unknown"),
                    "duration": info.get("duration", 0),
                    "thumbnail": info.get("thumbnail", ""),
                    "url": url,
                }
        except Exception as e:
            _log(f"info client={client} failed: {e}")
    return {"title": "Unknown", "duration": 0, "thumbnail": "", "url": url}


async def download_yt(url: str, quality: str = "audio"):
    if quality == "audio":
        fmt = "bestaudio"
    else:
        fmt = "best"

    clients = ["web", "android", "tv", "ios", "web_creator"]
    for client in clients:
        try:
            _log(f"Trying yt-dlp client={client} fmt={fmt}")
            result = _try_ytdlp(url, fmt, client)
            if result[0]:
                _log(f"SUCCESS with client={client}")
                return result
        except Exception as e:
            _log(f"client={client} failed: {e}")

    _log("All yt-dlp clients failed, trying cobalt API...")
    cobalt_result = await _try_cobalt_api(url)
    if cobalt_result[0]:
        _log("SUCCESS with cobalt API")
        return cobalt_result

    _log("All methods failed")
    return None, None
