import os
import yt_dlp
import uuid
from config import DOWNLOAD_DIR, DATA_DIR

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

COOKIES_FILE = os.path.join(DATA_DIR, "cookies.txt")


def _get_ydl_opts(format_spec: str):
    opts = {
        "format": format_spec,
        "outtmpl": os.path.join(DOWNLOAD_DIR, f"{uuid.uuid4()}.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "extractor_args": {"youtube": {"player_client": ["web"]}},
    }
    if os.path.exists(COOKIES_FILE):
        opts["cookiefile"] = COOKIES_FILE
    return opts


def _find_downloaded_file():
    for f in os.listdir(DOWNLOAD_DIR):
        p = os.path.join(DOWNLOAD_DIR, f)
        if os.path.isfile(p):
            return p
    return None


async def get_video_info(url: str):
    ydl_opts = _get_ydl_opts("best")
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
        formats = ["bestaudio[ext=m4a]", "bestaudio", "best"]
    else:
        formats = ["bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"]

    for fmt in formats:
        try:
            opts = _get_ydl_opts(fmt)
            opts["merge_output_format"] = "mp4"
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
