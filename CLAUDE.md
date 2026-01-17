# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YouTube Topic Scraper & Chinese Adapter - An automated tool to download YouTube videos by topic, extract/generate subtitles using Whisper ASR, translate to Chinese with AI-powered optimization, and burn bilingual subtitles into videos. Supports Chinese dubbing via Edge-TTS.

## Technology Stack

- **Python 3.9+**
- **yt-dlp**: Video search, download, and subtitle extraction
- **ffmpeg**: Video processing, subtitle burning, and audio mixing
- **openai-whisper**: ASR fallback when no native subtitles exist
- **deep-translator**: Free Google Translate API (default translation)
- **zhipuai (GLM-4)**: AI-powered subtitle optimization with global context awareness
- **edge-tts**: Chinese text-to-speech dubbing generation
- **pydub**: Audio processing for dubbing

## Architecture

### Core Pipeline Flow

```
Search → Download → Subtitle Extraction → Translation Optimization → ASS Generation → Subtitle Burning → (Optional) Dubbing
```

**Key Processing Stages:**

1. **Search** (`search.py`): YouTube video search with filters (duration, upload date, cookies support)
2. **Download** (`download.py`): Video download + native subtitle extraction, fallback to audio-only for Whisper
3. **Subtitle Processing** (`subtitle.py`):
   - Parse SRT/VTT formats
   - Whisper transcription (medium model default)
   - Validation and overlap fixing
4. **Translation** - Two modes:
   - **Standard** (`translate.py`): Line-by-line Google Translate
   - **Optimized** (`translation_optimizer.py`): Sentence merging + context-aware translation
   - **AI-Powered** (`subtitle_optimizer_glm.py`): GLM-4 global context re-segmentation
5. **Subtitle Styling** (`subtitle_generator.py`, `style_config.py`): Generate ASS with professional styles
6. **Burning** (`burn.py`): FFmpeg subtitle burning with resolution-based font sizing
7. **Dubbing** (`dubbing.py`): Edge-TTS Chinese audio generation + mixing

### Module Dependencies

- `config.py`: Centralized configuration (FFmpeg paths, directories, env variables via `.env`)
- `utils.py`: Logging setup, timestamp formatting helpers
- `main.py`: CLI entry point orchestrating all modules

### Important Design Patterns

**Translation Optimization Strategy:**
- Default mode (`--no-optimize` flag NOT set): Uses `translation_optimizer.py` which merges fragmented subtitle lines into complete sentences before translation
- AI mode: Uses `subtitle_optimizer_glm.py` with GLM-4 API for global context re-segmentation and translation
- Fallback: If AI fails, degrades to standard line-by-line translation

**Subtitle Format Flow:**
```
Raw SRT/VTT → Parsed entries → Translation (standard/optimized/AI) → Bilingual SRT → Styled ASS → Burned Video
```

**Font Sizing Logic:**
- `burn.py:calculate_font_size()`: Base calculation from video resolution
- `burn.py:calculate_ass_font_size()`: ASS-specific font sizing
- `subtitle_generator.py`: Applies custom font sizes when generating ASS

## Common Commands

### Running the Application

```bash
# Search YouTube videos
python main.py -s "query topic" -c cookies.txt

# Download and process (full pipeline)
python main.py -u "https://youtube.com/watch?v=VIDEO_ID" -c cookies.txt -y

# Process existing video with custom style
python main.py -v "downloads/video.mp4" -b "subs/video.en.srt" --style premium -y

# Generate Chinese dubbing
python main.py -u "URL" -c cookies.txt --dub --voice zh-CN-YunxiNeural -y

# Disable AI optimization (use standard translation)
python main.py -u "URL" --no-optimize -y
```

### Testing Individual Modules

```bash
# Test translation optimizer standalone
python translation_optimizer.py

# Test GLM AI optimizer
python subtitle_optimizer_glm.py input.srt output.srt "video context"

# Test dubbing standalone
python dubbing.py input.srt video.mp4 output_dubbed.mp4

# Test ASS generation
python subtitle_generator.py

# Check configuration
python config.py
```

### Dependency Management

```bash
# Install dependencies
pip install -r requirements.txt

# Install FFmpeg (Windows)
powershell -ExecutionPolicy Bypass -File scripts/install_ffmpeg.ps1
```

## Configuration

### Environment Variables (`.env`)

```bash
# FFmpeg Configuration
FFMPEG_PATH=D:\path\to\ffmpeg.exe  # Optional, auto-detected if unset

# Translation Configuration
TARGET_LANGUAGE=zh-CN
SOURCE_LANGUAGE=en

# AI Translation (Optional - for GLM optimizer)
GLM_API_KEY=your_glm_api_key_here  # Required for subtitle_optimizer_glm.py
```

### Subtitle Styles (`style_config.py`)

Three built-in styles:
- **obama**: English top, Chinese bottom, white text, thick outline (default)
- **box_classic**: Chinese top, English bottom (yellow), black background box
- **premium**: Chinese top (large 85px), English bottom (small 60px), professional look

To add new styles, edit `style_config.py` STYLES dictionary with ASS format parameters.

## Directory Structure

All scripts operate using these default paths (configured in `config.py`):
- `./downloads/` - Original videos (.mp4) and audio
- `./subs_raw/` - Raw subtitle files (.vtt, .srt)
- `./subs_translated/` - Translated Chinese subtitle files and styled ASS
- `./output/` - Final subtitle-burned videos
- `./logs/` - Operation logs
- `./ui/` - Web UI parts (part0, part1, part2 subdirectories)
- `./web/` - Web interface files (index.html, app.js)

## Key Implementation Details

### Cookie Handling for YouTube

YouTube bot detection requires cookies. Two methods:
1. **Browser extraction**: `--cookies chrome` (requires browser cookie export)
2. **File-based**: `-c cookies.txt` (Netscape format)

Use [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) Chrome extension to export.

### Subtitle Overlap Fixing Algorithm

Located in `subtitle_generator.py:fix_overlaps()`
- Iterative algorithm (up to 5 passes)
- Enforces minimum 100ms gap between subtitles
- Preserves minimum 500ms duration per entry

### Translation Optimization

**Standard Optimizer** (`translation_optimizer.py`):
1. Groups consecutive subtitle lines up to sentence endings (max 4 lines)
2. Merges into full sentences
3. Translates with Google Translate
4. Distributes translation back based on time-duration ratios
5. Intelligently segments at punctuation marks

**AI Optimizer** (`subtitle_optimizer_glm.py`):
1. Sends batches of 50 subtitles to GLM-4 API
2. AI performs re-segmentation and translation in one pass
3. Returns JSON with optimized timestamps and translations
4. Requires `GLM_API_KEY` in `.env`

### Dubbing Workflow

`dubbing.py: DubbingEngine` class:
1. Parses SRT, extracts Chinese text (Unicode range `\u4e00-\u9fff`)
2. Generates TTS audio segments via edge-tts
3. Speeds up audio if duration exceeds subtitle slot (max 1.3x)
4. Mixes with video using FFmpeg (adjusts background audio volume to 0.0 by default)

## Troubleshooting Common Issues

### "fragment not found" download error
- Cause: Network issues or invalid cookies
- Fix: Remove `-c cookies.txt` parameter, retry without cookies

### FFmpeg not found
- `config.py` auto-detects common Windows paths
- Set `FFMPEG_PATH` in `.env` if auto-detection fails

### Whisper transcription fails
- Ensure sufficient RAM (medium model requires ~4GB)
- Falls back gracefully if audio extraction fails

### GLM API translation fails
- Check `GLM_API_KEY` in `.env`
- Falls back to standard translation on error
- Check API quota at https://open.bigmodel.cn/

### Dubbing audio sync issues
- Check pydub FFmpeg configuration in `dubbing.py:36-57`
- Adjust speed_factor or background_volume in DubbingEngine constructor

## Development Guidelines

### Adding New Features

**New subtitle style:**
1. Add entry to `STYLES` dict in `style_config.py`
2. Test with `python subtitle_generator.py`

**New translation provider:**
1. Create optimizer module following `subtitle_optimizer_glm.py` pattern
2. Add CLI flag in `main.py`
3. Wire up in `process_video()` function (main.py:239)

**New TTS voice:**
1. List available: `edge-tts --list-voices | grep zh`
2. Pass via `--voice` parameter (e.g., `zh-CN-XiaoxiaoNeural`)

### Code Entry Points

- **Main orchestration**: `main.py:process_video()` (line 239) - core pipeline
- **CLI arguments**: `main.py:main()` (line 49) - argument parsing
- **Search logic**: `search.py:search_videos()` - YouTube search with filters
- **Download logic**: `download.py:download_video()` - yt-dlp wrapper
- **Burning logic**: `burn.py:burn_subtitles()` - FFmpeg subtitle burning

## Git Workflow

This project uses Git for version control. Before committing:
1. Ensure `.gitignore` excludes: `*.mp4`, `*.srt`, `*.ass`, `*.log`, `cookies.txt`, `.env`
2. Never commit: Cookies, API keys, downloaded videos, generated subtitles
3. Safe to commit: Source code (.py), config files, documentation (.md)

See `docs/CLAUDE.md` for detailed GitHub deployment guide.
