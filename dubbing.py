#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chinese Dubbing Module
Uses edge-tts to generate Chinese audio tracks for videos, synchronized with subtitles.
"""

import os
import sys
import asyncio
import tempfile
import shutil
import subprocess
import re
from pathlib import Path
from typing import List, Optional

# Audio processing
try:
    import audioop
except ImportError:
    import audioop_lts as audioop
    sys.modules["audioop"] = audioop

import edge_tts
from pydub import AudioSegment

# Project imports
from utils import setup_logger, format_timestamp
from subtitle import parse_srt, SubtitleEntry

logger = setup_logger("dubbing")

# Configure pydub to use our FFMPEG
# Try to find FFMPEG path similar to burn.py logic
FFMPEG_PATH = None
_common_paths = [
    r"D:\SofewareHome\aboutT\ffmpeg\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe",
    r"D:\Tools\AboutUniversal\installffmpeg\ffmpeg-8.0.1-essentials_build\ffmpeg-8.0.1-essentials_build\bin\ffmpeg.exe",
    r"C:\ffmpeg\bin\ffmpeg.exe",
]

for path in _common_paths:
    if Path(path).exists():
        FFMPEG_PATH = path
        # Configure pydub
        AudioSegment.converter = path
        logger.info(f"Pydub using FFmpeg at: {path}")
        break

if not FFMPEG_PATH:
    # Hope it is in PATH
    if shutil.which("ffmpeg"):
        FFMPEG_PATH = "ffmpeg"
        logger.info("Pydub using FFmpeg from system PATH")
    else:
        logger.warning("FFmpeg not found! Dubbing might fail.")

class DubbingEngine:
    def __init__(self, voice: str = "zh-CN-YunxiNeural", speed_factor: float = 1.0):
        """
        Initialize the Dubbing Engine.
        :param voice: Edge-TTS voice (e.g., zh-CN-YunxiNeural, zh-CN-XiaoxiaoNeural)
        :param speed_factor: Global speed factor (default 1.0)
        """
        self.voice = voice
        self.global_speed_factor = speed_factor

    async def generate_segment_audio(self, text: str, output_file: str) -> bool:
        """Generate audio for a single text segment using Edge-TTS."""
        try:
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(output_file)
            return True
        except Exception as e:
            logger.error(f"TTS generation failed for '{text}': {e}")
            return False

    def speed_change(self, sound: AudioSegment, speed: float) -> AudioSegment:
        """
        Change audio speed without changing pitch.
        Note: Pydub doesn't have a native high-quality time stretch.
        We'll use a simple frame rate trick which technically changes pitch unless processed carefully.
        For pydub, a safe way is tricky.
        Better approach: Use ffmpeg-python or just speedup (changes pitch slightly).
        
        Actually, for speech, small pitch changes (upto 1.2x) are acceptable or 'cartoonish'.
        A better, robust way is using `pydub.effects.speedup` (requires audiosegment to be split in chunks).
        Let's try a simple frame rate manipulation for now, or use `pydub.effects.speedup`.
        """
        # pydub.effects.speedup is safer but only works for speed > 1.0
        if speed <= 1.0:
            return sound
            
        # Limit speed to avoid "chipmunk" effect too much
        safe_speed = min(speed, 1.5)
        
        # This implementation simply drops chunks, acceptable for small speedups
        return sound.speedup(playback_speed=safe_speed)

    def process_subtitle_and_dub(self, 
                                 subtitle_path: Path, 
                                 video_path: Path, 
                                 output_path: Path,
                                 background_volume: float = 0.0) -> bool:
        """
        Main workflow: Read srt -> Gen Audio -> Sync -> Mix -> Save.
        """
        logger.info(f"🎤 Starting dubbing for: {video_path.name}")
        
        # 1. Parse Subtitles
        try:
            entries = parse_srt(subtitle_path)
            logger.info(f"Loaded {len(entries)} subtitle entries.")
        except Exception as e:
            logger.error(f"Failed to parse subtitle: {e}")
            return False

        # 2. Create a temporary directory for audio segments
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            
            # Master audio track (initialized as empty)
            master_track = AudioSegment.empty()
            
            # Cursor to track current time in the master track (in ms)
            current_time_ms = 0
            
            for i, entry in enumerate(entries):
                # Use translated text if available (from global optimize we expect dual language or just Chinese? 
                # Let's assume we extract Chinese from the subtitle file)
                # The subtitle parser for optimized files returns 'merged' text which might be dual.
                # We need to extract ONLY Chinese.
                
                # Improved Logic: Filter explicitly for lines containing Chinese characters
                # Unicode range for Chinese: \u4e00-\u9fff
                lines = entry.text.strip().split('\n')
                chinese_lines = []
                for line in lines:
                    if re.search(r'[\u4e00-\u9fff]', line):
                        chinese_lines.append(line)
                
                # If Chinese lines found, join them. Otherwise fallback to last line (risky but better than nothing)
                if chinese_lines:
                     text_to_speak = " ".join(chinese_lines)
                else:
                     # Fallback: if no Chinese detected, maybe it's just punctuation or English
                     # We skip English-only lines to prevent double reading
                     logger.warning(f"No Chinese detected in entry {i}, skipping TTS.")
                     continue
                
                # Clean up text (remove empty, symbols)
                text_to_speak = text_to_speak.strip()
                if not text_to_speak:
                    continue

                segment_file = temp_dir_path / f"seg_{i}.mp3"
                
                # Generate Audio (Async call inside sync context)
                # We need to run the async function
                asyncio.run(self.generate_segment_audio(text_to_speak, str(segment_file)))
                
                if not segment_file.exists():
                    logger.warning(f"Audio segment {i} missing, skipping.")
                    continue

                # Load generated audio
                segment_audio = AudioSegment.from_mp3(str(segment_file))
                
                # Check Duration
                expected_duration_ms = (entry.end_time - entry.start_time) * 1000
                actual_duration_ms = len(segment_audio)
                
                # Calculate required start time relative to master track
                start_time_ms = entry.start_time * 1000
                
                # Add silence gap if needed (if master cursor is behind start time)
                if start_time_ms > current_time_ms:
                    silence_gap = start_time_ms - current_time_ms
                    master_track += AudioSegment.silent(duration=silence_gap)
                    current_time_ms = start_time_ms
                
                # Handle Overlap or Speedup
                # If audio is longer than the visual slot
                if actual_duration_ms > expected_duration_ms:
                    speed_ratio = actual_duration_ms / expected_duration_ms
                    if speed_ratio > 1.3:
                         # Too fast? allow some overlap or cap speed
                         speed_ratio = 1.3
                    
                    # Apply speedup
                    segment_audio = self.speed_change(segment_audio, speed_ratio)
                
                # Append to master track
                master_track += segment_audio
                current_time_ms += len(segment_audio)
                
                logger.info(f"Processed segment {i+1}/{len(entries)}: Dur={actual_duration_ms}ms -> Slot={(entry.end_time-entry.start_time)*1000}ms")

            # 3. Save the full dub track
            dub_track_path = temp_dir_path / "full_dub.mp3"
            master_track.export(str(dub_track_path), format="mp3")
            logger.info(f"Generated full dub track: {dub_track_path}")
            
            # 4. Mix with Video using FFmpeg
            # Command:
            # ffmpeg -i video.mp4 -i dub.mp3 -filter_complex 
            # "[0:a]volume=0.2[bg];[1:a]volume=1.0[fg];[bg][fg]amix=inputs=2:duration=first" 
            # -c:v copy -map 0:v -map 2:a output.mp4
            # NOTE: map indices depend on filter output.
            
            logger.info("Combining audio with video...")
            
            cmd = [
                str(FFMPEG_PATH),
                "-i", str(video_path),
                "-i", str(dub_track_path),
                "-filter_complex", f"[0:a]volume={background_volume}[bg];[1:a]volume=1.0[fg];[bg][fg]amix=inputs=2:duration=first[aout]",
                "-map", "0:v",
                "-map", "[aout]",
                "-c:v", "copy",
                "-y",  # overwrite
                str(output_path)
            ]
            
            process = subprocess.run(cmd, capture_output=True, text=True)
            if process.returncode != 0:
                logger.error(f"FFmpeg mix failed: {process.stderr}")
                return False
                
            logger.info(f"✅ Dubbed video saved to: {output_path}")
            return True

# Helper wrapper
def create_dubbed_video(subtitle_path: str, video_path: str, output_path: str, voice: str = "zh-CN-YunxiNeural"):
    engine = DubbingEngine(voice=voice)
    return engine.process_subtitle_and_dub(Path(subtitle_path), Path(video_path), Path(output_path))

if __name__ == "__main__":
    import sys
    # Usage: python dubbing.py input.srt input_video.mp4 output_video.mp4
    if len(sys.argv) < 4:
        print("Usage: python dubbing.py <srt> <video> <output> [voice]")
        sys.exit(1)
        
    srt = sys.argv[1]
    vid = sys.argv[2]
    out = sys.argv[3]
    voice = sys.argv[4] if len(sys.argv) > 4 else "zh-CN-YunxiNeural"
    
    create_dubbed_video(srt, vid, out, voice)
