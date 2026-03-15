#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch processing module for YouTube video download and processing.
Supports concurrent downloads with error handling and progress reporting.
"""

import threading
import time
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import setup_logger

logger = setup_logger("batch_processor")


class BatchResult:
    """Data class for batch processing result."""

    def __init__(self, index: int, url: str):
        self.index = index
        self.url = url
        self.status = 'pending'  # pending, processing, success, failed
        self.start_time = None
        self.end_time = None
        self.video_title = None
        self.output_file = None
        self.error = None
        self.duration = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'index': self.index,
            'url': self.url,
            'status': self.status,
            'video_title': self.video_title,
            'output_file': str(self.output_file) if self.output_file else None,
            'duration_seconds': self.duration,
            'error': self.error
        }


class BatchProcessor:
    """Main batch processing class for concurrent video downloads."""

    def __init__(self, max_workers: int = 3, continue_on_error: bool = True):
        """
        Initialize batch processor.

        Args:
            max_workers: Number of concurrent downloads
            continue_on_error: Whether to continue processing on individual failures
        """
        self.max_workers = max_workers
        self.continue_on_error = continue_on_error
        self.results = []
        self.lock = threading.Lock()
        self.start_time = None
        self.end_time = None

    def read_urls_from_file(self, filepath: str) -> List[str]:
        """
        Read URLs from text file, filtering comments and empty lines.

        Args:
            filepath: Path to text file containing URLs

        Returns:
            List of URLs

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(filepath)

        if not file_path.exists():
            raise FileNotFoundError(f"URL file not found: {filepath}")

        urls = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Strip whitespace
                url = line.strip()

                # Skip empty lines and comments
                if not url or url.startswith('#'):
                    continue

                # Basic URL validation
                if 'youtube.com' in url or 'youtu.be' in url:
                    urls.append(url)
                else:
                    logger.warning(f"Skipping invalid YouTube URL: {url}")

        return urls

    def process_single_video(self, url: str, index: int, total: int, args) -> BatchResult:
        """
        Process single video with error handling wrapper.

        Args:
            url: YouTube video URL
            index: Video index in batch (1-based)
            total: Total number of videos in batch
            args: Command line arguments namespace

        Returns:
            BatchResult object with processing status
        """
        result = BatchResult(index, url)
        result.status = 'processing'
        result.start_time = time.time()

        # Import here to avoid circular imports
        from main import handle_download

        try:
            logger.info(f"[{index}/{total}] Processing: {url}")

            # Call existing handle_download function
            handle_download(
                url=url,
                quality=getattr(args, 'quality', '1080'),
                whisper_model=getattr(args, 'whisper_model', 'medium'),
                no_burn=getattr(args, 'no_burn', False),
                preview_only=getattr(args, 'preview_only', False),
                simple_style=getattr(args, 'simple_style', False),
                cookies_from_browser=getattr(args, 'cookies', None),
                cookies_file=getattr(args, 'cookies_file', None),
                style=getattr(args, 'style', 'premium'),
                no_optimize=getattr(args, 'no_optimize', False),
                auto_confirm=getattr(args, 'yes', True),  # Always auto-confirm in batch
                cleanup=getattr(args, 'cleanup', False),
                skip_translation=getattr(args, 'skip_translation', False),
                dub=getattr(args, 'dub', False),
                voice=getattr(args, 'voice', 'zh-CN-YunxiNeural'),
                audio_sync=getattr(args, 'audio_sync', False)
            )

            result.status = 'success'
            result.video_title = 'Processed successfully'  # Title would be set by handle_download
            logger.info(f"[{index}/{total}] ✓ Success: {url}")

        except Exception as e:
            result.status = 'failed'
            result.error = str(e)
            logger.error(f"[{index}/{total}] ✗ Failed: {url} - {e}")

            # If not continuing on error, re-raise
            if not self.continue_on_error:
                raise

        finally:
            result.end_time = time.time()
            result.duration = result.end_time - result.start_time

        return result

    def process_batch(self, urls: List[str], args) -> List[BatchResult]:
        """
        Execute batch processing with ThreadPoolExecutor.

        Args:
            urls: List of YouTube URLs to process
            args: Command line arguments namespace

        Returns:
            List of BatchResult objects
        """
        self.start_time = time.time()
        total = len(urls)
        self.results = []

        logger.info(f"Starting batch processing of {total} videos with {self.max_workers} workers")
        logger.info(f"Continue on error: {self.continue_on_error}")

        # Use ThreadPoolExecutor for concurrent processing
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(
                    self.process_single_video,
                    url,
                    idx,
                    total,
                    args
                ): url
                for idx, url in enumerate(urls, 1)
            }

            # Process completed tasks as they finish
            for future in as_completed(future_to_url):
                url = future_to_url[future]

                try:
                    result = future.result()

                    # Thread-safe result collection
                    with self.lock:
                        self.results.append(result)

                except Exception as e:
                    logger.error(f"Task failed unexpectedly: {url} - {e}")

                    # Create failure result
                    result = BatchResult(0, url)
                    result.status = 'failed'
                    result.error = f"Unexpected error: {str(e)}"
                    result.start_time = time.time()
                    result.end_time = time.time()
                    result.duration = 0

                    with self.lock:
                        self.results.append(result)

                    if not self.continue_on_error:
                        logger.critical("Critical error, stopping batch processing")
                        executor.shutdown(wait=False)
                        raise

        self.end_time = time.time()

        # Sort results by index
        self.results.sort(key=lambda r: r.index)

        return self.results

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """
        Generate and display summary report.

        Args:
            output_file: Optional path to save JSON report

        Returns:
            Formatted report string
        """
        if not self.results:
            return "No results to report."

        total = len(self.results)
        successful = sum(1 for r in self.results if r.status == 'success')
        failed = total - successful
        success_rate = (successful / total * 100) if total > 0 else 0

        total_duration = self.end_time - self.start_time if self.end_time else 0
        avg_duration = total_duration / total if total > 0 else 0

        # Build console report
        report_lines = [
            "=" * 80,
            "Batch Processing Summary",
            "=" * 80,
            f"Total Videos:     {total}",
            f"  ✓ Successful:   {successful} ({success_rate:.1f}%)",
            f"  ✗ Failed:       {failed} ({100 - success_rate:.1f}%)",
            "",
            f"Total Duration:   {self._format_duration(total_duration)}",
            f"Average Time:     {self._format_duration(avg_duration)} per video"
        ]

        # Add failed videos section
        failed_results = [r for r in self.results if r.status == 'failed']
        if failed_results:
            report_lines.extend([
                "",
                "Failed Videos:",
                "-" * 80
            ])
            for result in failed_results[:10]:  # Show max 10 failures
                report_lines.append(
                    f"  {result.index}. {result.url}\n"
                    f"     Error: {result.error}"
                )
            if len(failed_results) > 10:
                report_lines.append(f"  ... and {len(failed_results) - 10} more failures")

        # Add successful output files section
        success_results = [r for r in self.results if r.status == 'success']
        if success_results:
            report_lines.extend([
                "",
                "Output Files:",
                "-" * 80
            ])
            for result in success_results[:5]:  # Show max 5
                report_lines.append(f"  - {result.output_file or 'Output generated'}")
            if len(success_results) > 5:
                report_lines.append(f"  ... and {len(success_results) - 5} more files")

        report_lines.append("=" * 80)

        # Save JSON report if requested
        if output_file:
            self._save_json_report(output_file, successful, failed, success_rate, total_duration)
            report_lines.append(f"\nReport saved to: {output_file}")

        return "\n".join(report_lines)

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            minutes = (seconds % 3600) / 60
            return f"{int(hours)}h {int(minutes)}m"

    def _save_json_report(self, output_file: str, successful: int, failed: int,
                         success_rate: float, total_duration: float):
        """Save detailed JSON report."""
        report_data = {
            'start_time': datetime.fromtimestamp(self.start_time).isoformat() if self.start_time else None,
            'end_time': datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            'total_duration_seconds': total_duration,
            'total_videos': len(self.results),
            'successful': successful,
            'failed': failed,
            'success_rate': success_rate,
            'concurrent_workers': self.max_workers,
            'results': [r.to_dict() for r in self.results],
            'summary': {
                'failed_urls': [r.url for r in self.results if r.status == 'failed'],
                'average_processing_time_seconds': total_duration / len(self.results) if self.results else 0
            }
        }

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        logger.info(f"JSON report saved to: {output_file}")

    def cleanup_original_videos(self):
        """
        Delete original video files from downloads/ directory after successful processing.

        Returns:
            Tuple of (deleted_count, freed_space_gb)
        """
        from pathlib import Path

        downloads_dir = Path('downloads')
        deleted_count = 0
        deleted_size = 0

        if not downloads_dir.exists():
            logger.warning(f"Downloads directory not found: {downloads_dir}")
            return 0, 0

        # Find all video files in downloads/
        video_patterns = ['*.mp4', '*.webm', '*.mkv', '*.avi']
        video_files = []

        for pattern in video_patterns:
            video_files.extend(downloads_dir.glob(pattern))

        # Delete files
        for video_file in video_files:
            try:
                size = video_file.stat().st_size
                video_file.unlink()
                deleted_size += size
                deleted_count += 1
                logger.info(f"Deleted original: {video_file.name}")
            except Exception as e:
                logger.warning(f"Failed to delete {video_file}: {e}")

        freed_gb = deleted_size / (1024 ** 3)
        logger.info(f"Cleanup complete: Deleted {deleted_count} files, freed {freed_gb:.2f} GB")

        return deleted_count, freed_gb
