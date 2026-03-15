#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Course Video Extractor
Extracts all video URLs from a YouTube course using smart search strategies.
"""

import re
from typing import List, Dict, Set
from datetime import datetime
from pathlib import Path

from search import search_videos
from utils import setup_logger

logger = setup_logger("course_extractor")

# YouTube video ID extraction pattern
YT_VIDEO_ID_PATTERN = re.compile(r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})')


def extract_video_id(url: str) -> str:
    """Extract video ID from YouTube URL."""
    match = YT_VIDEO_ID_PATTERN.search(url)
    return match.group(1) if match else None


def search_course_videos(course_name: str, max_results: int = 50,
                        cookies_from_browser: str = None,
                        cookies_file: str = None) -> List[Dict]:
    """
    Search for course videos using multiple strategies.

    Args:
        course_name: Name of the course to search for
        max_results: Maximum number of videos to extract
        cookies_from_browser: Browser to extract cookies from
        cookies_file: Path to cookies file

    Returns:
        List of video info dictionaries
    """
    all_videos = []
    seen_ids: Set[str] = set()

    # Strategy 1: Direct course name search
    logger.info(f"Searching for: {course_name}")
    results, _ = search_videos(
        query=course_name,
        max_results=max_results,
        duration_min=0,  # No duration filter for courses
        duration_max=None,
        upload_date=None,
        cookies_from_browser=cookies_from_browser,
        cookies_file=cookies_file,
        no_filter=True  # Get all results
    )

    for video in results:
        video_id = extract_video_id(video['url'])
        if video_id and video_id not in seen_ids:
            seen_ids.add(video_id)
            all_videos.append(video)

    logger.info(f"Found {len(all_videos)} videos from direct search")

    # Strategy 2: Try with "course" suffix if not enough results
    if len(all_videos) < max_results:
        logger.info(f"Searching for: {course_name} course")
        try:
            results2, _ = search_videos(
                query=f"{course_name} course",
                max_results=max_results,
                duration_min=0,
                duration_max=None,
                upload_date=None,
                cookies_from_browser=cookies_from_browser,
                cookies_file=cookies_file,
                no_filter=True
            )

            for video in results2:
                video_id = extract_video_id(video['url'])
                if video_id and video_id not in seen_ids:
                    seen_ids.add(video_id)
                    all_videos.append(video)

            logger.info(f"Added {len(all_videos)} videos total")
        except Exception as e:
            logger.warning(f"Secondary search failed: {e}")

    # Strategy 3: Try with "playlist" if still not enough
    if len(all_videos) < max_results:
        logger.info(f"Searching for: {course_name} playlist")
        try:
            results3, _ = search_videos(
                query=f"{course_name} playlist",
                max_results=max_results,
                duration_min=0,
                duration_max=None,
                upload_date=None,
                cookies_from_browser=cookies_from_browser,
                cookies_file=cookies_file,
                no_filter=True
            )

            for video in results3:
                video_id = extract_video_id(video['url'])
                if video_id and video_id not in seen_ids:
                    seen_ids.add(video_id)
                    all_videos.append(video)

            logger.info(f"Added {len(all_videos)} videos total")
        except Exception as e:
            logger.warning(f"Playlist search failed: {e}")

    # Strategy 4: Try with "tutorial"
    if len(all_videos) < max_results:
        logger.info(f"Searching for: {course_name} tutorial")
        try:
            results4, _ = search_videos(
                query=f"{course_name} tutorial",
                max_results=max_results,
                duration_min=0,
                duration_max=None,
                upload_date=None,
                cookies_from_browser=cookies_from_browser,
                cookies_file=cookies_file,
                no_filter=True
            )

            for video in results4:
                video_id = extract_video_id(video['url'])
                if video_id and video_id not in seen_ids:
                    seen_ids.add(video_id)
                    all_videos.append(video)

            logger.info(f"Added {len(all_videos)} videos total")
        except Exception as e:
            logger.warning(f"Tutorial search failed: {e}")

    # Sort by upload date (newest first) or title if date not available
    def sort_key(video):
        # Try to extract episode number from title
        title_match = re.search(r'#?(\d+)', video.get('title', ''))
        if title_match:
            return int(title_match.group(1))
        return 0

    all_videos.sort(key=sort_key)

    # Limit to max_results
    return all_videos[:max_results]


def save_course_urls(videos: List[Dict], output_file: str, course_name: str = "Course"):
    """
    Save extracted video URLs to a text file.

    Args:
        videos: List of video info dictionaries
        output_file: Path to output file
        course_name: Name of the course (for header comment)
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        # Write header
        f.write(f"# {course_name}\n")
        f.write(f"# Extracted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total videos: {len(videos)}\n")
        f.write("#\n")
        f.write("# Use this file with: python main.py --batch {} -y\n".format(output_file))
        f.write("#\n")

        # Write videos
        for idx, video in enumerate(videos, 1):
            title = video.get('title', 'Unknown').strip()
            url = video.get('url', '')

            # Clean title for comment (remove special chars)
            clean_title = re.sub(r'[^\w\s-]', '', title)[:60]

            f.write(f"\n# Video {idx}: {clean_title}\n")
            f.write(f"{url}\n")

    logger.info(f"Saved {len(videos)} video URLs to: {output_file}")


def extract_videos_from_multiple_searches(course_name: str,
                                          max_results: int = 50,
                                          cookies_from_browser: str = None,
                                          cookies_file: str = None) -> List[Dict]:
    """
    Main function to extract all course videos.

    Args:
        course_name: Name of the course
        max_results: Maximum number of videos to extract
        cookies_from_browser: Browser to extract cookies from
        cookies_file: Path to cookies file

    Returns:
        List of video info dictionaries
    """
    return search_course_videos(
        course_name=course_name,
        max_results=max_results,
        cookies_from_browser=cookies_from_browser,
        cookies_file=cookies_file
    )
