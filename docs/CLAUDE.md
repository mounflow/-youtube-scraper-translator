# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
YouTube Topic Scraper & Chinese Adapter - An automated tool to download YouTube videos by topic, extract/generate subtitles, and translate/adapt them into natural Simplified Chinese.

## Technology Stack
- **Python 3.9+**
- **yt-dlp**: Video search, download, and subtitle extraction (preferred)
- **ffmpeg**: Video processing, subtitle burning, and format conversion
- **openai-whisper**: ASR fallback when no native subtitles exist
- **Edge-TTS or DeepL API** (optional): High-quality translation

## Directory Structure
All scripts should operate using these default paths:
- `./downloads/` - Original videos (.mp4) and audio
- `./subs_raw/` - Raw subtitle files (.vtt, .srt) and extracted plain text
- `./subs_translated/` - Translated Chinese subtitle files
- `./output/` - Final output (subtitle-burned videos or standalone subtitles)
- `./logs/` - Operation logs and error reports

## Implementation Commands

### /search_plan <topic>
Search YouTube for videos matching `<topic>`.
- Filters: uploaded within 30 days, duration 10-20 minutes, sorted by view count
- Output: Top 3 candidates with title, URL, and description summary

### /download_best <url>
Download video from specified URL.
- Quality: 1080p video + best available English subtitles
- Fallback: If subtitles unavailable, download audio for Whisper transcription

### /process_subs <video_filename>
Subtitle processing pipeline:
1. Extract .srt/.vtt subtitles if available
2. If no subtitles, run Whisper (medium or base model) on audio
3. Clean text: strip timestamps, keep only dialogue, save to `./subs_raw/`

### /translate_zh <source_text_file>
Translate source text to Simplified Chinese.
- Style: Colloquial, natural flow, Chinese-native expression
- Terminology: Maintain professional accuracy (e.g., "Quantum Mechanics" → "量子力学")
- Length limit: Single subtitle lines should not exceed 15-20 Chinese characters
- Output: Bilingual (EN/ZH) .srt with timestamps to `./subs_translated/`

### /burn_subs <video_file> <subtitle_file>
Burn Chinese subtitles into video using ffmpeg.
- Style: White text, black outline, bottom-center alignment
- Output: Save to `./output/`

## Development Rules

### Error Handling
- `yt-dlp` download failures: auto-retry 2x, then log error if persists

### Validation Checks
- Post-download: Verify file size > 5MB
- Post-translation: Verify .srt timestamp continuity
- Pre-burn: Capture frame at 10s for manual preview confirmation

### Code Style
- Follow PEP 8 for Python code
- All functions require docstrings

### Execution Protocol
Before executing any `> /` command, output a brief execution plan first.

---

## GitHub Deployment Guide

This section provides instructions for deploying this project to GitHub.

### Initial Setup

1. **Initialize Git Repository** (first time only):
```bash
cd D:\AI_Practice\CC\ProjectTwo
git init
```

2. **Verify .gitignore**:
The `.gitignore` file excludes:
- All video files (*.mp4, *.mkv, etc.)
- All subtitle files (*.srt, *.ass, *.vtt)
- All logs (*.log)
- Temporary files and caches
- Cookies (security sensitive)

Only source code and configuration files are tracked.

3. **Check repository status**:
```bash
git status
```

Should show:
- Untracked files: Python modules (.py), config files (.md, .txt), PowerShell scripts
- Ignored: downloads/, subs_*/, output/, logs/, cookies.txt

### Committing Changes

1. **Stage all source files**:
```bash
git add .
```

2. **Review staged files** (optional):
```bash
git status
git diff --staged
```

3. **Create commit**:
```bash
git commit -m "Initial commit: YouTube scraper with translation optimization"
```

Commit message guidelines:
- Use present tense ("Add" not "Added")
- Be concise but descriptive
- Reference issues if applicable: "Fix #123"

### Creating GitHub Repository

1. **Create repository on GitHub**:
   - Visit https://github.com/new
   - Repository name: `youtube-scraper-translator` (or your choice)
   - Description: "Automated YouTube video scraper with Chinese subtitle translation"
   - Visibility: Public or Private
   - **DO NOT** initialize with README/LICENSE/gitignore (we already have them)

2. **Link local repo to GitHub**:
```bash
git remote add origin https://github.com/YOUR_USERNAME/youtube-scraper-translator.git
```

Replace `YOUR_USERNAME` with your GitHub username.

### Pushing to GitHub

1. **Set main branch name** (if needed):
```bash
git branch -M main
```

2. **Push to GitHub**:
```bash
git push -u origin main
```

The `-u` flag sets upstream, so future pushes can use just `git push`.

### Updating Repository

After making changes to source code:

1. **Check changes**:
```bash
git status
git diff
```

2. **Stage and commit**:
```bash
git add .
git commit -m "Fix: Improved subtitle overlap detection algorithm"
```

3. **Push to GitHub**:
```bash
git push
```

### Branching Workflow (Optional)

For feature development:

1. **Create feature branch**:
```bash
git checkout -b feature/subtitle-style-config
```

2. **Make changes and commit**:
```bash
git add .
git commit -m "Add: Custom subtitle style configuration"
```

3. **Push branch to GitHub**:
```bash
git push origin feature/subtitle-style-config
```

4. **Merge to main** (via GitHub Pull Request or locally):
```bash
git checkout main
git merge feature/subtitle-style-config
git push origin main
```

### Common Git Commands

| Command | Purpose |
|---------|---------|
| `git status` | Show working tree status |
| `git log --oneline` | Show commit history |
| `git diff` | Show unstaged changes |
| `git diff --staged` | Show staged changes |
| `git restore FILE` | Discard changes to file |
| `git restore --staged FILE` | Unstage file |
| `git clean -fd` | Remove untracked files/directories |
| `git pull` | Update local repo from remote |
| `git push` | Push local commits to remote |

### GitHub Repository Checklist

Before pushing to GitHub, ensure:

- ✅ `.gitignore` properly excludes large files
- ✅ No cookies.txt or sensitive data in repo
- ✅ `README.md` is complete with usage instructions
- ✅ `requirements.txt` lists all dependencies
- ✅ Code follows PEP 8 style guidelines
- ✅ All functions have docstrings
- ✅ No hardcoded API keys or passwords

### Security Notes

**NEVER commit to GitHub:**
- ❌ `cookies.txt` (contains YouTube session tokens)
- ❌ API keys or passwords
- ❌ Personal credentials
- ❌ Large video/audio files
- ❌ Test videos with copyrighted content

**Safe to commit:**
- ✅ Source code (.py files)
- ✅ Configuration files (.json, .yaml, .txt configs)
- ✅ Documentation (.md files)
- ✅ Example/test data (small, non-sensitive)

### Collaboration

If contributing to this project:

1. **Fork the repository** on GitHub
2. **Clone your fork**:
```bash
git clone https://github.com/YOUR_USERNAME/youtube-scraper-translator.git
```

3. **Create feature branch**:
```bash
git checkout -b feature/my-feature
```

4. **Make changes and commit**:
```bash
git add .
git commit -m "Add: My new feature"
```

5. **Push to your fork**:
```bash
git push origin feature/my-feature
```

6. **Create Pull Request** on GitHub

### Release Management

When creating a new release:

1. **Update version number** in code (if applicable)
2. **Create git tag**:
```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

3. **Create GitHub Release**:
   - Visit repository → Releases → "Create a new release"
   - Choose tag (e.g., v1.0.0)
   - Add release notes describing changes

### Troubleshooting Git Issues

**Issue: "fatal: remote origin already exists"**
```bash
git remote set-url origin https://github.com/YOUR_USERNAME/REPO_NAME.git
```

**Issue: "Permission denied (publickey)"**
- Setup SSH keys: https://docs.github.com/en/authentication/connecting-to-github-with-ssh
- Or use HTTPS URL (requires GitHub personal access token for 2FA)

**Issue: Push rejected due to large files**
```bash
git reset --soft HEAD~1  # Undo last commit
git rm --cached large_file.mp4  # Remove large file from staging
git commit -m "Remove large file"
```

**Issue: .gitignore not working**
```bash
git rm -r --cached .  # Remove all files from cache
git add .             # Re-add files (respecting .gitignore)
git commit -m "Fix: Apply .gitignore rules"
```

### Best Practices

1. **Commit frequently** with small, logical changes
2. **Write clear commit messages** following conventional commits format
3. **Review changes before committing** with `git diff`
4. **Pull before pushing** to avoid merge conflicts
5. **Keep main branch stable**, use branches for development
6. **Tag releases** for version tracking
7. **Update README.md** when adding new features
8. **Keep dependencies updated** via `pip install --upgrade -r requirements.txt`

---

## Claude Code Specific Instructions

When working with this project via Claude Code:

1. **Always check .gitignore** before suggesting file creation
2. **Never commit** cookies.txt, video files, or subtitle files
3. **Test locally** before pushing to GitHub
4. **Verify dependencies** are in requirements.txt
5. **Update documentation** when adding features
6. **Use git status** to confirm what will be committed
7. **Review git diff** before committing to ensure quality