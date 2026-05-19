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


async def _try_ytdlp(url: str, quality: str = "audio"):
    cookies = _has_cookies()

    if quality == "audio":
        format_chain = ["bestaudio[ext=m4a]/bestaudio/best/worst", "bestaudio/best/worst", "worst"]
    else:
        format_chain = ["best[ext=mp4]/best/worst", "best/worst", "worst"]

    for format_str in format_chain:
        for attempt in range(2):
            try:
                _log(f"fmt={format_str} attempt={attempt+1}/2{' (cookies)' if cookies else ''}")
                out = os.path.join(DOWNLOAD_DIR, f"{uuid.uuid4()}.%(ext)s")
                opts = {
                    "format": format_str,
                    "outtmpl": out,
                    "quiet": True,
                    "no_warnings": True,
                    "noplaylist": True,
                }
                if cookies:
                    opts["cookiefile"] = COOKIES_FILE
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    if not info:
                        continue
                    title = info.get("title", "YouTube Video")
                    fp = ydl.prepare_filename(info)
                    if fp and os.path.exists(fp):
                        _log("SUCCESS")
                        return fp, title
                    for f in os.listdir(DOWNLOAD_DIR):
                        p = os.path.join(DOWNLOAD_DIR, f)
                        if os.path.isfile(p):
                            _log("SUCCESS")
                            return p, title
            except Exception as e:
                _log(f"fmt={format_str} attempt={attempt+1} failed: {e}")
            await asyncio.sleep(1)
    return None, None


async def get_video_info(url: str):
    return {"title": "YouTube Video", "duration": 0, "thumbnail": "", "url": url}


async def download_yt(url: str, quality: str = "audio"):
    _log(f"Starting download: url={url}, quality={quality}")
    result = await _try_ytdlp(url, quality)
    if result[0]:
        return result
    _log("All methods failed")
    return None, None
