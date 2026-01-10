"""
Subtitle processing module.
Handles parsing, cleaning, and validation of subtitle files (SRT/VTT).
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple
from utils import setup_logger, SUBS_RAW_DIR, parse_timestamp, format_timestamp

logger = setup_logger("subtitle")


class SubtitleEntry:
    """Represents a single subtitle entry with timing and text."""

    def __init__(self, index: int, start_time: float, end_time: float, text: str):
        self.index = index
        self.start_time = start_time
        self.end_time = end_time
        self.text = text

    def __repr__(self):
        return f"SubtitleEntry({self.index}, {self.start_time:.2f}-{self.end_time:.2f}, {self.text[:30]}...)"


def parse_srt(file_path: Path) -> List[SubtitleEntry]:
    """
    Parse SRT subtitle file.

    Args:
        file_path: Path to SRT file

    Returns:
        List of SubtitleEntry objects
    """
    entries = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split by double newlines to separate subtitle blocks
        blocks = re.split(r'\n\s*\n', content.strip())

        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue

            # Parse index
            try:
                index = int(lines[0].strip())
            except ValueError:
                continue

            # Parse timestamp
            time_match = re.search(
                r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})',
                lines[1]
            )
            if not time_match:
                continue

            start_time = parse_timestamp(time_match.group(1))
            end_time = parse_timestamp(time_match.group(2))

            # Parse text (may be multiple lines)
            text = '\n'.join(lines[2:]).strip()

            # Remove HTML tags and cleanup
            text = clean_text(text)

            if text:
                entries.append(SubtitleEntry(index, start_time, end_time, text))

        logger.info(f"Parsed {len(entries)} subtitle entries from {file_path.name}")
        return entries

    except Exception as e:
        logger.error(f"Error parsing SRT file {file_path}: {e}")
        logger.error(f"  File size: {file_path.stat().st_size if file_path.exists() else 0} bytes")
        logger.error(f"  Hint: Check if file encoding is UTF-8 and format is valid")
        return []


def parse_vtt(file_path: Path) -> List[SubtitleEntry]:
    """
    Parse WebVTT subtitle file.

    Args:
        file_path: Path to VTT file

    Returns:
        List of SubtitleEntry objects
    """
    entries = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove WEBVTT header
        content = re.sub(r'WEBVTT.*?\n\n', '', content, flags=re.DOTALL)

        # Split by double newlines
        blocks = re.split(r'\n\s*\n', content.strip())

        index = 0
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 2:
                continue

            # Parse timestamp (VTT format)
            time_match = re.search(
                r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})',
                lines[0]
            )
            if not time_match:
                # Try alternative format without hours
                time_match = re.search(
                    r'(\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}\.\d{3})',
                    lines[0]
                )
                if time_match:
                    # Add hours
                    start = "00:" + time_match.group(1)
                    end = "00:" + time_match.group(2)
                    # Convert to SRT format
                    start = start.replace('.', ',')
                    end = end.replace('.', ',')
                    start_time = parse_timestamp(start)
                    end_time = parse_timestamp(end)
                else:
                    continue
            else:
                start = time_match.group(1).replace('.', ',')
                end = time_match.group(2).replace('.', ',')
                start_time = parse_timestamp(start)
                end_time = parse_timestamp(end)

            index += 1

            # Parse text
            text = '\n'.join(lines[1:]).strip()
            text = clean_text(text)

            if text:
                entries.append(SubtitleEntry(index, start_time, end_time, text))

        logger.info(f"Parsed {len(entries)} subtitle entries from VTT file")
        return entries

    except Exception as e:
        logger.error(f"Error parsing VTT file {file_path}: {e}")
        logger.error(f"  File size: {file_path.stat().st_size if file_path.exists() else 0} bytes")
        logger.error(f"  Hint: Check if file encoding is UTF-8 and format is valid")
        return []


def clean_text(text: str) -> str:
    """
    Clean subtitle text by removing HTML tags and extra whitespace.

    Args:
        text: Raw subtitle text

    Returns:
        Cleaned text
    """
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Remove common subtitle artifacts
    text = re.sub(r'\{.*?\}', '', text)  # Remove {brackets}
    text = re.sub(r'\[.*?\]', '', text)  # Remove [brackets]
    text = re.sub(r'\(.*?\)', '', text)  # Remove (parentheses)

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    # Remove common speaker labels
    text = re.sub(r'^(Speaker|Narrator|Host|Guest):\s*', '', text, flags=re.IGNORECASE)

    return text


def save_srt(entries: List[SubtitleEntry], output_path: Path) -> None:
    """
    Save subtitle entries as SRT file.

    Args:
        entries: List of SubtitleEntry objects
        output_path: Output file path
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for entry in entries:
                f.write(f"{entry.index}\n")
                f.write(f"{format_timestamp(entry.start_time)} --> {format_timestamp(entry.end_time)}\n")
                f.write(f"{entry.text}\n\n")

        logger.info(f"Saved {len(entries)} subtitle entries to {output_path.name}")

    except Exception as e:
        logger.error(f"Error saving SRT file {output_path}: {e}")


def extract_plain_text(entries: List[SubtitleEntry], output_path: Path) -> None:
    """
    Extract and save plain text from subtitle entries.

    Args:
        entries: List of SubtitleEntry objects
        output_path: Output text file path
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for entry in entries:
                f.write(f"{entry.text}\n")

        logger.info(f"Extracted plain text to {output_path.name}")

    except Exception as e:
        logger.error(f"Error extracting plain text: {e}")


def validate_subtitles(entries: List[SubtitleEntry]) -> Tuple[bool, List[str]]:
    """
    Validate subtitle entries for continuity and proper formatting.

    Args:
        entries: List of SubtitleEntry objects

    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []

    if not entries:
        issues.append("No subtitle entries found")
        return False, issues

    # Check for gaps and overlaps
    for i in range(len(entries) - 1):
        current_end = entries[i].end_time
        next_start = entries[i + 1].start_time

        # Check for overlap
        if current_end > next_start:
            issues.append(f"Entry {entries[i].index} overlaps with entry {entries[i + 1].index}")

        # Check for large gaps (more than 5 seconds)
        if next_start - current_end > 5.0:
            issues.append(f"Large gap ({next_start - current_end:.2f}s) between entries {entries[i].index} and {entries[i + 1].index}")

    # Check for very long subtitles
    for entry in entries:
        duration = entry.end_time - entry.start_time
        if duration > 10.0:
            issues.append(f"Entry {entry.index} is very long ({duration:.2f}s)")

    is_valid = len(issues) == 0

    if is_valid:
        logger.info("Subtitle validation passed")
    else:
        logger.warning(f"Subtitle validation found {len(issues)} issues")

    return is_valid, issues


def transcribe_with_whisper(audio_path: Path, model: str = "medium") -> List[SubtitleEntry]:
    """
    Transcribe audio using Whisper.

    Args:
        audio_path: Path to audio file
        model: Whisper model size (tiny, base, small, medium, large)

    Returns:
        List of SubtitleEntry objects
    """
    try:
        import whisper

        logger.info(f"Loading Whisper model: {model}")
        model_instance = whisper.load_model(model)

        logger.info(f"Transcribing audio: {audio_path.name}")
        result = model_instance.transcribe(str(audio_path), task="transcribe")

        # Convert to subtitle entries
        entries = []
        for i, segment in enumerate(result['segments'], 1):
            text = segment['text'].strip()
            if text:
                entries.append(SubtitleEntry(
                    index=i,
                    start_time=segment['start'],
                    end_time=segment['end'],
                    text=text
                ))

        logger.info(f"Whisper transcription complete: {len(entries)} segments")

        # Save SRT file
        output_path = SUBS_RAW_DIR / f"{audio_path.stem}.srt"
        save_srt(entries, output_path)

        return entries

    except ImportError:
        logger.error("Whisper not installed. Run: pip install openai-whisper")
        return []
    except Exception as e:
        logger.error(f"Error transcribing with Whisper: {e}")
        logger.error(f"  Audio file: {audio_path}")
        logger.error(f"  Hint: Ensure audio file is valid and model '{model}' is downloaded")
        return []


if __name__ == "__main__":
    # Test subtitle parsing
    import sys

    if len(sys.argv) > 1:
        subtitle_file = Path(sys.argv[1])
        if subtitle_file.suffix == '.srt':
            entries = parse_srt(subtitle_file)
        elif subtitle_file.suffix == '.vtt':
            entries = parse_vtt(subtitle_file)
        else:
            print("Unsupported subtitle format")
            sys.exit(1)

        print(f"\nParsed {len(entries)} subtitle entries")
        for entry in entries[:5]:
            print(f"  {entry}")

        is_valid, issues = validate_subtitles(entries)
        print(f"\nValidation: {'PASSED' if is_valid else 'FAILED'}")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("Usage: python subtitle.py <subtitle_file>")
