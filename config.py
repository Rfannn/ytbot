import os

BALE_TOKEN = os.getenv("BALE_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")  # e.g. https://your-app.onrender.com/webhook/bot
APP_URL = os.getenv("APP_URL", "http://localhost:8000")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///data/bot.db")
ADMIN_IDS = os.getenv("ADMIN_IDS", "")  # comma-separated Bale user IDs

BALE_API_BASE = "https://tapi.bale.ai/bot"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
DOWNLOAD_DIR = "/tmp/downloads"
