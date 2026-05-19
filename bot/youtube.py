import os
import yt_dlp
import uuid
from config import DOWNLOAD_DIR

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def _get_ydl_opts(format_spec: str, ext: str):
    return {
        "format": format_spec,
        "outtmpl": os.path.join(DOWNLOAD_DIR, f"{uuid.uuid4()}.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
    }


async def get_video_info(url: str):
    ydl_opts = {"quiet": True, "no_warnings": True}
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
        opts = _get_ydl_opts("bestaudio/best", "mp3")
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    elif quality == "720p":
        opts = _get_ydl_opts("bestvideo[height<=720]+bestaudio/best[height<=720]", "mp4")
    elif quality == "1080p":
        opts = _get_ydl_opts("bestvideo[height<=1080]+bestaudio/best[height<=1080]", "mp4")
    else:
        opts = _get_ydl_opts("best", "mp4")

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)
        base, _ = os.path.splitext(file_path)
        if quality == "audio":
            file_path = base + ".mp3"
        else:
            file_path = base + ".mp4"
        if os.path.exists(file_path):
            return file_path, info.get("title", "video")
        for f in os.listdir(DOWNLOAD_DIR):
            p = os.path.join(DOWNLOAD_DIR, f)
            if os.path.isfile(p):
                return p, info.get("title", "video")
        return None, None
