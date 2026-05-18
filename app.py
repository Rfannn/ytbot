"""
Main Flask application for Bale YouTube Downloader Bot
"""

import logging
import os
from flask import Flask, request, jsonify
from pathlib import Path
import config
from database import Database
from downloader import YouTubeDownloader
from bot_handler import BaleBot

# ════════════════════════════════════════════════════════════
# Configure Logging
# ════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════
# Initialize Flask App
# ════════════════════════════════════════════════════════════

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB max request

# ════════════════════════════════════════════════════════════
# Initialize Components
# ════════════════════════════════════════════════════════════

try:
    db = Database(config.DB_FILE)
    downloader = YouTubeDownloader(config.TEMP_FILES_DIR)
    bot = BaleBot(db, downloader)
    logger.info("✅ All components initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize components: {str(e)}")
    raise

# ════════════════════════════════════════════════════════════
# Routes
# ════════════════════════════════════════════════════════════


@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Webhook endpoint for Bale bot
    Receives updates and processes them
    """
    try:
        update = request.get_json()
        
        if not update:
            return jsonify({'ok': False, 'error': 'Empty request'}), 400

        logger.info(f"🔔 Webhook received: {update.get('update_id')}")

        # Process the update
        if bot.process_update(update):
            return jsonify({'ok': True}), 200
        else:
            return jsonify({'ok': False, 'error': 'Processing failed'}), 500

    except Exception as e:
        logger.error(f"❌ Webhook error: {str(e)}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'ok': True,
        'status': 'healthy',
        'bot_token': bool(config.BALE_BOT_TOKEN),
        'database': config.DB_FILE.exists(),
        'temp_dir': config.TEMP_FILES_DIR.exists()
    }), 200


@app.route('/', methods=['GET'])
def index():
    """Index page"""
    return jsonify({
        'name': '🎬 Bale YouTube Downloader Bot',
        'version': '1.0',
        'status': 'running',
        'webhook': '/webhook',
        'health': '/health'
    }), 200


# ════════════════════════════════════════════════════════════
# Error Handlers
# ════════════════════════════════════════════════════════════


@app.errorhandler(404)
def not_found(error):
    return jsonify({'ok': False, 'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 Error: {str(error)}")
    return jsonify({'ok': False, 'error': 'Internal server error'}), 500


# ════════════════════════════════════════════════════════════
# Startup/Shutdown
# ════════════════════════════════════════════════════════════


@app.before_request
def before_request():
    """Before each request"""
    pass


@app.after_request
def after_request(response):
    """After each request"""
    return response


# ════════════════════════════════════════════════════════════
# Background Tasks (if needed)
# ════════════════════════════════════════════════════════════


def cleanup_old_files():
    """Cleanup old files periodically"""
    deleted = downloader.cleanup_old_files(config.MAX_FILE_AGE_SECONDS)
    if deleted > 0:
        logger.info(f"🗑️ Cleaned up {deleted} old files")


# ════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════


if __name__ == '__main__':
    logger.info("🚀 Starting Bale YouTube Downloader Bot")
    logger.info(f"Webhook URL: {config.WEBHOOK_URL}")
    logger.info(f"Database: {config.DB_FILE}")
    logger.info(f"Temp directory: {config.TEMP_FILES_DIR}")
    
    # Run Flask app
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=False
    )
