"""
Database module for managing SQLite operations
Handles rate limiting, user settings, and file caching
"""

import sqlite3
import time
from pathlib import Path
from typing import Optional, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_file: Path):
        self.db_file = db_file
        self.init_database()

    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(str(self.db_file))
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Rate limits table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rate_limits (
                chat_id TEXT PRIMARY KEY,
                last_request_time INTEGER,
                created_at INTEGER DEFAULT (cast(strftime('%s') as integer))
            )
        ''')

        # User settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                chat_id TEXT PRIMARY KEY,
                quality TEXT DEFAULT 'best',
                subtitles BOOLEAN DEFAULT 0,
                language TEXT DEFAULT 'fa',
                created_at INTEGER DEFAULT (cast(strftime('%s') as integer))
            )
        ''')

        # File cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT,
                file_id TEXT UNIQUE,
                file_name TEXT,
                file_path TEXT,
                file_size INTEGER,
                youtube_url TEXT,
                created_at INTEGER DEFAULT (cast(strftime('%s') as integer))
            )
        ''')

        # Processed updates table (prevent duplicate processing)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_updates (
                update_id INTEGER PRIMARY KEY,
                processed_at INTEGER DEFAULT (cast(strftime('%s') as integer))
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("✅ Database initialized")

    # ════════════════════════════════════════════════════════════
    # Rate Limiting Methods
    # ════════════════════════════════════════════════════════════

    def is_rate_limited(self, chat_id: str, limit_seconds: int) -> bool:
        """Check if user is rate limited"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT last_request_time FROM rate_limits WHERE chat_id = ?', (chat_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            elapsed = time.time() - row['last_request_time']
            return elapsed < limit_seconds
        return False

    def get_remaining_time(self, chat_id: str, limit_seconds: int) -> int:
        """Get remaining time in seconds until next allowed request"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT last_request_time FROM rate_limits WHERE chat_id = ?', (chat_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            elapsed = time.time() - row['last_request_time']
            remaining = limit_seconds - elapsed
            return max(0, int(remaining))
        return 0

    def update_rate_limit(self, chat_id: str):
        """Update rate limit timestamp for user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT OR REPLACE INTO rate_limits (chat_id, last_request_time) VALUES (?, ?)',
            (chat_id, int(time.time()))
        )
        
        conn.commit()
        conn.close()

    # ════════════════════════════════════════════════════════════
    # User Settings Methods
    # ════════════════════════════════════════════════════════════

    def get_user_settings(self, chat_id: str) -> Dict:
        """Get user settings"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT quality, subtitles, language FROM user_settings WHERE chat_id = ?',
            (chat_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'quality': row['quality'],
                'subtitles': bool(row['subtitles']),
                'language': row['language']
            }
        
        # Return defaults if not found
        return {
            'quality': 'best',
            'subtitles': False,
            'language': 'fa'
        }

    def set_user_quality(self, chat_id: str, quality: str):
        """Set user's preferred quality"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            '''INSERT OR REPLACE INTO user_settings (chat_id, quality, subtitles, language)
               SELECT ?, ?, subtitles, language FROM user_settings 
               WHERE chat_id = ? 
               UNION ALL 
               SELECT ?, ?, 0, 'fa' WHERE NOT EXISTS 
               (SELECT 1 FROM user_settings WHERE chat_id = ?)''',
            (chat_id, quality, chat_id, chat_id, quality, chat_id)
        )
        
        conn.commit()
        conn.close()

    def set_user_subtitles(self, chat_id: str, enabled: bool):
        """Set subtitle preference"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            '''INSERT OR REPLACE INTO user_settings (chat_id, quality, subtitles, language)
               SELECT ?, quality, ?, language FROM user_settings 
               WHERE chat_id = ? 
               UNION ALL 
               SELECT ?, 'best', ?, 'fa' WHERE NOT EXISTS 
               (SELECT 1 FROM user_settings WHERE chat_id = ?)''',
            (chat_id, int(enabled), chat_id, chat_id, int(enabled), chat_id)
        )
        
        conn.commit()
        conn.close()

    # ════════════════════════════════════════════════════════════
    # File Cache Methods
    # ════════════════════════════════════════════════════════════

    def cache_file(self, chat_id: str, file_id: str, file_name: str, 
                   file_path: str, file_size: int, youtube_url: str):
        """Cache a downloaded file for later retrieval"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            '''INSERT INTO file_cache 
               (chat_id, file_id, file_name, file_path, file_size, youtube_url, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (chat_id, file_id, file_name, file_path, file_size, youtube_url, int(time.time()))
        )
        
        conn.commit()
        conn.close()

    def get_cached_file(self, file_id: str) -> Optional[Dict]:
        """Retrieve cached file info"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT chat_id, file_name, file_path, file_size FROM file_cache WHERE file_id = ?',
            (file_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None

    def delete_old_files(self, max_age_seconds: int) -> int:
        """Delete files older than max_age_seconds"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cutoff_time = int(time.time()) - max_age_seconds
        cursor.execute('DELETE FROM file_cache WHERE created_at < ?', (cutoff_time,))
        
        conn.commit()
        deleted_count = cursor.rowcount
        conn.close()
        
        return deleted_count

    # ════════════════════════════════════════════════════════════
    # Update Processing Methods
    # ════════════════════════════════════════════════════════════

    def is_update_processed(self, update_id: int) -> bool:
        """Check if update was already processed"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT 1 FROM processed_updates WHERE update_id = ?', (update_id,))
        exists = cursor.fetchone() is not None
        conn.close()
        
        return exists

    def mark_update_processed(self, update_id: int):
        """Mark update as processed"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT OR IGNORE INTO processed_updates (update_id) VALUES (?)',
            (update_id,)
        )
        
        conn.commit()
        conn.close()
