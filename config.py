"""
Configuration management for YouTube Scraper & Translator.
Loads settings from environment variables or .env file.
"""

import os
from pathlib import Path
from typing import Optional

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Project root directory
PROJECT_ROOT = Path(__file__).parent

# =============================================================================
# FFmpeg Configuration
# =============================================================================
def _find_ffmpeg() -> str:
    """Find FFmpeg executable path."""
    # 1. Check environment variable
    env_path = os.getenv("FFMPEG_PATH")
    if env_path and Path(env_path).exists():
        return env_path
    
    # 2. Check common Windows locations
    common_paths = [
        r"D:\SofewareHome\aboutT\ffmpeg\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
    ]
    for path in common_paths:
        if Path(path).exists():
            return path
    
    # 3. Fallback to PATH
    return "ffmpeg"

FFMPEG_PATH: str = _find_ffmpeg()
FFMPEG_DIR: str = str(Path(FFMPEG_PATH).parent) if FFMPEG_PATH != "ffmpeg" else ""

# =============================================================================
# Node.js Configuration (for yt-dlp)
# =============================================================================
def _find_node() -> str:
    """Find Node.js executable path."""
    # 1. Check environment variable
    env_path = os.getenv("NODE_PATH")
    if env_path and Path(env_path).exists():
        return env_path
    
    # 2. Check common Windows locations
    common_paths = [
        r"C:\Program Files\nodejs\node.exe",
        r"C:\Program Files (x86)\nodejs\node.exe",
    ]
    for path in common_paths:
        if Path(path).exists():
            return path
    
    # 3. Fallback to PATH
    return "node"

NODE_PATH: str = _find_node()

# =============================================================================
# Logging Configuration
# =============================================================================
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

# =============================================================================
# Video Processing Configuration
# =============================================================================
MIN_VIDEO_SIZE_MB: float = float(os.getenv("MIN_VIDEO_SIZE_MB", "1.0"))
DEFAULT_VIDEO_QUALITY: str = os.getenv("DEFAULT_VIDEO_QUALITY", "1080")

# =============================================================================
# Translation Configuration
# =============================================================================
TARGET_LANGUAGE: str = os.getenv("TARGET_LANGUAGE", "zh-CN")
SOURCE_LANGUAGE: str = os.getenv("SOURCE_LANGUAGE", "en")

# =============================================================================
# Output Directories
# =============================================================================
DOWNLOADS_DIR: Path = PROJECT_ROOT / os.getenv("DOWNLOADS_DIR", "downloads")
SUBS_RAW_DIR: Path = PROJECT_ROOT / os.getenv("SUBS_RAW_DIR", "subs_raw")
SUBS_TRANSLATED_DIR: Path = PROJECT_ROOT / os.getenv("SUBS_TRANSLATED_DIR", "subs_translated")
OUTPUT_DIR: Path = PROJECT_ROOT / os.getenv("OUTPUT_DIR", "output")
LOGS_DIR: Path = PROJECT_ROOT / os.getenv("LOGS_DIR", "logs")

# Ensure directories exist
for directory in [DOWNLOADS_DIR, SUBS_RAW_DIR, SUBS_TRANSLATED_DIR, OUTPUT_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


def print_config():
    """Print current configuration for debugging."""
    print("=" * 60)
    print("Current Configuration:")
    print("=" * 60)
    print(f"  FFMPEG_PATH:      {FFMPEG_PATH}")
    print(f"  NODE_PATH:        {NODE_PATH}")
    print(f"  LOG_LEVEL:        {LOG_LEVEL}")
    print(f"  MIN_VIDEO_SIZE:   {MIN_VIDEO_SIZE_MB} MB")
    print(f"  TARGET_LANGUAGE:  {TARGET_LANGUAGE}")
    print(f"  SOURCE_LANGUAGE:  {SOURCE_LANGUAGE}")
    print("=" * 60)


if __name__ == "__main__":
    print_config()
