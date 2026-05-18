"""
YouTube downloader module using yt-dlp
Handles video downloading with quality selection
"""

import subprocess
import json
import re
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)


class YouTubeDownloader:
    """Wrapper around yt-dlp for downloading videos"""

    YOUTUBE_URL_PATTERNS = [
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?youtu\.be\/([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
    ]

    # Quality format mapping for yt-dlp
    QUALITY_FORMAT_MAP = {
        'best': 'best[ext=mp4]/best',
        '1080': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]',
        '720': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]',
        '480': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]',
        'audio': 'bestaudio[ext=m4a]/bestaudio',
    }

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        venv_bin = Path(os.environ.get('HOME', '/home/testyt')) / 'venv' / 'bin' / 'yt-dlp'
        if venv_bin.exists():
            self.yt_dlp_path = str(venv_bin)
        else:
            self.yt_dlp_path = 'yt-dlp'

    @staticmethod
    def extract_youtube_urls(text: str) -> list:
        """Extract YouTube URLs from text"""
        urls = []
        for pattern in YouTubeDownloader.YOUTUBE_URL_PATTERNS:
            matches = re.findall(pattern, text)
            for video_id in matches:
                urls.append(f"https://www.youtube.com/watch?v={video_id}")
        return list(set(urls))  # Remove duplicates

    @staticmethod
    def is_valid_youtube_url(url: str) -> bool:
        """Check if URL is a valid YouTube URL"""
        return bool(YouTubeDownloader.extract_youtube_urls(url))

    def download(self, youtube_url: str, quality: str = 'best', 
                 subtitles: bool = False) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Download a YouTube video
        
        Returns: (success: bool, file_path: Optional[str], error: Optional[str])
        """
        try:
            # Validate URL
            if not self.is_valid_youtube_url(youtube_url):
                return False, None, "Invalid YouTube URL"

            # Get format string
            format_string = self.QUALITY_FORMAT_MAP.get(quality, 'best')

# Build yt-dlp command
            cmd = [
                self.yt_dlp_path,
                '--format', format_string,
                '--output', str(self.output_dir / '%(title)s.%(ext)s'),
                '--socket-timeout', '30',
                '--retries', '3',
                '--max-filesize', f'{45*1024*1024}',
            ]

            # Add subtitle options if requested
            if subtitles:
                cmd.extend([
                    '--write-subs',
                    '--sub-langs', 'fa,en',
                    '--skip-unavailable-subs'
                ])

            # Add audio codec specification for audio format
            if quality == 'audio':
                cmd.extend(['--audio-format', 'mp3', '--audio-quality', '192'])

            cmd.append(youtube_url)

            logger.info(f"🎬 Starting download: {youtube_url} (Quality: {quality})")
            
            # Execute download
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                logger.error(f"❌ Download failed: {error_msg}")
                return False, None, f"Download failed: {error_msg[:100]}"

            # Find the downloaded file
            files = list(self.output_dir.glob('*'))
            if not files:
                return False, None, "No file was downloaded"

            # Get the most recently created file
            latest_file = max(files, key=lambda p: p.stat().st_mtime)
            
            logger.info(f"✅ Download successful: {latest_file.name}")
            return True, str(latest_file), None

        except subprocess.TimeoutExpired:
            return False, None, "Download timeout (30 minutes exceeded)"
        except FileNotFoundError:
            return False, None, "yt-dlp not installed. Install: pip install yt-dlp"
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
            return False, None, f"Error: {str(e)[:100]}"

    def get_video_info(self, youtube_url: str) -> Optional[Dict]:
        """Get video information without downloading"""
        try:
            if not self.is_valid_youtube_url(youtube_url):
                return None

            cmd = [
                self.yt_dlp_path,
                '--dump-json',
                '--socket-timeout', '30',
                youtube_url
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                logger.error(f"Failed to get video info: {result.stderr}")
                return None

            info = json.loads(result.stdout)
            return {
                'title': info.get('title'),
                'duration': info.get('duration'),
                'uploader': info.get('uploader'),
                'view_count': info.get('view_count'),
                'age_restricted': info.get('age_restricted', False),
            }

        except json.JSONDecodeError:
            logger.error("Failed to parse video info JSON")
            return None
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            return None

    def cleanup_old_files(self, max_age_seconds: int = 300) -> int:
        """Delete files older than max_age_seconds"""
        import time
        current_time = time.time()
        deleted_count = 0

        for file_path in self.output_dir.glob('*'):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"🗑️ Deleted old file: {file_path.name}")
                    except Exception as e:
                        logger.error(f"Error deleting {file_path.name}: {str(e)}")

        return deleted_count
