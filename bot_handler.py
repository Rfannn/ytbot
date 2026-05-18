"""
Bot handler module for Bale webhook
Processes incoming messages and manages bot logic
"""

import requests
import logging
import re
from typing import Optional, Dict
from config import (
    BALE_SEND_MESSAGE, BALE_SEND_DOCUMENT, BALE_EDIT_MESSAGE,
    BALE_ANSWER_CALLBACK, QUALITY_OPTIONS, MESSAGES,
    RATE_LIMIT_SECONDS, MAX_FILE_SIZE_BYTES
)
from database import Database
from downloader import YouTubeDownloader
from pathlib import Path

logger = logging.getLogger(__name__)


class BaleBot:
    """Bale bot handler"""

    def __init__(self, db: Database, downloader: YouTubeDownloader):
        self.db = db
        self.downloader = downloader

    def process_update(self, update: Dict) -> bool:
        """Process incoming webhook update"""
        try:
            update_id = update.get('update_id')
            
            # Prevent duplicate processing
            if self.db.is_update_processed(update_id):
                logger.info(f"⏭️ Update {update_id} already processed")
                return True
            
            self.db.mark_update_processed(update_id)

            # Handle different message types
            if 'message' in update:
                self.handle_message(update['message'])
            elif 'callback_query' in update:
                self.handle_callback(update['callback_query'])
            
            return True

        except Exception as e:
            logger.error(f"❌ Error processing update: {str(e)}")
            return False

    def handle_message(self, message: Dict):
        """Handle incoming text message"""
        chat_id = message['chat']['id']
        text = message.get('text', '').strip()

        logger.info(f"📩 Message from {chat_id}: {text[:50]}")

        # Handle /start command
        if text.startswith('/start'):
            self.send_start_message(chat_id)
            return

        # Handle /settings command
        if text.startswith('/settings'):
            self.send_settings_menu(chat_id)
            return

        # Check if it's a YouTube URL
        if self.downloader.is_valid_youtube_url(text):
            self.handle_download_request(chat_id, text)
            return

        # If not recognized, show help
        self.send_message(chat_id, "❌ Please send a YouTube URL or use /start")

    def handle_callback(self, callback_query: Dict):
        """Handle callback button presses"""
        callback_id = callback_query['id']
        chat_id = callback_query['from']['id']
        data = callback_query.get('data', '').strip()

        logger.info(f"🔘 Callback from {chat_id}: {data}")

        try:
            # Quality selection callbacks
            if data.startswith('quality_'):
                parts = data.replace('quality_', '').split('|', 1)
                quality_key = parts[0]
                if len(parts) > 1:
                    youtube_url = parts[1]
                else:
                    youtube_url = callback_query.get('message', {}).get('text', '')
                if quality_key in QUALITY_OPTIONS:
                    quality_value = QUALITY_OPTIONS[quality_key]['value']
                    self.answer_callback(callback_id, "⏳ Downloading...")
                    self.perform_download(chat_id, youtube_url, quality_value)
                    return

            # Settings callbacks
            if data.startswith('set_quality_'):
                quality_value = data.replace('set_quality_', '')
                self.db.set_user_quality(chat_id, quality_value)
                self.answer_callback(callback_id, f"✅ Quality set to {quality_value}")
                return

            if data == 'toggle_subtitles':
                settings = self.db.get_user_settings(chat_id)
                new_value = not settings['subtitles']
                self.db.set_user_subtitles(chat_id, new_value)
                status = "✅ Enabled" if new_value else "❌ Disabled"
                self.answer_callback(callback_id, f"Subtitles {status}")
                return

        except Exception as e:
            logger.error(f"Error handling callback: {str(e)}")
            self.answer_callback(callback_id, f"❌ Error: {str(e)[:50]}")

    def handle_download_request(self, chat_id: str, youtube_url: str):
        """Handle YouTube download request"""
        # Check rate limit
        if self.db.is_rate_limited(chat_id, RATE_LIMIT_SECONDS):
            remaining = self.db.get_remaining_time(chat_id, RATE_LIMIT_SECONDS)
            minutes = (remaining // 60) + (1 if remaining % 60 else 0)
            msg = MESSAGES['rate_limited']['fa'].format(minutes=minutes)
            self.send_message(chat_id, msg)
            return

        # Show quality selection
        self.send_quality_menu(chat_id, youtube_url)

    def perform_download(self, chat_id: str, youtube_url: str, quality: str):
        """Perform actual download"""
        try:
            # Check rate limit again
            if self.db.is_rate_limited(chat_id, RATE_LIMIT_SECONDS):
                remaining = self.db.get_remaining_time(chat_id, RATE_LIMIT_SECONDS)
                minutes = (remaining // 60) + (1 if remaining % 60 else 0)
                msg = MESSAGES['rate_limited']['fa'].format(minutes=minutes)
                self.send_message(chat_id, msg)
                return

            # Send processing message
            self.send_message(chat_id, MESSAGES['processing']['fa'])

            # Get user settings
            settings = self.db.get_user_settings(chat_id)

            # Download video
            success, file_path, error = self.downloader.download(
                youtube_url,
                quality=quality,
                subtitles=settings['subtitles']
            )

            if not success:
                error_msg = MESSAGES['error']['fa'].format(error=error)
                self.send_message(chat_id, error_msg)
                return

            # Check file size
            file_size = Path(file_path).stat().st_size
            if file_size > MAX_FILE_SIZE_BYTES:
                error_msg = MESSAGES['file_too_large']['fa']
                self.send_message(chat_id, error_msg)
                Path(file_path).unlink()
                return

            # Send file to user
            self.send_document(chat_id, file_path)

            # Update rate limit
            self.db.update_rate_limit(chat_id)

            # Clean up file
            Path(file_path).unlink(missing_ok=True)

            # Clean up old files
            self.downloader.cleanup_old_files()

            logger.info(f"✅ Download complete for {chat_id}")

        except Exception as e:
            logger.error(f"❌ Download error: {str(e)}")
            error_msg = MESSAGES['error']['fa'].format(error=str(e)[:50])
            self.send_message(chat_id, error_msg)

    # ════════════════════════════════════════════════════════════
    # Message Sending Methods
    # ════════════════════════════════════════════════════════════

    def send_start_message(self, chat_id: str):
        """Send start/help message"""
        msg = MESSAGES['start']['fa']
        self.send_message(chat_id, msg)

    def send_quality_menu(self, chat_id: str, youtube_url: str):
        """Send quality selection menu"""
        msg = MESSAGES['quality_prompt']['fa']
        buttons = []
        
        for key, option in QUALITY_OPTIONS.items():
            callback_data = f'quality_{key}|{youtube_url}'
            buttons.append({
                'text': option['label'],
                'callback_data': callback_data
            })

        keyboard = {'inline_keyboard': [[btn] for btn in buttons]}
        self.send_message(chat_id, msg, keyboard)

    def send_settings_menu(self, chat_id: str):
        """Send settings menu"""
        settings = self.db.get_user_settings(chat_id)
        subtitles_status = "✅ ON" if settings['subtitles'] else "❌ OFF"
        
        msg = f"⚙️ Settings\n\nQuality: {settings['quality']}\nSubtitles: {subtitles_status}"
        
        buttons = [
            [
                {'text': '🎬 Quality', 'callback_data': 'set_quality_best'},
                {'text': '📝 Subtitles', 'callback_data': 'toggle_subtitles'}
            ]
        ]
        
        keyboard = {'inline_keyboard': buttons}
        self.send_message(chat_id, msg, keyboard)

    def send_message(self, chat_id: str, text: str, keyboard: Optional[Dict] = None):
        """Send text message to chat"""
        try:
            payload = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'HTML'
            }
            
            if keyboard:
                payload['reply_markup'] = keyboard

            response = requests.post(BALE_SEND_MESSAGE, json=payload, timeout=10)
            logger.info(f"📤 Message sent to {chat_id}: {response.status_code}")
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False

    def send_document(self, chat_id: str, file_path: str):
        """Send file document to chat"""
        try:
            with open(file_path, 'rb') as f:
                files = {'document': f}
                data = {'chat_id': chat_id}
                
                response = requests.post(
                    BALE_SEND_DOCUMENT,
                    data=data,
                    files=files,
                    timeout=30
                )
            
            logger.info(f"📤 Document sent to {chat_id}: {response.status_code}")
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Error sending document: {str(e)}")
            return False

    def answer_callback(self, callback_id: str, text: str = '', show_alert: bool = False):
        """Answer callback query"""
        try:
            payload = {
                'callback_query_id': callback_id,
                'text': text,
                'show_alert': show_alert
            }
            
            response = requests.post(BALE_ANSWER_CALLBACK, json=payload, timeout=10)
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Error answering callback: {str(e)}")
            return False
