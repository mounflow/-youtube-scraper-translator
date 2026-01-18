#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube Topic Scraper & Chinese Adapter - Main Entry Point

Automated tool to download YouTube videos, extract/generate subtitles,
translate to Chinese, and burn subtitles into videos.
"""

import argparse
import sys
import os
from pathlib import Path

# 设置Windows控制台UTF-8编码
# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    try:
        os.system('chcp 65001 > nul')
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

from utils import setup_logger, SUBS_RAW_DIR, SUBS_TRANSLATED_DIR, format_timestamp
from search import search_videos, display_results
from download import download_video, extract_audio
from subtitle import parse_srt, parse_vtt, transcribe_with_whisper, validate_subtitles
from translate import Translator, save_bilingual_srt
from burn import burn_subtitles, check_ffmpeg_installed, get_video_resolution, calculate_font_size, calculate_ass_font_size
from subtitle_generator import generate_styled_ass
from translation_optimizer import optimize_srt_translation
from dubbing import create_dubbed_video
from style_config import STYLES

logger = setup_logger("main")


def get_available_styles():
    """Get formatted list of available subtitle styles."""
    styles_info = []
    for name, config in STYLES.items():
        desc = config.get("description", "No description")
        styles_info.append(f"  {name}: {desc}")
    return "\n".join(styles_info)



def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description='YouTube Video Scraper & Chinese Adapter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available Subtitle Styles:
{get_available_styles()}

Examples:
  # Search for videos
  python main.py --search "Quantum Computing 101"

  # Search with cookies (fixes YouTube bot detection)
  python main.py --search "Quantum Computing 101" --cookies chrome

  # Search with cookie file (Netscape format)
  python main.py --search "Quantum Computing 101" --cookies-file cookies.txt

  # Search without filters (show all results)
  python main.py --search "Quantum Computing 101" --cookies-file cookies.txt --no-filter

  # Custom filters: 5-30 minutes, no date restriction
  python main.py --search "Quantum Computing" --cookies-file cookies.txt --duration-min 300 --duration-max 1800 --upload-date none

  # Download and process a video
  python main.py --url https://www.youtube.com/watch?v=VIDEO_ID --cookies firefox

  # Process existing downloaded video
  python main.py --video downloads/video.mp4 --subtitle downloads/video.en.srt
        """
    )

    parser.add_argument('-s', '--search', metavar='QUERY', help='Search YouTube videos')
    parser.add_argument('-u', '--url', metavar='URL', help='YouTube video URL to download')
    parser.add_argument('-v', '--video', metavar='PATH', help='Path to downloaded video file')
    parser.add_argument('-b', '--subtitle', metavar='PATH', help='Path to subtitle file')
    parser.add_argument('-q', '--quality', default='1080', help='Video quality (default: 1080)')
    parser.add_argument('--whisper-model', default='medium', choices=['tiny', 'base', 'small', 'medium', 'large'],
                       help='Whisper model size (default: medium)')
    parser.add_argument('--no-burn', action='store_true', help='Skip subtitle burning')
    parser.add_argument('--preview-only', action='store_true', help='Only generate preview, don\'t burn full video')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompts (auto-confirm all)')
    parser.add_argument('--cleanup', action='store_true',
                       help='Clean up intermediary files after processing')
    parser.add_argument('--skip-translation', action='store_true',
                       help='Skip subtitle translation step (use provided subtitle as is)')
    parser.add_argument('--dub', action='store_true',
                       help='Generate Chinese dubbed audio track')
    parser.add_argument('--voice', type=str, default='zh-CN-YunxiNeural',
                       help='Edge-TTS voice for dubbing (default: zh-CN-YunxiNeural)')
    parser.add_argument('--simple-style', action='store_true', help='Use simple SRT style instead of advanced ASS style')
    parser.add_argument('--style', default='premium', help='Subtitle style name (default: premium)')
    parser.add_argument('--no-optimize', action='store_true', help='Disable smart translation optimization (context-aware translation)')
    parser.add_argument('--audio-sync', action='store_true', help='Enable audio waveform-based subtitle timing synchronization')
    parser.add_argument('--cookies', metavar='BROWSER', choices=['chrome', 'firefox', 'edge', 'opera', 'brave', 'chromium'],
                       help='Browser to extract cookies from (fixes YouTube bot detection)')
    parser.add_argument('-c', '--cookies-file', metavar='PATH',
                       help='Path to cookie file in Netscape format (alternative to --cookies)')
    parser.add_argument('--no-filter', action='store_true',
                       help='Disable search filters (duration and upload date)')
    parser.add_argument('--duration-min', type=int, default=600,
                       help='Minimum video duration in seconds (default: 600)')
    parser.add_argument('--duration-max', type=int, default=1200,
                       help='Maximum video duration in seconds (default: 1200)')
    parser.add_argument('--upload-date', type=str, default='now-30days',
                       help='Upload date filter (default: now-30days, use "none" to disable)')

    args = parser.parse_args()

    # Banner
    print("=" * 80)
    print("YouTube Topic Scraper & Chinese Adapter")
    print("=" * 80)

    # Check ffmpeg installation
    if not check_ffmpeg_installed():
        print("\nWarning: ffmpeg is not installed or not in PATH")
        print("Subtitle burning requires ffmpeg.")
        print("Please install from https://ffmpeg.org/download.html\n")

    # Search mode
    if args.search:
        handle_search(args.search, args.cookies, args.cookies_file, args.no_filter,
                     args.duration_min, args.duration_max, args.upload_date)
        return

    # Download mode
    if args.url:
        handle_download(args.url, args.quality, args.whisper_model, args.no_burn, args.preview_only, args.simple_style, args.cookies, args.cookies_file, args.style, args.no_optimize, args.yes, args.cleanup, args.skip_translation, args.dub, args.voice, args.audio_sync)
        return

    # Process existing files mode
    if args.video:
        handle_process(args.video, args.subtitle, args.whisper_model, args.no_burn, args.preview_only, args.simple_style, args.style, args.no_optimize, args.yes, args.cleanup, args.skip_translation, args.dub, args.voice, args.audio_sync)
        return

    # No arguments specified
    parser.print_help()
    print("\nError: Please specify --search, --url, or --video")
    sys.exit(1)


def handle_search(query: str, cookies_from_browser: str = None, cookies_file: str = None,
                  no_filter: bool = False, duration_min: int = 600, duration_max: int = 1200,
                  upload_date: str = "now-30days"):
    """Handle video search command."""
    print(f"\n[Step 1/6] Searching for: {query}")
    if cookies_from_browser:
        print(f"Using cookies from browser: {cookies_from_browser}")
    elif cookies_file:
        print(f"Using cookies from file: {cookies_file}")

    if no_filter:
        filter_info = "No filters applied"
    else:
        date_info = upload_date if upload_date != "none" else "any date"
        filter_info = f"Filters: {duration_min//60}-{duration_max//60} min, {date_info}"
    print(f"Search mode: {filter_info}")
    print("-" * 80)

    # Convert "none" string to None for upload_date
    effective_upload_date = None if upload_date == "none" else upload_date

    results_tuple = search_videos(
        query=query,
        max_results=10 if no_filter else 3,  # More results when no filter
        duration_min=duration_min,
        duration_max=duration_max,
        upload_date=effective_upload_date,
        cookies_from_browser=cookies_from_browser,
        cookies_file=cookies_file,
        no_filter=no_filter
    )
    
    # search_videos returns (results, duration)
    results, _ = results_tuple

    display_results(results)

    if results:
        print("\nTo download a video, run:")
        for i, video in enumerate(results, 1):
            print(f"  python main.py --url {video['url']}")


def handle_download(url: str, quality: str, whisper_model: str, no_burn: bool, preview_only: bool, simple_style: bool, cookies_from_browser: str = None, cookies_file: str = None, style: str = "obama", no_optimize: bool = False, auto_confirm: bool = False, cleanup: bool = False, skip_translation: bool = False, dub: bool = False, voice: str = "zh-CN-YunxiNeural", audio_sync: bool = False):
    """Handle video download and processing."""
    print(f"\n[Step 1/6] Downloading video")
    if cookies_from_browser:
        print(f"Using cookies from browser: {cookies_from_browser}")
    elif cookies_file:
        print(f"Using cookies from file: {cookies_file}")
    print("-" * 80)

    # Download video
    result = download_video(url, quality=quality, cookies_from_browser=cookies_from_browser, cookies_file=cookies_file)

    if not result:
        logger.error("Download failed")
        sys.exit(1)

    print(f"\n[*] Downloaded: {result['title']}")
    print(f"  Video: {result['video']}")
    print(f"  Subtitle: {result['subtitle'] if result['subtitle'] else 'None (will use Whisper)'}")

    # Process the downloaded video
    process_video(result, whisper_model, no_burn, preview_only, simple_style, style, no_optimize, auto_confirm, cleanup, skip_translation, dub, voice, audio_sync)


def handle_process(video_path: str, subtitle_path: str, whisper_model: str, no_burn: bool, preview_only: bool, simple_style: bool, style: str = "obama", no_optimize: bool = False, auto_confirm: bool = False, cleanup: bool = False, skip_translation: bool = False, dub: bool = False, voice: str = "zh-CN-YunxiNeural", audio_sync: bool = False):
    """Handle processing of existing video and subtitle files."""
    video_file = Path(video_path)
    subtitle_file = Path(subtitle_path) if subtitle_path else None

    print(f"\n[Step 1/6] Processing existing files")
    print("-" * 80)

    if not video_file.exists():
        logger.error(f"Video file not found: {video_file}")
        sys.exit(1)

    result = {
        'video': video_file,
        'subtitle': subtitle_file,
        'title': video_file.stem,
    }

    process_video(result, whisper_model, no_burn, preview_only, simple_style, style, no_optimize, auto_confirm, cleanup, skip_translation, dub, voice, audio_sync)


def process_video(result: dict, whisper_model: str, no_burn: bool, preview_only: bool, simple_style: bool = False, style: str = "obama", no_optimize: bool = False, auto_confirm: bool = False, cleanup: bool = False, skip_translation: bool = False, dub: bool = False, voice: str = "zh-CN-YunxiNeural", audio_sync: bool = False):
    """Process video through the complete pipeline."""
    video_file = result['video']
    subtitle_file = result['subtitle']
    video_title = result['title']

    # Track temporary files for cleanup
    temp_files = []

    # Step 2: Extract or transcribe subtitles
    print(f"\n[Step 2/6] Processing subtitles")
    print("-" * 80)

    entries = None

    if subtitle_file and subtitle_file.exists():
        # Parse existing subtitle
        print(f"Parsing subtitle file: {subtitle_file.name}")

        if subtitle_file.suffix == '.srt':
            entries = parse_srt(subtitle_file)
        elif subtitle_file.suffix == '.vtt':
            entries = parse_vtt(subtitle_file)
        else:
            print(f"Unsupported subtitle format: {subtitle_file.suffix}")
    else:
        # No subtitle file, use Whisper
        print("No subtitle file found. Using Whisper for transcription...")

        # Extract audio
        audio_file = extract_audio(video_file)
        if not audio_file:
            logger.error("Audio extraction failed")
            sys.exit(1)

        # Transcribe with Whisper
        entries = transcribe_with_whisper(audio_file, model=whisper_model)

        if not entries:
            logger.error("Whisper transcription failed")
            sys.exit(1)

    if not entries:
        logger.error("No subtitle entries to process")
        sys.exit(1)

    print(f"[*] Processed {len(entries)} subtitle entries")

    # Validate subtitles
    print(f"\n[Step 3/6] Validating subtitles")
    print("-" * 80)

    is_valid, issues = validate_subtitles(entries)

    if is_valid:
        print("[*] Subtitle validation passed")
    else:
        print(f"WARNING: Subtitle validation found {len(issues)} issues:")
        for issue in issues:
            print(f"  - {issue}")

    # Step 4: Translate subtitles
    print(f"\n[Step 4/6] Translating subtitles")
    print("-" * 80)

    try:
        # Prepare subtitle source for generation
        temp_srt_path = SUBS_TRANSLATED_DIR / f"{video_title}_temp_source.srt"
        temp_files.append(temp_srt_path)

        # Decide translation strategy
        if skip_translation:
            print("[*] Skipping translation (using provided subtitles as is)")
            subtitle_source = subtitle_file
        elif not no_optimize:
            print("[*] Translation Optimization: ENABLED (完整句子合并 + 上下文感知)")
            # Save raw entries to SRT first
            with open(temp_srt_path, 'w', encoding='utf-8') as f:
                for entry in entries:
                     f.write(f"{entry.index}\n{format_timestamp(entry.start_time)} --> {format_timestamp(entry.end_time)}\n{entry.text}\n\n")

            # Run new sentence-based optimizer
            from sentence_subtitle_optimizer import optimize_srt
            optimized_srt_path = SUBS_TRANSLATED_DIR / f"{video_title}_sentence_optimized.srt"

            # Pass video path and audio sync flag to optimizer
            video_path_for_optimizer = str(video_file) if hasattr(video_file, 'resolve') else str(video_file)
            optimize_success = optimize_srt(
                str(temp_srt_path),
                str(optimized_srt_path),
                video_path=video_path_for_optimizer,
                audio_sync=audio_sync
            )

            if optimize_success:
                subtitle_source = optimized_srt_path
            else:
                logger.error("优化失败，回退到标准翻译")
                no_optimize = True # Fallback

        if no_optimize:
            print("[*] Translation Optimization: DISABLED (Line-by-line translation)")
            translator = Translator()
            translated = translator.translate_subtitles(entries)
            print(f"[*] Translated {len(translated)} entries")
            
            # Save to SRT
            save_bilingual_srt(translated, temp_srt_path, format_type="bilingual")
            subtitle_source = temp_srt_path

        # Determine output format
        if not simple_style:
            # Generate Advanced ASS with resolution-based font sizing
            subtitle_output = SUBS_TRANSLATED_DIR / f"{video_title}_styled.ass"
            try:
                # Detect video resolution for font sizing
                resolution = get_video_resolution(video_file)
                custom_font_size = None
                if resolution:
                    custom_font_size = calculate_ass_font_size(resolution)
                    print(f"[*] Video resolution: {resolution[0]}x{resolution[1]}")
                    print(f"[*] Calculated ASS font size: {custom_font_size}px")
                else:
                    print("[WARNING] Could not detect video resolution, using default font size")

                generate_styled_ass(str(subtitle_source), str(subtitle_output), style_name=style, custom_font_size=custom_font_size)
                print(f"[*] Generated Styled ASS ({style}): {subtitle_output.name}")
            except Exception as e:
                logger.error(f"ASS generation failed: {e}")
                subtitle_output = subtitle_source # Fallback to SRT
        else:
            # Use Simple SRT
            subtitle_output = subtitle_source
            print(f"[*] Using Simple SRT: {subtitle_output.name}")

        subtitle_for_burn = subtitle_output

        # Display sample
        if 'translated' in locals() and translated:
            print("\nSample translation:")
            sample = translated[0]
            print(f"  EN: {sample['original']}")
            print(f"  ZH: {sample['translated']}")

        # Cleanup temporary files
        if cleanup:
            cleaned_count = 0
            for temp_file in temp_files:
                if temp_file.exists():
                    try:
                        temp_file.unlink()
                        cleaned_count += 1
                        logger.info(f"Cleaned up temporary file: {temp_file.name}")
                    except Exception as e:
                        logger.warning(f"Failed to cleanup {temp_file.name}: {e}")
            if cleaned_count > 0:
                print(f"[*] Cleaned up {cleaned_count} temporary file(s)")

    except Exception as e:
        logger.error(f"Translation failed: {e}")
        sys.exit(1)

    # Step 5 & 6: Burn subtitles
    if not no_burn:
        print(f"\n[Step 5/6] Preparing subtitle burning")
        print("-" * 80)

        # Get video resolution for font sizing
        resolution = get_video_resolution(video_file)
        if resolution:
            if not simple_style:
                font_size = calculate_ass_font_size(resolution)
            else:
                font_size = calculate_font_size(resolution)
            print(f"Video resolution: {resolution[0]}x{resolution[1]}")
            print(f"Font size: {font_size}")
            custom_style = {'FontSize': font_size}
        else:
            custom_style = None

        print(f"\n[Step 6/6] Burning subtitles")
        print("-" * 80)

        # Generate preview first
        preview_path = burn_subtitles(video_file, subtitle_for_burn, preview_only=True)

        if preview_path:
            print(f"[*] Preview generated: {preview_path}")

            if not preview_only:
                # Ask for confirmation (skip if --yes flag is set)
                if auto_confirm:
                    print("\n[*] Auto-confirming with --yes flag...")
                    response = 'y'
                else:
                    response = input("\nPreview the image above. Continue with full video? (y/n): ")

                if response.lower() == 'y':
                    output_file = burn_subtitles(video_file, subtitle_for_burn, style=custom_style)

                    if output_file:
                        print(f"[*] Final video: {output_file}")
                        print("\n" + "=" * 80)
                        print("Processing complete!")
                        print("=" * 80)
                    else:
                        logger.error("Subtitle burning failed")
                        sys.exit(1)
                else:
                    print("Cancelled. Bilingual subtitles saved for manual use.")
                    output_file = None # No output file generated
        else:
            logger.error("Preview generation failed")
            output_file = None
    else:
        print(f"\n[Step 5/6] Skipping subtitle burning (--no-burn specified)")
        print("-" * 80)
        output_file = video_file # Use original file for dubbing if burning skipped

    # Step 7: Dubbing (New)
    if dub and output_file:
         print(f"\n[Step 7/7] Generating Chinese Dubbing")
         print("-" * 80)
         
         dubbed_output = output_file.with_name(f"{output_file.stem}_dubbed{output_file.suffix}")
         print(f"[*] Voice: {voice}")
         print(f"[*] Generating audio... (this may take a while)")
         
         # subtitle_for_burn usually points to the styled ASS or the SRT
         # dubbing needs the SRT content. 
         # subtitle_source was set earlier to point to the processed SRT
         
         success = create_dubbed_video(str(subtitle_source), str(output_file), str(dubbed_output), voice)
         
         if success:
             print(f"[*] Dubbed video saved to: {dubbed_output}")
             print("\n" + "=" * 80)
             print("Processing complete! (Dubbing + Burning)")
             print("=" * 80)
         else:
             logger.error("Dubbing failed")
    
    if not dub and not no_burn and output_file:
        print("\n" + "=" * 80)
        print("Processing complete!")
        print("=" * 80)
    
    if not dub and no_burn:
        print("\n" + "=" * 80)
        print("Processing complete! (No burning performed)")
        print("=" * 80)
        print(f"Bilingual subtitles saved to: {subtitle_output}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
