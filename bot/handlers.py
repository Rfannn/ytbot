import os
import httpx
from bot.bale_api import (
    send_message, send_document, send_chat_action, answer_callback_query,
    edit_message_text, MENU_BUTTONS, YOUTUBE_QUALITY, BACK_TO_MENU,
    make_keyboard, get_file, get_file_link,
)
from bot.youtube import get_video_info, download_yt, COOKIES_FILE
from bot.filedl import download_file, cleanup_file
from bot.chatgpt import ask_gpt
from db import (
    get_user, create_user, set_chat_mode, get_chat_mode,
    add_conversation, get_conversation_history, clear_conversation,
    log_stat, is_admin, get_stats_summary,
)

# In-memory store for pending YouTube URLs per user
_pending_yt: dict = {}


def _extract_text(msg):
    return msg.get("text", "").strip()


def _chat_id(msg):
    return msg.get("chat", {}).get("id")


def _message_id(msg):
    return msg.get("message_id")


def _from_user(msg):
    return msg.get("from", {})


async def handle_update(update: dict):
    msg = update.get("message")
    cb = update.get("callback_query")

    if cb:
        return await _handle_callback(cb)
    if msg:
        return await _handle_message(msg)


async def _ensure_user(msg):
    user = _from_user(msg)
    bale_id = str(user.get("id"))
    await create_user(
        bale_id,
        username=user.get("username"),
        first_name=user.get("first_name"),
    )
    return bale_id


async def _download_bale_file(file_id: str) -> bytes | None:
    try:
        file_info = await get_file(file_id)
        file_path = file_info.get("result", {}).get("file_path")
        if not file_path:
            return None
        url = get_file_link(file_path)
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url)
            if r.status_code == 200:
                return r.content
    except Exception as e:
        print(f"Error downloading file from Bale: {e}")
    return None


async def _handle_message(msg):
    bale_id = await _ensure_user(msg)
    chat_id = _chat_id(msg)
    text = _extract_text(msg)
    mode = await get_chat_mode(bale_id)

    doc = msg.get("document")
    if doc and mode == "youtube":
        file_name = doc.get("file_name", "")
        if file_name.lower() in ("cookies.txt", "cookies") or file_name.lower().endswith("cookies.txt"):
            content = await _download_bale_file(doc["file_id"])
            if content:
                os.makedirs(os.path.dirname(COOKIES_FILE), exist_ok=True)
                with open(COOKIES_FILE, "wb") as f:
                    f.write(content)
                await send_message(chat_id, "✅ YouTube cookies saved! Now send a YouTube link to download.")
                await log_stat("cookies_uploaded", bale_id)
            else:
                await send_message(chat_id, "❌ Failed to download the file. Try again.")
            return
        await send_message(chat_id, "Send a file named **cookies.txt** to upload YouTube cookies, or send a YouTube link.", parse_mode="Markdown")
        return

    # ChatGPT mode
    if mode == "chatgpt" and text:
        await send_chat_action(chat_id, "typing")
        history = await get_conversation_history(bale_id)
        messages = [{"role": h["role"], "content": h["content"]} for h in history]
        messages.append({"role": "user", "content": text})
        await add_conversation(bale_id, "user", text)
        try:
            reply = await ask_gpt(messages)
            await add_conversation(bale_id, "assistant", reply)
            await send_message(chat_id, reply)
            await log_stat("chatgpt", bale_id, text[:100])
        except Exception as e:
            await send_message(chat_id, f"ChatGPT error: {str(e)}")
        return

    # YouTube mode
    if mode == "youtube" and text:
        if text == "🍪 Upload Cookies":
            await send_message(chat_id,
                "📤 *How to export YouTube cookies:*\n\n"
                "1. Install a browser extension:\n"
                "   • Chrome: *Get cookies.txt* (from Chrome Web Store)\n"
                "   • Firefox: *cookies.txt* (from Firefox Add-ons)\n"
                "2. Go to https://www.youtube.com and log in\n"
                "3. Click the extension icon → *Export* cookies\n"
                "4. Send the exported **cookies.txt** file to this bot\n\n"
                "After uploading, try downloading a video again.",
                parse_mode="Markdown"
            )
            return
        await send_chat_action(chat_id, "typing")
        if "youtube.com" in text or "youtu.be" in text:
            try:
                info = await get_video_info(text)
                _pending_yt[bale_id] = text
                caption = f"🎬 *{info['title']}*\nChoose quality:"
                await send_message(chat_id, caption, reply_markup=YOUTUBE_QUALITY, parse_mode="Markdown")
            except Exception as e:
                await send_message(chat_id, f"❌ Could not process link: {str(e)}")
        else:
            await send_message(chat_id, "Please send a valid YouTube link.\n\nYou can also type *🍪 Upload Cookies* to upload YouTube cookies.", parse_mode="Markdown")
        return

    # File download mode
    if mode == "filedl" and text:
        await send_chat_action(chat_id, "typing")
        await _download_and_send(chat_id, text, bale_id)
        return

    # Commands
    if text in ("/start", "/menu"):
        user_info = _from_user(msg)
        name = user_info.get("first_name", "User")
        welcome = (
            f"👋 Hello {name}! Welcome to the Multi-Purpose Bot.\n\n"
            f"Choose a feature from the menu below:"
        )
        await send_message(chat_id, welcome, reply_markup=MENU_BUTTONS)
        await set_chat_mode(bale_id, "none")

    elif text == "/help" or text == "❓ Help":
        await _show_help(chat_id)

    elif text == "🎬 YouTube Downloader":
        await set_chat_mode(bale_id, "youtube")
        await send_message(chat_id, "📥 Send me a YouTube link to download.", reply_markup=BACK_TO_MENU)

    elif text == "📁 File Downloader":
        await set_chat_mode(bale_id, "filedl")
        await send_message(chat_id, "📥 Send me a direct download link for any file.", reply_markup=BACK_TO_MENU)

    elif text == "🤖 ChatGPT":
        await set_chat_mode(bale_id, "chatgpt")
        await send_message(chat_id, "🤖 ChatGPT mode activated!\n\nSend /clear to reset conversation.", reply_markup=BACK_TO_MENU)

    elif text == "🌐 Open Panel":
        await send_message(chat_id, "🌐 Open the web panel:\n" + os.getenv("APP_URL", "http://localhost:8000"))

    elif text == "/clear":
        await clear_conversation(bale_id)
        await send_message(chat_id, "Conversation cleared.")

    elif text == "/admin" and await is_admin(bale_id):
        await send_message(chat_id, "Admin panel:\n" + os.getenv("APP_URL", "http://localhost:8000") + "/admin")

    elif text == "/stats" and await is_admin(bale_id):
        _, rows = await get_stats_summary()
        lines = ["📊 *Bot Statistics*"]
        for row in rows:
            lines.append(f"• {row['action']}: {row['count']}")
        await send_message(chat_id, "\n".join(lines) if lines else "No stats yet.", parse_mode="Markdown")

    elif text.startswith("/"):
        await send_message(chat_id, "Unknown command. Use /start or /menu.")

    else:
        await send_message(chat_id, "Please use the menu to choose a feature.", reply_markup=MENU_BUTTONS)


async def _handle_callback(cb):
    cb_id = cb["id"]
    msg = cb.get("message", {})
    chat_id = _chat_id(msg)
    data = cb.get("data", "")
    bale_id = str(cb["from"]["id"])

    await answer_callback_query(cb_id)

    if data == "menu:main":
        await set_chat_mode(bale_id, "none")
        await edit_message_text(chat_id, msg["message_id"], "Main menu:")
        await send_message(chat_id, "Choose a feature:", reply_markup=MENU_BUTTONS)

    elif data in ("yt:audio", "yt:720p", "yt:1080p"):
        quality_map = {"yt:audio": "audio", "yt:720p": "720p", "yt:1080p": "1080p"}
        quality = quality_map[data]
        yt_url = _pending_yt.get(bale_id)
        if not yt_url:
            await send_message(chat_id, "❌ No pending YouTube link. Please send one again.")
            return
        await _handle_yt_download(chat_id, msg["message_id"], bale_id, yt_url, quality)


async def _handle_yt_download(chat_id, msg_id, bale_id, url, quality):
    await edit_message_text(chat_id, msg_id, f"⏳ Downloading {quality}...")
    filepath, title = await download_yt(url, quality)
    if filepath and os.path.exists(filepath):
        fname = os.path.basename(filepath)
        with open(filepath, "rb") as f:
            await send_document(chat_id, f.read(), caption=f"🎬 {title}", filename=fname)
        cleanup_file(filepath)
        await log_stat("youtube", bale_id, f"{title} ({quality})")
    else:
        await send_message(chat_id, "❌ Download failed. Video may be too large or unavailable.")


async def _download_and_send(chat_id, url, bale_id):
    await send_message(chat_id, "⏳ Downloading file...")
    filepath, error, content_type, size = await download_file(url)
    if error:
        await send_message(chat_id, f"❌ {error}")
        return
    if filepath and os.path.exists(filepath):
        fname = os.path.basename(filepath)
        sz = f"{size / 1024 / 1024:.1f} MB" if size > 1024 * 1024 else f"{size / 1024:.1f} KB"
        with open(filepath, "rb") as f:
            await send_document(chat_id, f.read(), caption=f"📁 {fname} ({sz})", filename=fname)
        cleanup_file(filepath)
        await log_stat("filedl", bale_id, url[:100])
    else:
        await send_message(chat_id, "❌ Download failed.")


async def _show_help(chat_id):
    help_text = (
        "🤖 *Multi-Purpose Bot Help*\n\n"
        "🎬 *YouTube Downloader* — Download YouTube videos as audio or video\n"
        "📁 *File Downloader* — Download any file from a direct link\n"
        "🤖 *ChatGPT* — Chat with AI\n"
        "🌐 *Web Panel* — Access the web dashboard\n\n"
        "Commands:\n"
        "/start — Show main menu\n"
        "/help — Show this help\n"
        "/clear — Clear ChatGPT history\n"
        "/menu — Back to main menu"
    )
    await send_message(chat_id, help_text, parse_mode="Markdown")
