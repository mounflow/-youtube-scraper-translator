"""
Utility functions for YouTube video processing project.
Provides logging, directory management, and common helper functions.
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional


# Project directories
PROJECT_ROOT = Path(__file__).parent
DOWNLOADS_DIR = PROJECT_ROOT / "downloads"
SUBS_RAW_DIR = PROJECT_ROOT / "subs_raw"
SUBS_TRANSLATED_DIR = PROJECT_ROOT / "subs_translated"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure all directories exist
for directory in [DOWNLOADS_DIR, SUBS_RAW_DIR, SUBS_TRANSLATED_DIR, OUTPUT_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


def setup_logger(name: str = "youtube_processor") -> logging.Logger:
    """
    Set up and return a logger with file and console handlers.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    from config import LOG_LEVEL

    logger = logging.getLogger(name)
    
    # Map string level to logging constant
    level = getattr(logging, LOG_LEVEL, logging.INFO)
    logger.setLevel(level)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Log file with timestamp
    log_file = LOGS_DIR / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    # File handler (Always DEBUG for file)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # Console handler (Use configured level)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger



def validate_file_size(file_path: Path, min_size_mb: Optional[float] = None) -> bool:
    """
    Validate if file size meets minimum requirement.

    Args:
        file_path: Path to the file
        min_size_mb: Minimum size in megabytes (default: from config)

    Returns:
        True if file size >= min_size_mb, False otherwise
    """
    from config import MIN_VIDEO_SIZE_MB
    
    if min_size_mb is None:
        min_size_mb = MIN_VIDEO_SIZE_MB
    if not file_path.exists():
        return False

    size_mb = file_path.stat().st_size / (1024 * 1024)
    return size_mb >= min_size_mb


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


def format_timestamp(seconds: float) -> str:
    """
    Convert seconds to SRT timestamp format (HH:MM:SS,mmm).

    Args:
        seconds: Time in seconds

    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def parse_timestamp(timestamp: str) -> float:
    """
    Parse SRT timestamp to seconds.

    Args:
        timestamp: Timestamp in format HH:MM:SS,mmm

    Returns:
        Time in seconds
    """
    time_part, ms_part = timestamp.split(',')
    h, m, s = map(int, time_part.split(':'))
    ms = int(ms_part)
    return h * 3600 + m * 60 + s + ms / 1000


def get_video_info(url: str) -> dict:
    """
    Extract video ID from YouTube URL.

    Args:
        url: YouTube video URL

    Returns:
        Dictionary with video information
    """
    from urllib.parse import urlparse, parse_qs

    parsed = urlparse(url)
    if parsed.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed.path == '/watch':
            return {'video_id': parse_qs(parsed.query)['v'][0], 'type': 'video'}
        elif parsed.path.startswith('/embed/'):
            return {'video_id': parsed.path.split('/')[2], 'type': 'video'}
    elif parsed.hostname == 'youtu.be':
        return {'video_id': parsed.path[1:], 'type': 'video'}
    return {'video_id': None, 'type': 'unknown'}
