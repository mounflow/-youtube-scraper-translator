# YouTube Topic Scraper & Chinese Adapter

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An automated tool to download YouTube videos by topic, extract/generate subtitles, and translate/adapt them into natural Simplified Chinese.

## Features

- Automated YouTube video search and download
- Multi-source subtitle extraction (native subtitles + Whisper ASR)
- Context-aware Chinese translation with sentence merging
- Professional bilingual subtitle burning (English + Chinese)
- Multiple subtitle styles (Obama, Box Classic, etc.)
- Batch processing with auto-confirmation

## Quick Start

### Prerequisites

- Python 3.9+
- FFmpeg (required for video processing)
- Google Chrome + [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) extension

### Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/youtube-scraper-translator.git
cd youtube-scraper-translator
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install FFmpeg:
- **Windows**: Run `install_ffmpeg.ps1` (PowerShell script)
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

4. Prepare YouTube cookies (required to avoid bot detection):
- Install [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) Chrome extension
- Visit YouTube.com
- Click extension icon → Export → Save as `cookies.txt` in project root

### Usage

#### Search and Download Videos
```bash
# Search YouTube for videos
python main.py -s "quantum computing" -c cookies.txt

# Download specific video
python main.py -u "https://www.youtube.com/watch?v=VIDEO_ID" -c cookies.txt
```

#### Process Subtitles and Burn
```bash
# Process existing video with subtitles
python main.py -v "downloads/video.mp4" -b "downloads/video.en.srt" -y

# Full pipeline (auto-confirm all prompts)
python main.py -s "Claude Code" -c cookies.txt -y
```

#### Options
```
-s, --search       Search YouTube videos by topic
-u, --url          Direct YouTube video URL
-v, --video        Path to local video file
-b, --subtitle     Path to subtitle file (.srt/.vtt)
-q, --quality      Video quality (default: 1080)
-c, --cookies-file Path to cookies.txt (REQUIRED)
-y, --yes          Skip all confirmation prompts (auto-confirm)
--style           Subtitle style (obama, box_classic, etc.)
--preview-only    Generate preview image only (no full video)
--cleanup         Clean temporary files after processing
```

## Project Structure

```
youtube-scraper-translator/
├── main.py                    # Entry point & CLI
├── search.py                  # YouTube search module
├── downloader.py              # Video download module
├── subtitle_generator.py      # Subtitle processing & burning
├── translation_optimizer.py   # Translation optimization
├── style_config.py           # Subtitle style definitions
├── requirements.txt          # Python dependencies
├── COOKIES.md                # Cookie setup guide
├── CLAUDE.md                 # Claude Code AI instructions
├── README.md                 # This file
├── downloads/                # Downloaded videos (gitignored)
├── subs_raw/                 # Raw subtitles (gitignored)
├── subs_translated/          # Translated subtitles (gitignored)
├── output/                   # Final videos (gitignored)
└── logs/                     # Operation logs (gitignored)
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Video Download | [yt-dlp](https://github.com/yt-dlp/yt-dlp) | YouTube video/audio extraction |
| ASR Fallback | [OpenAI Whisper](https://github.com/openai/whisper) | Speech-to-text transcription |
| Translation | [deep-translator](https://github.com/nidhaloff/deep-translator) | Google Translate API (free) |
| Video Processing | [FFmpeg](https://ffmpeg.org/) | Subtitle burning & format conversion |
| Subtitle Processing | [pysrt](https://github.com/byroot/pysrt) | SRT parsing & overlap fixing |

## Features in Detail

### 1. Smart Translation Optimization
- **Sentence Merging**: Combines fragmented subtitles into complete sentences
- **Context-Aware Translation**: Translates full sentences for better accuracy
- **Intelligent Segmentation**: Splits translations at punctuation marks (not mid-word)
- **Term Correction**: Fixes common terminology (e.g., "Claude code" → "Claude Code")

### 2. Advanced Subtitle Processing
- **Overlap Fix**: Iterative algorithm resolves subtitle timing conflicts (5-pass max)
- **Time-Based Distribution**: Allocates translation text based on subtitle duration
- **Multi-Format Support**: Handles .srt, .vtt, .ass formats
- **Validation**: Checks timestamp continuity and format correctness

### 3. Professional Subtitle Styles
- **obama**: Clean white text with black outline (45pt)
- **box_classic**: White text with dark background box (50pt main, 35pt English)
- Custom styles supported via `style_config.py`

### 4. Batch Processing
- Auto-confirmation mode (`-y/--yes`) for unattended operation
- Progress logging to `logs/` directory
- Error recovery with retry logic
- Temporary file cleanup

## Examples

### Example 1: Search and Process a Single Video
```bash
python main.py -s "Elon Musk interview" -c cookies.txt -y
```

Output:
```
[*] Found 3 candidates
    1. Elon Musk cries while talking about his heroes (3:05)
    2. Elon Musk: Tesla's Full Self-Driving... (12:34)
    3. Elon Musk on SpaceX, Mars, and... (8:21)
[?] Select video (1-3): 1
[*] Downloading: Elon Musk cries while talking about his heroes
[*] Processing 78 subtitle entries...
[*] Fixed 73 overlaps in 2 iterations
[*] Generated bilingual subtitles
[*] Preview: output/Elon_Musk_interview_preview.png
```

### Example 2: Process Existing Video
```bash
python main.py -v "downloads/my_video.mp4" \
               -b "downloads/my_video.en.srt" \
               --style box_classic \
               -y
```

### Example 3: Generate Preview Only
```bash
python main.py -v "downloads/test.mp4" \
               -b "downloads/test.en.srt" \
               --preview-only \
               -y
```

## Configuration

### Cookie Setup (Required)
YouTube requires cookies to avoid bot detection. Follow these steps:

1. Install [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. Visit YouTube.com and log in
3. Click the extension icon → "Export" → "Download" (NOT "Current tab")
4. Save as `cookies.txt` in project root
5. Verify: First line should start with `# Netscape HTTP Cookie File`

See [COOKIES.md](COOKIES.md) for detailed guide.

### FFmpeg Installation
- **Windows**: Run `install_ffmpeg.ps1` in PowerShell (as Administrator)
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

Verify installation:
```bash
ffmpeg -version
```

## Troubleshooting

### Issue: "HTTP Error 429: Too Many Requests"
**Cause**: YouTube rate limiting
**Solution**: Use cookies.txt and add delays between requests

### Issue: "No module named 'ffmpeg'"
**Cause**: ffmpeg-python not installed
**Solution**: `pip install ffmpeg-python`

### Issue: Subtitle overlaps in output
**Cause**: Original subtitle timing conflicts
**Solution**: Tool auto-fixes overlaps (logs show fixed count)

### Issue: Translation quality poor
**Cause**: Google Translate free API limitations
**Solution**:
- Merge more sentences (adjust `translation_optimizer.py` line 74)
- Use paid DeepL API (modify `translation_optimizer.py` line 63)

## Development

### Adding New Subtitle Styles
Edit `style_config.py`:
```python
STYLES["mystyle"] = {
    "ass_style_line": "Style: Default,Arial,40,&H00FFFFFF,...",
    "description": "My custom style"
}
```

### Adjusting Translation Logic
Edit `translation_optimizer.py`:
- Line 74: `len(group) < 4` → Merge more/less sentences
- Line 127: Adjust time-based character distribution ratio
- Line 136: Add custom punctuation marks for segmentation

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - feel free to use this project for any purpose.

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- [OpenAI Whisper](https://github.com/openai/whisper) - ASR engine
- [deep-translator](https://github.com/nidhaloff/deep-translator) - Translation API
- [FFmpeg](https://ffmpeg.org/) - Video processing

## Disclaimer

This tool is for educational purposes only. Please respect YouTube's Terms of Service and copyright laws. The author is not responsible for any misuse of this software.

---

**Made with ❤️ for the Chinese-speaking developer community**
