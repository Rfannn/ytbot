import os
import re
import httpx
import uuid
from config import DOWNLOAD_DIR, MAX_FILE_SIZE

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


async def download_file(url: str):
    async with httpx.AsyncClient(timeout=300, follow_redirects=True) as client:
        r = await client.head(url)
        content_length = int(r.headers.get("content-length", 0))
        content_type = r.headers.get("content-type", "application/octet-stream")

        if content_length > MAX_FILE_SIZE:
            return None, "File too large (max 50MB)", None, content_length

        r = await client.get(url)
        if r.status_code != 200:
            return None, f"Failed to download (HTTP {r.status_code})", None, None

        filename = _extract_filename(r.headers, url, content_type)
        if not filename:
            ext = _ext_from_url(url, content_type)
            filename = f"{uuid.uuid4()}{ext}"

        filepath = os.path.join(DOWNLOAD_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(r.content)

        return filepath, None, content_type, len(r.content)


def _extract_filename(headers, url: str, content_type: str) -> str:
    cd = headers.get("Content-Disposition", "")
    match = re.search(r'filename\*?="?([^";]+)"?', cd)
    if match:
        name = match.group(1).strip()
        if name:
            return name

    from urllib.parse import urlparse
    path = urlparse(url).path
    if "/" in path:
        name = path.rsplit("/", 1)[-1]
        if name and "." in name:
            import html
            return html.unquote(name)

    ext = _ext_from_url(url, content_type)
    if ext:
        return f"download{ext}"
    return ""


def _ext_from_url(url: str, content_type: str) -> str:
    match = re.search(r"\.([a-zA-Z0-9]+)(?:\?|$)", url)
    if match:
        return f".{match.group(1)}"
    mapping = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "application/pdf": ".pdf",
        "application/zip": ".zip",
        "text/plain": ".txt",
        "application/x-msdownload": ".exe",
        "application/vnd.ms-excel": ".xls",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
        "application/msword": ".doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "video/mp4": ".mp4",
        "audio/mpeg": ".mp3",
    }
    return mapping.get(content_type, "")


def cleanup_file(filepath: str):
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass
