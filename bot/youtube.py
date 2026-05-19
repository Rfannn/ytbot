import os
import yt_dlp
import uuid
from config import DOWNLOAD_DIR, DATA_DIR

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

COOKIES_FILE = os.path.join(DATA_DIR, "cookies.txt")


def _cookies_opts():
    if os.path.exists(COOKIES_FILE):
        print(f"[youtube] Using cookies from {COOKIES_FILE}")
        return {"cookiefile": COOKIES_FILE}
    print(f"[youtube] No cookies file at {COOKIES_FILE}")
    return {}


def _base_opts():
    return {
        "quiet": True,
        "no_warnings": True,
        "extractor_args": {"youtube": {"player_client": ["android", "tv"]}},
    }


def _get_ydl_opts(format_spec: str):
    opts = {
        "format": format_spec,
        "outtmpl": os.path.join(DOWNLOAD_DIR, f"{uuid.uuid4()}.%(ext)s"),
    }
    opts.update(_base_opts())
    opts.update(_cookies_opts())
    return opts


def _find_downloaded_file():
    for f in os.listdir(DOWNLOAD_DIR):
        p = os.path.join(DOWNLOAD_DIR, f)
        if os.path.isfile(p):
            return p
    return None


async def get_video_info(url: str):
    ydl_opts = _base_opts()
    ydl_opts.update(_cookies_opts())
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title", "Unknown"),
            "duration": info.get("duration", 0),
            "thumbnail": info.get("thumbnail", ""),
            "url": url,
        }


async def download_yt(url: str, quality: str = "audio"):
    if quality == "audio":
        formats = ["bestaudio", "best"]
    else:
        formats = ["best", "worst"]

    for fmt in formats:
        try:
            opts = _get_ydl_opts(fmt)
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
                if os.path.exists(file_path):
                    return file_path, info.get("title", "video")
                found = _find_downloaded_file()
                if found:
                    return found, info.get("title", "video")
        except Exception as e:
            print(f"[youtube] Format {fmt} failed: {e}")
            continue

    return None, None
