import os

BALE_TOKEN = os.getenv("BALE_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
APP_URL = os.getenv("APP_URL", "http://localhost:8000")
ADMIN_IDS = os.getenv("ADMIN_IDS", "")

BALE_API_BASE = "https://tapi.bale.ai/bot"
MAX_FILE_SIZE = 50 * 1024 * 1024

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DOWNLOAD_DIR = os.path.join(DATA_DIR, "downloads")
