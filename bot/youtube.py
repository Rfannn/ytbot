import os
import yt_dlp
import uuid
from config import DOWNLOAD_DIR, DATA_DIR

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

COOKIES_FILE = os.path.join(DATA_DIR, "cookies.txt")


def _find_downloaded_file():
    for f in os.listdir(DOWNLOAD_DIR):
        p = os.path.join(DOWNLOAD_DIR, f)
        if os.path.isfile(p):
            return p
    return None


async def get_video_info(url: str):
    try:
        from pytubefix import YouTube
        yt = YouTube(url)
        return {
            "title": yt.title,
            "duration": yt.length,
            "thumbnail": yt.thumbnail_url,
            "url": url,
        }
    except Exception:
        ydl_opts = {"quiet": True, "no_warnings": True}
        if os.path.exists(COOKIES_FILE):
            ydl_opts["cookiefile"] = COOKIES_FILE
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title", "Unknown"),
                "duration": info.get("duration", 0),
                "thumbnail": info.get("thumbnail", ""),
                "url": url,
            }


async def download_yt(url: str, quality: str = "audio"):
    try:
        from pytubefix import YouTube
        from pytubefix.cli import on_progress

        yt = YouTube(url, on_progress_callback=on_progress)

        if quality == "audio":
            stream = yt.streams.filter(only_audio=True).first()
        elif quality == "720p":
            stream = yt.streams.filter(res="720p").first() or yt.streams.filter(res="480p").first() or yt.streams.get_highest_resolution()
        elif quality == "1080p":
            stream = yt.streams.filter(res="1080p").first() or yt.streams.get_highest_resolution()
        else:
            stream = yt.streams.get_highest_resolution()

        if stream:
            file_path = stream.download(output_path=DOWNLOAD_DIR)
            return file_path, yt.title
    except Exception as e:
        print(f"[youtube] pytubefix failed: {e}")

    print("[youtube] Falling back to yt-dlp...")
    return await _download_ytdlp(url, quality)


async def _download_ytdlp(url: str, quality: str = "audio"):
    if quality == "audio":
        formats = ["bestaudio", "best"]
    else:
        formats = ["best", "worst"]

    for fmt in formats:
        try:
            opts = {
                "format": fmt,
                "outtmpl": os.path.join(DOWNLOAD_DIR, f"{uuid.uuid4()}.%(ext)s"),
                "quiet": True,
                "no_warnings": True,
                "extractor_args": {"youtube": {"player_client": ["web"]}},
            }
            if os.path.exists(COOKIES_FILE):
                opts["cookiefile"] = COOKIES_FILE
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
