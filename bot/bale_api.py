import httpx
from config import BALE_TOKEN, BALE_API_BASE

BASE = f"{BALE_API_BASE}{BALE_TOKEN}"


async def _req(method: str, **kwargs):
    url = f"{BASE}/{method}"
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, json=kwargs)
        return r.json()


async def get_me():
    return await _req("getMe")


async def send_message(chat_id, text, reply_markup=None, parse_mode=None):
    kwargs = {"chat_id": chat_id, "text": text}
    if reply_markup:
        kwargs["reply_markup"] = reply_markup
    if parse_mode:
        kwargs["parse_mode"] = parse_mode
    return await _req("sendMessage", **kwargs)


async def send_photo(chat_id, photo, caption=None, reply_markup=None):
    kwargs = {"chat_id": chat_id, "photo": photo}
    if caption:
        kwargs["caption"] = caption
    if reply_markup:
        kwargs["reply_markup"] = reply_markup
    return await _req("sendPhoto", **kwargs)


async def send_document(chat_id, document, caption=None, reply_markup=None):
    url = f"{BASE}/sendDocument"
    files = {"document": ("file", document)}
    data = {"chat_id": str(chat_id)}
    if caption:
        data["caption"] = caption
    if reply_markup:
        data["reply_markup"] = reply_markup
    async with httpx.AsyncClient(timeout=300) as client:
        r = await client.post(url, data=data, files=files)
        return r.json()


async def send_document_by_url(chat_id, file_url, caption=None):
    kwargs = {"chat_id": chat_id, "document": file_url}
    if caption:
        kwargs["caption"] = caption
    return await _req("sendDocument", **kwargs)


async def send_chat_action(chat_id, action):
    return await _req("sendChatAction", chat_id=chat_id, action=action)


async def answer_callback_query(callback_query_id, text=None, show_alert=False):
    kwargs = {"callback_query_id": callback_query_id}
    if text:
        kwargs["text"] = text
    kwargs["show_alert"] = show_alert
    return await _req("answerCallbackQuery", **kwargs)


async def edit_message_text(chat_id, message_id, text, reply_markup=None):
    kwargs = {"chat_id": chat_id, "message_id": message_id, "text": text}
    if reply_markup:
        kwargs["reply_markup"] = reply_markup
    return await _req("editMessageText", **kwargs)


async def get_file(file_id):
    return await _req("getFile", file_id=file_id)


async def get_file_link(file_path: str):
    return f"https://tapi.bale.ai/file/bot{BALE_TOKEN}/{file_path}"


def make_keyboard(buttons):
    return {"inline_keyboard": [[{"text": b[0], "callback_data": b[1]}] for b in buttons]}


def make_reply_keyboard(buttons, resize=True):
    return {
        "keyboard": [[{"text": b}] for b in buttons],
        "resize_keyboard": resize,
    }


def remove_keyboard():
    return {"remove_keyboard": True}


MENU_BUTTONS = make_reply_keyboard([
    "🎬 YouTube Downloader",
    "📁 File Downloader",
    "🤖 ChatGPT",
    "🌐 Open Panel",
    "❓ Help",
])

YOUTUBE_QUALITY = make_keyboard([
    ("🎵 Audio (MP3)", "yt:audio"),
    ("🎬 Video (720p)", "yt:720p"),
    ("🎬 Video (1080p)", "yt:1080p"),
    ("🔙 Back to Menu", "menu:main"),
])

BACK_TO_MENU = make_keyboard([
    ("🔙 Back to Menu", "menu:main"),
])
