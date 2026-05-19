import os
import asyncio
import yt_dlp
import uuid
from config import DOWNLOAD_DIR

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

COOKIES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cookies.txt")


def _log(msg: str):
    print(f"[youtube] {msg}")


def _has_cookies() -> bool:
    return os.path.exists(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 0


def _get_video_id(url: str) -> str:
    if "youtu.be" in url:
        return url.split("/")[-1].split("?")[0]
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    return url


def _detect_format(info: dict, quality: str) -> str | None:
    formats = info.get("formats", [])
    if not formats:
        return None
    if quality == "audio":
        audio = [f for f in formats if f.get("vcodec") == "none" and f.get("acodec") != "none"]
        if audio:
            audio.sort(key=lambda f: f.get("abr") or 0, reverse=True)
            for f in audio:
                if f.get("ext") == "m4a":
                    return f["format_id"]
            return audio[0]["format_id"]
        return None
    target = 1080 if quality == "1080p" else 720
    progressive = [f for f in formats if f.get("acodec") != "none" and f.get("vcodec") != "none"]
    if not progressive:
        return None
    progressive.sort(key=lambda f: abs((f.get("height") or 0) - target))
    for f in progressive:
        if (f.get("height") or 0) <= target and f.get("ext") == "mp4":
            return f["format_id"]
    for f in progressive:
        if (f.get("height") or 0) <= target:
            return f["format_id"]
    progressive.sort(key=lambda f: (f.get("height") or 0))
    return progressive[0]["format_id"]


async def _try_ytdlp(url: str, quality: str = "audio"):
    cookies = _has_cookies()
    title = "YouTube Video"
    format_str = "bestaudio[ext=m4a]/bestaudio/best/worst" if quality == "audio" else "best[ext=mp4]/best/worst"

    # Step 1: auto-detect formats
    try:
        _log("Auto-detecting formats...")
        detect_opts: dict = {"quiet": True, "no_warnings": True}
        if cookies:
            detect_opts["cookiefile"] = COOKIES_FILE
        with yt_dlp.YoutubeDL(detect_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get("title", title)
            fid = _detect_format(info, quality)
            if fid:
                format_str = f"{fid}+bestaudio/{fid}/best[ext=mp4]/best/worst" if quality != "audio" else f"{fid}/bestaudio/best/worst"
                _log(f"Detected format: {fid}")
    except Exception as e:
        _log(f"Format detection skipped: {e}")

    # Step 2: download with retries
    for attempt in range(3):
        try:
            _log(f"Download attempt {attempt+1}/3 fmt={format_str}")
            opts: dict = {
                "format": format_str,
                "outtmpl": os.path.join(DOWNLOAD_DIR, f"{uuid.uuid4()}.%(ext)s"),
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "ignoreerrors": True,
                "retries": 3,
                "fragment_retries": 3,
                "file_access_retries": 3,
                "extractor_retries": 3,
                "no_part": True,
                "throttled_rate": "100M",
            }
            if cookies:
                opts["cookiefile"] = COOKIES_FILE
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filepath = ydl.prepare_filename(info)
                if os.path.exists(filepath):
                    _log("SUCCESS")
                    return filepath, title
                for f in os.listdir(DOWNLOAD_DIR):
                    p = os.path.join(DOWNLOAD_DIR, f)
                    if os.path.isfile(p):
                        _log("SUCCESS")
                        return p, title
        except Exception as e:
            _log(f"Attempt {attempt+1} failed: {e}")
            if "Requested format" in str(e):
                format_str = "bestaudio/best/worst" if quality == "audio" else "best/worst"
            await asyncio.sleep(2)
    return None, None


async def get_video_info(url: str):
    video_id = _get_video_id(url)
    return {"title": "YouTube Video", "duration": 0, "thumbnail": "", "url": url}


async def download_yt(url: str, quality: str = "audio"):
    _log(f"Starting download: url={url}, quality={quality}")
    result = await _try_ytdlp(url, quality)
    if result[0]:
        return result
    _log("All methods failed")
    return None, None
