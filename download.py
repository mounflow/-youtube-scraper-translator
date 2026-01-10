"""
Video download module using yt-dlp.
Downloads YouTube videos with subtitles in specified quality.
"""

import yt_dlp
from pathlib import Path
from typing import Optional, Dict
from utils import setup_logger, DOWNLOADS_DIR, validate_file_size, sanitize_filename

logger = setup_logger("download")


def download_video(
    url: str,
    quality: str = "1080",
    download_subs: bool = True,
    sub_lang: str = "en",
    retry: int = 2,
    cookies_from_browser: Optional[str] = None,
    cookies_file: Optional[str] = None
) -> Optional[Dict[str, Path]]:
    """
    Download YouTube video with subtitles.

    Args:
        url: YouTube video URL
        quality: Video quality (e.g., "1080", "720")
        download_subs: Whether to download subtitles
        sub_lang: Subtitle language code (default: "en")
        retry: Number of retry attempts if download fails
        cookies_from_browser: Browser to extract cookies from (e.g., 'chrome', 'firefox', 'edge')
        cookies_file: Path to cookie file in Netscape format

    Returns:
        Dictionary with paths to downloaded files, or None if failed
    """
    ydl_opts = {
        # Force single MP4 file format to avoid HLS fragments (VPN environment fix)
        'format': f'best[height<={quality}][ext=mp4]/best[ext=mp4]/best[height<=480][ext=mp4]/best[height<=360]',
        # Default outtmpl (will be overridden)
        'outtmpl': str(DOWNLOADS_DIR / '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        'prefer_ffmpeg': True,
        # VPN environment tolerance
        'external_downloader_args': ['-timeout', '600000'],  # 10 minutes timeout
        'nocheckcertificate': True,  # Skip certificate verification for VPN
        'http_chunksize': '10485760',  # 10MB chunk size
        # Disable hlsnative to avoid fragment download issues
        'hls_prefer_native': False,
        'retries': 10,  # More retries
        'keepvideo': False,  # Don't keep intermediate files
    }

    # Add cookies if specified
    if cookies_from_browser:
        ydl_opts['cookiesfrombrowser'] = (cookies_from_browser,)
        logger.info(f"Using cookies from browser: {cookies_from_browser}")
    elif cookies_file:
        ydl_opts['cookiefile'] = cookies_file
        logger.info(f"Using cookies from file: {cookies_file}")

    if download_subs:
        ydl_opts.update({
            'writesubtitles': True,
            'writeautomaticsub': True,  # Fallback to auto-generated subs
            'subtitleslangs': [sub_lang],
            'subtitlesformat': 'srt',
        })

    # Step 1: Pre-fetch title to accept clean filename
    clean_title = "video"
    try:
        logger.info("Resolving video title...")
        # Use a separate options dict for pre-fetch
        fetch_opts = {
            'quiet': True,
            'nocheckcertificate': True,
            'retries': 3
        }
        if cookies_from_browser:
            fetch_opts['cookiesfrombrowser'] = (cookies_from_browser,)
        elif cookies_file:
            fetch_opts['cookiefile'] = cookies_file
            
        with yt_dlp.YoutubeDL(fetch_opts) as ydl_temp:
             info_temp = ydl_temp.extract_info(url, download=False)
             raw_title = info_temp.get('title', 'video')
             clean_title = sanitize_filename(raw_title)
             
        # ENFORCE SAFE FILENAME
        ydl_opts['outtmpl'] = str(DOWNLOADS_DIR / f"{clean_title}.%(ext)s")
        logger.info(f"Target filename: {clean_title}")
        
    except Exception as e:
        logger.error(f"Failed to resolve video title: {e}")
        return None
    
    for attempt in range(retry + 1):
        try:
            logger.info(f"Downloading from: {url} (Attempt {attempt + 1}/{retry + 1})")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Download video
                ydl.download([url])

                # Since we enforced the filename, we can now reliably find it
                final_title = clean_title
                
                # Find downloaded files
                video_file = find_video_file(final_title)
                subtitle_file = find_subtitle_file(final_title)

                if not video_file:
                    logger.error(f"Video file not found after download: {final_title}")
                    continue

                # Validate file size
                if not validate_file_size(video_file):
                    logger.error(f"Downloaded video is too small or corrupted: {video_file}")
                    continue
                
                # Get duration
                duration = 0
                try:
                    if 'info_temp' in locals():
                        duration = info_temp.get('duration', 0)
                except:
                    pass

                result = {
                    'video': video_file,
                    'subtitle': subtitle_file,
                    'title': final_title,
                    'duration': duration,
                }

                if subtitle_file:
                    logger.info(f"Downloaded video with subtitle: {video_file.name}")
                    logger.info(f"Subtitle file: {subtitle_file.name}")
                else:
                    logger.warning(f"Downloaded video without subtitle: {video_file.name}")
                    logger.info("Audio file available for Whisper transcription")

                return result

        except Exception as e:
            logger.error(f"Download attempt {attempt + 1} failed: {e}")
            logger.error(f"  URL: {url}")
            if attempt == retry:
                logger.error(f"All {retry + 1} download attempts failed")

    return None


def find_video_file(title: str) -> Optional[Path]:
    """
    Find downloaded video file by title.

    Args:
        title: Video title

    Returns:
        Path to video file or None
    """
    extensions = ['.mp4', '.mkv', '.webm', '.avi']
    for ext in extensions:
        video_file = DOWNLOADS_DIR / f"{title}{ext}"
        if video_file.exists():
            return video_file
    return None


def find_subtitle_file(title: str) -> Optional[Path]:
    """
    Find downloaded subtitle file by title.

    Args:
        title: Video title

    Returns:
        Path to subtitle file or None
    """
    # Check for .srt subtitle
    subtitle_file = DOWNLOADS_DIR / f"{title}.{subtitle_lang_code()}.srt"
    if subtitle_file.exists():
        return subtitle_file

    # Check for .vtt subtitle
    subtitle_file = DOWNLOADS_DIR / f"{title}.{subtitle_lang_code()}.vtt"
    if subtitle_file.exists():
        return subtitle_file

    return None


def subtitle_lang_code() -> str:
    """
    Get yt-dlp subtitle language code format.

    Returns:
        Language code string
    """
    return "en"


def extract_audio(video_path: Path, output_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Extract audio from video file for Whisper transcription.

    Args:
        video_path: Path to video file
        output_dir: Directory to save audio (default: DOWNLOADS_DIR)

    Returns:
        Path to extracted audio file or None
    """
    if output_dir is None:
        output_dir = DOWNLOADS_DIR

    audio_path = output_dir / f"{video_path.stem}.mp3"

    try:
        import ffmpeg

        logger.info(f"Extracting audio from: {video_path.name}")

        (
            ffmpeg
            .input(str(video_path))
            .output(str(audio_path), acodec='libmp3lame', ab='128k')
            .overwrite_output()
            .run(quiet=True)
        )

        if audio_path.exists():
            logger.info(f"Audio extracted successfully: {audio_path.name}")
            return audio_path
        else:
            logger.error("Audio extraction failed - output file not created")
            return None

    except ImportError:
        logger.error("ffmpeg-python not installed. Run: pip install ffmpeg-python")
        return None
    except Exception as e:
        logger.error(f"Error extracting audio: {e}")
        return None
