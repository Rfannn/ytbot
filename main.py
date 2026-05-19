import os
import sys
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import init_db
from bot.handlers import handle_update
from bot.bale_api import send_message
from web.routes import router as web_router

app = FastAPI(title="MultiBot")

app.mount("/static", StaticFiles(directory="web/static"), name="static")
app.include_router(web_router)


@app.on_event("startup")
async def startup():
    await init_db()
    print("✅ Bot database initialized")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook/bot")
async def bale_webhook(update: dict):
    try:
        await handle_update(update)
    except Exception as e:
        print(f"❌ Error handling update: {e}")
    return JSONResponse({"ok": True})


@app.get("/set-webhook")
async def set_webhook():
    from bot.bale_api import BASE
    import httpx
    wh_url = os.getenv("WEBHOOK_URL", "")
    if not wh_url:
        return JSONResponse({"ok": False, "error": "WEBHOOK_URL not set"})
    webhook_endpoint = f"{wh_url.rstrip('/')}/webhook/bot"
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BASE}/setWebhook", json={"url": webhook_endpoint})
        return r.json()


@app.get("/delete-webhook")
async def delete_webhook():
    from bot.bale_api import BASE
    import httpx
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BASE}/deleteWebhook")
        return r.json()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
