from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import os

from fastapi.responses import FileResponse
import os

from bot.youtube import get_video_info, download_yt
from bot.filedl import download_file, cleanup_file
from bot.chatgpt import ask_gpt
from db import get_all_users, get_stats_summary, set_admin, is_admin, get_setting, set_setting, log_stat
from config import DOWNLOAD_DIR

templates = Jinja2Templates(directory="web/templates")

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/youtube", response_class=HTMLResponse)
async def youtube_page(request: Request):
    return templates.TemplateResponse("youtube.html", {"request": request})


@router.post("/youtube", response_class=HTMLResponse)
async def youtube_download(request: Request, url: str = Form(...), format: str = Form("audio")):
    try:
        info = await get_video_info(url)
        quality = "audio" if format == "audio" else "720p"
        filepath, title = await download_yt(url, quality)
        if filepath and os.path.exists(filepath):
            # Re-host the file for download
            download_url = f"/download/{os.path.basename(filepath)}"
            return templates.TemplateResponse("youtube.html", {
                "request": request,
                "result": {"title": title, "download_url": download_url},
            })
        return templates.TemplateResponse("youtube.html", {
            "request": request,
            "error": "Processing failed.",
        })
    except Exception as e:
        return templates.TemplateResponse("youtube.html", {
            "request": request,
            "error": str(e),
        })


@router.get("/filedl", response_class=HTMLResponse)
async def filedl_page(request: Request):
    return templates.TemplateResponse("filedl.html", {"request": request})


@router.post("/filedl", response_class=HTMLResponse)
async def filedl_download(request: Request, url: str = Form(...)):
    try:
        filepath, error, content_type, size = await download_file(url)
        if error:
            return templates.TemplateResponse("filedl.html", {"request": request, "error": error})
        if filepath and os.path.exists(filepath):
            sz = f"{size / 1024 / 1024:.1f} MB" if size > 1024 * 1024 else f"{size / 1024:.1f} KB"
            download_url = f"/download/{os.path.basename(filepath)}"
            return templates.TemplateResponse("filedl.html", {
                "request": request,
                "result": {"size": sz, "download_url": download_url},
            })
        return templates.TemplateResponse("filedl.html", {"request": request, "error": "Download failed."})
    except Exception as e:
        return templates.TemplateResponse("filedl.html", {"request": request, "error": str(e)})


@router.get("/download/{filename}")
async def serve_file(filename: str):
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath, filename=filename)
    return JSONResponse({"error": "File not found"}, status_code=404)


@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request, "messages": []})


@router.post("/chat")
async def chat_send(data: dict):
    msg = data.get("message", "")
    if not msg:
        return JSONResponse({"reply": "Please send a message."})
    try:
        reply = await ask_gpt([{"role": "user", "content": msg}])
        return JSONResponse({"reply": reply})
    except Exception as e:
        return JSONResponse({"reply": f"Error: {str(e)}"})


# --- Admin routes ---

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    users = await get_all_users()
    summary, stat_rows = await get_stats_summary()
    total_downloads = sum(r["count"] for r in stat_rows if r["action"] in ("youtube", "filedl"))
    chatgpt_count = sum(r["count"] for r in stat_rows if r["action"] == "chatgpt")
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "total_users": summary[0] if summary else 0,
        "total_downloads": total_downloads,
        "chatgpt_count": chatgpt_count,
        "users": users,
    })


@router.post("/admin/toggle-admin")
async def toggle_admin(bale_id: str = Form(...)):
    adm = await is_admin(bale_id)
    await set_admin(bale_id, not adm)
    return HTMLResponse(status_code=303, headers={"Location": "/admin"})


@router.get("/admin/settings", response_class=HTMLResponse)
async def admin_settings_page(request: Request):
    settings = {
        "openai_key": await get_setting("openai_key", ""),
        "webhook_url": await get_setting("webhook_url", ""),
    }
    return templates.TemplateResponse("admin/settings.html", {"request": request, "settings": settings})


@router.post("/admin/settings")
async def admin_settings_save(
    request: Request,
    openai_key: str = Form(""),
    webhook_url: str = Form(""),
):
    await set_setting("openai_key", openai_key)
    await set_setting("webhook_url", webhook_url)
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
    return templates.TemplateResponse("admin/settings.html", {
        "request": request,
        "settings": {"openai_key": openai_key, "webhook_url": webhook_url},
        "saved": True,
    })
