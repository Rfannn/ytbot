import os
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

        ext = _ext_from_url(url, content_type)
        filename = f"{uuid.uuid4()}{ext}"
        filepath = os.path.join(DOWNLOAD_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(r.content)

        return filepath, None, content_type, len(r.content)


def _ext_from_url(url: str, content_type: str) -> str:
    import re
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
    }
    return mapping.get(content_type, "")


def cleanup_file(filepath: str):
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass
