"""
Subtitle burning module using ffmpeg.
Burns subtitles into video files with customizable styling.
"""

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict
from utils import setup_logger, OUTPUT_DIR, validate_file_size
from config import FFMPEG_PATH, FFMPEG_DIR

logger = setup_logger("burn")



def burn_subtitles(
    video_path: Path,
    subtitle_path: Path,
    output_path: Optional[Path] = None,
    style: Optional[Dict] = None,
    preview_only: bool = False,
    force_style: bool = False,
    progress_callback = None,
    progress_mgr=None
) -> Optional[Path]:
    """
    Burn subtitles into video using ffmpeg.

    Args:
        video_path: Path to input video file
        subtitle_path: Path to subtitle file (.srt, .ass, or .vtt)
        output_path: Path for output video (default: OUTPUT_DIR)
        style: Dictionary with subtitle style options (only used for SRT)
        preview_only: If True, only generate preview image
        force_style: If True, apply force_style (NOT recommended for ASS files)
        progress_callback: Optional callback function(float, str) for progress updates
        progress_mgr: ProgressManager instance for Rich progress bars

    Returns:
        Path to output file or None if failed
    """
    if output_path is None:
        output_path = OUTPUT_DIR / f"{video_path.stem}_subtitled.mp4"

    # Default subtitle style (optimized for bilingual subtitles)
    default_style = {
        'FontName': 'Microsoft YaHei,SimHei,Arial',  # Chinese fonts优先
        'FontSize': 20,  # Smaller default size (inline styles will override)
        'PrimaryColour': '&HFFFFFF',  # White
        'OutlineColour': '&H000000',  # Black outline
        'Outline': 1,  # Thinner outline
        'Shadow': 2,  # Subtle shadow for readability
        'Alignment': '2',  # Bottom center
        'MarginV': 50,  # Position in lower 10% safety zone
        'MarginL': 30,  # Left margin (safety zone)
        'MarginR': 30,  # Right margin (safety zone)
    }

    if style:
        default_style.update(style)

    # Build style string
    style_str = ','.join(f"{k}={v}" for k, v in default_style.items())

    # For FFmpeg subtitles filter on Windows, copy subtitle to current directory
    # to use a simple relative filename that FFmpeg can find
    import shutil
    import os

    # Save current directory
    original_dir = os.getcwd()

    # Change to video's directory to ensure relative paths work
    video_dir = str(video_path.parent)
    os.chdir(video_dir)

    # Detect subtitle format
    is_ass = subtitle_path.suffix.lower() == '.ass'

    # Copy subtitle to this directory with appropriate extension
    temp_subtitle = Path(f"temp_subs{subtitle_path.suffix}")
    shutil.copy(str(subtitle_path), str(temp_subtitle))

    # Use just the filename (relative path from video's directory)
    subtitle_abs = temp_subtitle.name
    video_filename = video_path.name  # Use just filename since we're in video's directory

    # For ASS format, don't use force_style (ASS has its own styling)
    # For SRT/VTT, use force_style for better rendering
    use_force_style = force_style or not is_ass

    try:
        import ffmpeg

        # Ensure FFmpeg directory is in PATH so ffmpeg-python can find the binary
        if FFMPEG_DIR and FFMPEG_DIR not in os.environ.get('PATH', ''):
            os.environ['PATH'] = FFMPEG_DIR + os.pathsep + os.environ.get('PATH', '')
            logger.debug(f"Added FFmpeg to PATH: {FFMPEG_DIR}")

        logger.info(f"Burning subtitles into video: {video_path.name}")

        if preview_only:
            # Generate preview at 10 seconds
            preview_path = OUTPUT_DIR / f"{video_path.stem}_preview.png"
            logger.info(f"Generating preview image at 10 seconds...")

            try:
                # Build filter
                if use_force_style:
                    vf_filter = f"subtitles={subtitle_abs}:force_style='{style_str}'"
                else:
                    # For ASS files, rely on internal styling
                    vf_filter = f"subtitles={subtitle_abs}"
                    logger.info(f"Using ASS internal styling (no force_style)")

                # Run with proper error handling
                try:
                    (
                        ffmpeg
                        .input(video_filename, ss=10)
                        .output(
                            str(preview_path),
                            vframes=1,
                            vf=vf_filter
                        )
                        .overwrite_output()
                        .run(capture_stdout=True, capture_stderr=True)
                    )
                except ffmpeg.Error as e:
                    logger.error(f"FFmpeg error: {e.stderr.decode('utf-8') if e.stderr else 'Unknown error'}")
                    raise

                if preview_path.exists():
                    logger.info(f"Preview saved to: {preview_path}")
                    return preview_path
                else:
                    logger.error("Preview generation failed")
                    return None
            finally:
                # Cleanup: restore directory and remove temp file
                os.chdir(original_dir)
                if temp_subtitle.exists():
                    temp_subtitle.unlink()

        else:
            # Burn subtitles into full video
            logger.info(f"Processing video (this may take a while)...")

            try:
                # Get video duration for progress calculation
                try:
                    probe = ffmpeg.probe(video_filename)
                    duration = float(probe['format']['duration'])
                    total_frames = int(float(probe['streams'][0].get('nb_frames', 0)))
                    if total_frames == 0:
                        # Estimate from duration and fps
                        fps = eval(probe['streams'][0].get('r_frame_rate', '25/1'))
                        total_frames = int(duration * fps)
                except:
                    duration = 0
                    total_frames = 0
                
                # Build filter
                if use_force_style:
                    vf_filter = f"subtitles={subtitle_abs}:force_style='{style_str}'"
                else:
                    vf_filter = f"subtitles={subtitle_abs}"
                    logger.info(f"Using ASS internal styling (no force_style)")

                # Check for hardware acceleration
                use_nvenc = check_nvenc_support()
                if use_nvenc:
                    logger.info("⚡ NVIDIA NVENC Hardware Acceleration Enabled")
                    cmd = [
                        FFMPEG_PATH,
                        '-hwaccel', 'auto',
                        '-i', video_filename,
                        '-vf', vf_filter,
                        '-c:v', 'h264_nvenc',
                        '-preset', 'p4',       # Balance between speed and quality for NVENC
                        '-rc', 'vbr',
                        '-cq', '28',           # Constant quality
                        '-c:a', 'copy',
                        '-vsync', 'cfr',
                        '-async', '1',
                        '-y',
                        str(output_path)
                    ]
                else:
                    logger.info("💻 Using CPU Encoding (Multithreaded Ultrafast)")
                    cmd = [
                        FFMPEG_PATH,
                        '-i', video_filename,
                        '-vf', vf_filter,
                        '-c:v', 'libx264',
                        '-c:a', 'copy',
                        '-preset', 'ultrafast', # Maximum CPU speed
                        '-threads', '0',        # Maximize multithreading
                        '-crf', '23',
                        '-vsync', 'cfr',
                        '-async', '1',
                        '-y',
                        str(output_path)
                    ]
                
                # Run with progress monitoring
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    bufsize=1
                )
                
                # Monitor progress from stderr
                import re
                last_print_pct = 0

                # 创建 Rich 进度条任务
                task_id = None
                if progress_mgr and total_frames > 0:
                    task_id = progress_mgr.burn_task(total_frames)

                for line in process.stderr:
                    # Parse frame number from FFmpeg output
                    match = re.search(r'frame=\s*(\d+)', line)
                    if match:
                        current_frame = int(match.group(1))
                        if total_frames > 0:
                            progress = min(current_frame / total_frames, 0.99)
                            pct = int(progress * 100)

                            # 更新 Rich 进度条
                            if progress_mgr and task_id:
                                progress_mgr.progress.update(
                                    task_id,
                                    completed=current_frame,
                                    description=f"烧录字幕 {current_frame}/{total_frames} 帧 ({pct}%)"
                                )

                            # Print every 5% for API to parse
                            if pct >= last_print_pct + 5:
                                print(f"[Burning] frame={current_frame} progress={pct}%", flush=True)
                                last_print_pct = pct
                            if progress_callback:
                                progress_callback(progress, f"Burning: {pct}%")
                        else:
                            # No total frames, just print frame count
                            if current_frame % 100 == 0:
                                print(f"[Burning] frame={current_frame}", flush=True)
                
                process.wait()
                
                if process.returncode != 0:
                    raise Exception(f"FFmpeg failed with code {process.returncode}")

                if output_path.exists():
                    # Validate output
                    if validate_file_size(output_path):
                        logger.info(f"Subtitle burning complete: {output_path.name}")
                        return output_path
                    else:
                        logger.error("Output file validation failed")
                        return None
                else:
                    logger.error("Output file was not created")
                    return None
            finally:
                # Cleanup: restore directory and remove temp file
                os.chdir(original_dir)
                if temp_subtitle.exists():
                    temp_subtitle.unlink()

    except ImportError as e:
        # Cleanup before exit
        os.chdir(original_dir)
        if temp_subtitle.exists():
            temp_subtitle.unlink()

        logger.critical(f"ffmpeg-python import failed: {e}")
        logger.critical("Run: pip install ffmpeg-python")
        return None

    except Exception as e:
        # Cleanup on error
        os.chdir(original_dir)
        if 'temp_subtitle' in locals() and temp_subtitle.exists():
            temp_subtitle.unlink()
        logger.error(f"Error burning subtitles: {e}")
        return None


def _burn_with_subprocess(
    video_path: Path,
    subtitle_path: Path,
    output_path: Path,
    style_str: str,
    preview_only: bool = False
) -> Optional[Path]:
    """
    Fallback method using subprocess to call ffmpeg directly.

    Args:
        video_path: Path to input video
        subtitle_path: Path to subtitle file
        output_path: Path for output
        style_str: FFmpeg subtitle style string
        preview_only: Generate preview only

    Returns:
        Path to output file or None
    """
    import shutil
    import os

    # Save current directory
    original_dir = os.getcwd()

    # Change to video's directory
    video_dir = str(video_path.parent)
    os.chdir(video_dir)

    # Copy subtitle to this directory with a simple name
    temp_subtitle = Path("temp_subs.srt")
    shutil.copy(str(subtitle_path), str(temp_subtitle))
    subtitle_abs = "temp_subs.srt"

    try:
        if preview_only:
            # Generate preview
            preview_path = OUTPUT_DIR / f"{video_path.stem}_preview.png"
            cmd = [
                FFMPEG_PATH,
                '-ss', '10',
                '-i', str(video_path.name),
                '-vframes', '1',
                '-vf', f"subtitles={subtitle_abs}:force_style='{style_str}'",
                str(preview_path),
                '-y'
            ]
        else:
            # Burn subtitles
            cmd = [
                FFMPEG_PATH,
                '-i', str(video_path.name),
                '-vf', f"subtitles={subtitle_abs}:force_style='{style_str}'",
                '-c:v', 'libx264',
                '-c:a', 'copy',
                '-preset', 'veryfast',
                '-crf', '23',
                '-async', '1',
                '-vsync', 'cfr',
                str(output_path),
                '-y'
            ]

        logger.info(f"Running ffmpeg command...")
        logger.debug(f"Command: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        output_file = output_path if not preview_only else (OUTPUT_DIR / f"{video_path.stem}_preview.png")

        if output_file.exists():
            logger.info(f"FFmpeg processing complete: {output_file.name}")
            return output_file
        else:
            logger.error("FFmpeg completed but output file not found")
            return None

    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e}")
        logger.error(f"stderr: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Error running FFmpeg: {e}")
        return None
    finally:
        # Cleanup: restore directory and remove temp file
        os.chdir(original_dir)
        if temp_subtitle.exists():
            temp_subtitle.unlink()


def check_nvenc_support() -> bool:
    """Check if NVIDIA NVENC hardware encoder is supported."""
    if not FFMPEG_PATH:
        return False
    try:
        # Check if h264_nvenc encoder exists in ffmpeg
        result = subprocess.run(
            [FFMPEG_PATH, '-encoders'],
            capture_output=True, text=True, timeout=5
        )
        if 'h264_nvenc' in result.stdout:
            # Let's do a fast test to see if hardware is actually available
            test_cmd = [
                FFMPEG_PATH, '-f', 'lavfi', '-i', 'color=size=64x64:duration=0.1', 
                '-c:v', 'h264_nvenc', '-f', 'null', '-'
            ]
            test_result = subprocess.run(test_cmd, capture_output=True, timeout=5)
            # 0 means encode succeeded, hardware available
            if test_result.returncode == 0:
                return True
        return False
    except Exception:
        return False


def check_ffmpeg_installed() -> bool:
    """
    Check if ffmpeg is installed and accessible.

    Returns:
        True if ffmpeg is available, False otherwise
    """
    if FFMPEG_PATH and FFMPEG_PATH != 'ffmpeg':
        return Path(FFMPEG_PATH).exists()
    # Fallback: try running ffmpeg
    try:
        result = subprocess.run(
            [FFMPEG_PATH, '-version'],
            capture_output=True, timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def get_video_resolution(video_path: Path) -> Optional[tuple]:
    """
    Get video resolution using ffmpeg.

    Args:
        video_path: Path to video file

    Returns:
        Tuple of (width, height) or None
    """
    try:
        import ffmpeg

        # Set FFmpeg binary path if needed
        if FFMPEG_PATH != 'ffmpeg':
            import ffmpeg._nodes
            ffmpeg._nodes.get_ffmpeg_bin = lambda: FFMPEG_PATH

        probe = ffmpeg.probe(str(video_path))
        video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')

        width = int(video_info['width'])
        height = int(video_info['height'])

        return (width, height)

    except ImportError:
        # Fallback to subprocess if ffmpeg-python not available
        logger.warning("ffmpeg-python not available, using subprocess fallback")
        try:
            # Use ffprobe to get video info (faster than ffmpeg)
            ffprobe_path = FFMPEG_PATH.replace('ffmpeg.exe', 'ffprobe.exe') if FFMPEG_PATH != 'ffmpeg' else 'ffprobe'

            cmd = [
                ffprobe_path,
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height',
                '-of', 'csv=p=0',
                str(video_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )

            # Parse output: "1280,720" (comma-separated)
            output = result.stdout.strip()
            if ',' in output:
                parts = output.split(',')
                width = int(parts[0])
                height = int(parts[1])
                return (width, height)

        except Exception as e:
            logger.error(f"Error getting video resolution with subprocess: {e}")
            return None

    except Exception as e:
        logger.error(f"Error getting video resolution: {e}")
        return None


def calculate_font_size(resolution: tuple) -> int:
    """
    Calculate appropriate font size for SRT subtitles based on video resolution.

    Args:
        resolution: Tuple of (width, height)

    Returns:
        Recommended font size for SRT
    """
    height = resolution[1]

    # Scale font size based on video height
    if height <= 480:
        return 18
    elif height <= 720:
        return 24
    elif height <= 1080:
        return 28
    else:
        return 32




def calculate_ass_font_size(resolution: tuple) -> int:
    """
    Calculate ASS font size based on video resolution.
    Returns values suitable for ASS rendering (2/3 of original size).
    """
    height = resolution[1]

    # Scale font size based on video height (ASS native pixels)
    # Reduced to 2/3 of original size for better readability
    if height <= 480:
        return 27   # 40 * 2/3
    elif height <= 720:
        return 40   # 60 * 2/3
    elif height <= 1080:
        return 57   # 85 * 2/3 ≈ 56.67
    else:
        # 4K and beyond
        return 80   # 120 * 2/3


if __name__ == "__main__":
    import sys

    # Check ffmpeg installation
    if not check_ffmpeg_installed():
        print("Error: ffmpeg is not installed or not in PATH")
        print("Please install ffmpeg from https://ffmpeg.org/download.html")
        sys.exit(1)

    if len(sys.argv) > 2:
        video_file = Path(sys.argv[1])
        subtitle_file = Path(sys.argv[2])

        # Get video resolution and adjust font size
        resolution = get_video_resolution(video_file)
        if resolution:
            font_size = calculate_font_size(resolution)
            print(f"Video resolution: {resolution[0]}x{resolution[1]}")
            print(f"Using font size: {font_size}")

            custom_style = {
                'FontSize': font_size,
            }
        else:
            custom_style = None

        # Generate preview first
        print("\nGenerating preview...")
        preview = burn_subtitles(video_file, subtitle_file, preview_only=True)

        if preview:
            print(f"Preview saved to: {preview}")
            response = input("\nContinue with full video burning? (y/n): ")

            if response.lower() == 'y':
                output = burn_subtitles(video_file, subtitle_file, style=custom_style)

                if output:
                    print(f"\nSuccess! Output saved to: {output}")
                else:
                    print("\nSubtitle burning failed")
            else:
                print("Cancelled")
        else:
            print("Preview generation failed")
    else:
        print("Usage: python burn.py <video_file> <subtitle_file>")
