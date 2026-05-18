"""
Configuration module for Bale YouTube Downloader Bot
Handles environment variables and app settings
"""

import os
from pathlib import Path

# ════════════════════════════════════════════════════════════
# 🔐 ENVIRONMENT VARIABLES (set these on PythonAnywhere)
# ════════════════════════════════════════════════════════════

BALE_BOT_TOKEN = os.getenv('BALE_BOT_TOKEN', '')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://your-username.pythonanywhere.com/webhook')

# ════════════════════════════════════════════════════════════
# 📁 FILE PATHS
# ════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).parent
TEMP_FILES_DIR = BASE_DIR / 'temp_files'
DB_FILE = BASE_DIR / 'bot_database.db'

# Create temp directory if it doesn't exist
TEMP_FILES_DIR.mkdir(exist_ok=True)

# ════════════════════════════════════════════════════════════
# ⚙️ BOT SETTINGS
# ════════════════════════════════════════════════════════════

# Rate limiting (seconds between downloads)
RATE_LIMIT_SECONDS = 300  # 5 minutes

# Status check frequency (seconds)
STATUS_CHECK_SECONDS = 180  # 3 minutes

# Maximum file size before deletion (bytes)
MAX_FILE_AGE_SECONDS = 300  # 5 minutes

# File size limit for PythonAnywhere (45 MB)
MAX_FILE_SIZE_MB = 45
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# ════════════════════════════════════════════════════════════
# 🎬 QUALITY SETTINGS
# ════════════════════════════════════════════════════════════

QUALITY_OPTIONS = {
    '1': {'label': '🔊 فقط صدا (Audio Only)', 'value': 'audio'},
    '2': {'label': '📱 SD (480p)', 'value': '480'},
    '3': {'label': '📺 HD (720p)', 'value': '720'},
    '4': {'label': '🎬 Full HD (1080p)', 'value': '1080'},
    '5': {'label': '✨ بهترین کیفیت (Best)', 'value': 'best'},
}

DEFAULT_QUALITY = 'best'

# ════════════════════════════════════════════════════════════
# 🌐 API ENDPOINTS
# ════════════════════════════════════════════════════════════

BALE_API_BASE = f'https://tapi.bale.ai/bot{BALE_BOT_TOKEN}'
BALE_SEND_MESSAGE = f'{BALE_API_BASE}/sendMessage'
BALE_SEND_DOCUMENT = f'{BALE_API_BASE}/sendDocument'
BALE_EDIT_MESSAGE = f'{BALE_API_BASE}/editMessageText'
BALE_ANSWER_CALLBACK = f'{BALE_API_BASE}/answerCallbackQuery'

# ════════════════════════════════════════════════════════════
# 📝 MESSAGES (Bilingual)
# ════════════════════════════════════════════════════════════

MESSAGES = {
    'start': {
        'fa': '🎬 خوش آمدید به دانلودر یوتیوب!\n\nلینک یوتیوب خود را ارسال کنید یا از منو انتخاب کنید:',
        'en': '🎬 Welcome to YouTube Downloader!\n\nSend a YouTube link or choose from menu:'
    },
    'quality_prompt': {
        'fa': '📊 کیفیت دانلود را انتخاب کنید:',
        'en': '📊 Select download quality:'
    },
    'processing': {
        'fa': '⏳ در حال دانلود...',
        'en': '⏳ Downloading...'
    },
    'success': {
        'fa': '✅ دانلود موفق!',
        'en': '✅ Download successful!'
    },
    'rate_limited': {
        'fa': '⏱️ لطفاً {minutes} دقیقه صبر کنید.',
        'en': '⏱️ Please wait {minutes} minutes.'
    },
    'error': {
        'fa': '❌ خطا: {error}',
        'en': '❌ Error: {error}'
    },
    'invalid_url': {
        'fa': '❌ لینک یوتیوب نامعتبر است.',
        'en': '❌ Invalid YouTube link.'
    },
    'file_too_large': {
        'fa': '❌ فایل بیش از 45 مگابایت است.',
        'en': '❌ File larger than 45 MB.'
    },
}

# ════════════════════════════════════════════════════════════
# 🔧 YT-DLP SETTINGS
# ════════════════════════════════════════════════════════════

YTDLP_CONFIG = {
    'quiet': False,
    'no_warnings': False,
    'socket_timeout': 30,
    'socket_connect_timeout': 10,
    'retries': 3,
    'skip_unavailable_fragments': True,
}

# ════════════════════════════════════════════════════════════
# 🔍 VALIDATION
# ════════════════════════════════════════════════════════════

if not BALE_BOT_TOKEN:
    raise ValueError("❌ BALE_BOT_TOKEN environment variable not set!")

if not WEBHOOK_URL:
    raise ValueError("❌ WEBHOOK_URL environment variable not set!")
