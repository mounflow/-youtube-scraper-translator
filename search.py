"""
Video search module using yt-dlp.
Searches YouTube videos based on keywords with configurable filters.
"""

import yt_dlp
import time
from typing import List, Dict, Optional, Tuple
from utils import setup_logger, DOWNLOADS_DIR

logger = setup_logger("search")


def search_videos(
    query: str,
    max_results: int = 3,
    duration_min: int = 600,  # 10 minutes in seconds
    duration_max: int = 1200,  # 20 minutes in seconds
    upload_date: Optional[str] = "now-30days",  # Last 30 days
    cookies_from_browser: Optional[str] = None,
    cookies_file: Optional[str] = None,
    no_filter: bool = False
) -> Tuple[List[Dict], float]:
    """
    Search YouTube videos based on query and filters.

    Args:
        query: Search query string
        max_results: Maximum number of results to return
        duration_min: Minimum video duration in seconds (default: 600 = 10 min)
        duration_max: Maximum video duration in seconds (default: 1200 = 20 min)
        upload_date: Date filter for upload time (default: "now-30days")
        cookies_from_browser: Browser to extract cookies from (e.g., 'chrome', 'firefox', 'edge')
        cookies_file: Path to cookie file in Netscape format
        no_filter: If True, skip duration and date filters

    Returns:
        Tuple containing:
            - List of video information dictionaries
            - Float representing search execution time in seconds
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True, # Changed from 'in_search'
        'force_generic_extractor': False,
        'noplaylist': True,
        'format': 'best',
    }

    # Add cookies if specified
    if cookies_from_browser:
        ydl_opts['cookiesfrombrowser'] = (cookies_from_browser,)
        logger.info(f"Using cookies from browser: {cookies_from_browser}")
    elif cookies_file:
        ydl_opts['cookiefile'] = cookies_file
        logger.info(f"Using cookies from file: {cookies_file}")

    search_query = f"ytsearch{max_results}:{query}"

    start_time = time.time()
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Searching for: {query}")
            logger.info(f"Filters: duration {duration_min}-{duration_max}s, upload date: {upload_date}")

            info = ydl.extract_info(search_query, download=False)


            results = []
            for entry in info['entries']:
                if entry is None:
                    continue

                duration = entry.get('duration', 0)

                # Filter by duration (skip if no_filter is True)
                if no_filter or (duration and (duration_min <= duration <= duration_max)):
                    video_info = {
                        'title': entry.get('title', 'Unknown'),
                        'url': f"https://www.youtube.com/watch?v={entry.get('id', '')}",
                        'id': entry.get('id', ''),
                        'duration': duration,
                        'duration_formatted': format_duration(duration) if duration else 'Unknown',
                        'view_count': entry.get('view_count', 0),
                        'description': entry.get('description', '')[:200] + '...' if entry.get('description') else 'No description',
                        'upload_date': entry.get('upload_date', 'Unknown'),
                        'thumbnail': entry.get('thumbnail', ''),
                        'channel': entry.get('channel') or entry.get('uploader') or 'Unknown',
                    }
                    results.append(video_info)

            # Sort by view count (descending)
            results.sort(key=lambda x: x.get('view_count', 0), reverse=True)
            
            duration = time.time() - start_time
            logger.info(f"Found {len(results)} videos in {duration:.2f}s")
            return results, duration

    except Exception as e:
        logger.error(f"Error searching videos: {e}")
        return [], 0.0


def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string (e.g., "12:34")
    """
    seconds = int(seconds)
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"


def display_results(results: List[Dict]) -> None:
    """
    Display search results in a formatted way.

    Args:
        results: List of video information dictionaries
    """
    if not results:
        print("No videos found matching the criteria.")
        return

    print("\n" + "=" * 80)
    print(f"Found {len(results)} videos:")
    print("=" * 80)

    for idx, video in enumerate(results, 1):
        print(f"\n[{idx}] {video['title']}")
        print(f"    URL: {video['url']}")
        print(f"    Duration: {video['duration_formatted']} | Views: {video['view_count']:,}")
        print(f"    Description: {video['description']}")
        print(f"    Upload Date: {video['upload_date']}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    # Test search
    results = search_videos("Quantum Computing 101")
    display_results(results)
