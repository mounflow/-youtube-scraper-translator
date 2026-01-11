# YouTube Scraper & Translator 使用指南

这份指南基于实际测试和代码分析，为您提供详细的操作步骤和技巧。

## 1. 快速入门

### 环境准备
确保您已经安装了依赖库和 FFmpeg。
```bash
pip install -r requirements.txt
# Windows 用户请确保 FFmpeg 已安装并配置在环境变量中，或者直接放在项目目录下
```

### 核心命令速查

| 功能 | 命令示例 | 说明 |
|------|----------|------|
| **搜索视频** | `python main.py -s "Claude Code" --no-filter` | 搜索相关话题视频 |
| **下载并处理** | `python main.py -u "URL" -y` | 自动下载、翻译、压制 |
| **仅下载** | `python main.py -u "URL" --no-burn` | 下载视频和字幕，不烧录 |
| **处理本地文件** | `python main.py -v "video.mp4" -b "sub.srt"` | 重新处理已下载的文件 |

## 2. 详细功能说明

### A. 搜索视频 (Search)
搜索 YouTube 上的视频。建议使用 `--no-filter` 来查看更多结果，因为默认过滤器条件较严格（时长限制）。

```bash
# 基础搜索
python main.py -s "Python 教程"

# 显示更多结果（推荐）
python main.py -s "Claude Code" --no-filter

# 配合 cookies 搜索（如果你遇到 429 Too Many Requests）
python main.py -s "Claude Code" -c cookies.txt
```

### B. 下载与翻译 (Download & Translate)
工具会自动完成：下载 -> 提取字幕/Whisper 识别 -> **智能翻译** -> 字幕烧录。

**推荐命令：**
```bash
python main.py -u "https://youtu.be/..." -y
```
*   `-y`: 自动确认所有提示（适合无人值守）。
*   注意：如果遇到 `fragment not found` 错误，请尝试不加载 cookies (不加 `-c` 参数) 再次尝试。

### C. 字幕样式与翻译优化
项目包含智能翻译优化功能：
*   **句意合并**: 自动将破碎的字幕行合并为完整句子进行翻译。
*   **样式选择**:
    *   `obama` (默认): 经典黑边白字。
    *   `box_classic`: 底部黑框白字。
    *   `--style box_classic`: 指定样式。

```bash
# 指定样式下载
python main.py -u "URL" --style box_classic -y
```

## 3. 常见问题排查 (Troubleshooting)

### Q1: 下载失败 "fragment not found"
**原因**: 通常是网络波动或 cookie 失效导致的。
**解决**: 
1. 尝试去除 `-c cookies.txt` 参数，使用游客模式下载。
2. 确保网络环境可以稳定访问 YouTube。

### Q2: 报错 "Unknown format code 'd' for object of type 'float'"
**原因**: 代码中的已知 Bug（已修复）。
**解决**: 确保 `search.py` 中的 `format_duration` 函数已包含 `seconds = int(seconds)` 的修正。

### Q3: 找不到 FFmpeg
**解决**: 
1. 确认已安装 FFmpeg。
2. 在 `config.py` 或环境变量中检查 `FFMPEG_PATH` 设置。

### Q4: 翻译很慢
**原因**: 使用了免费的翻译 API 或 Whisper 本地模型较大。
**解决**: 耐心等待。Whisper 第一次运行时会下载模型。

## 4. 高级技巧

*   **本地重处理**: 如果你已经下载了视频，想换个字幕样式，不需要重新下载：
    ```bash
    python main.py -v "downloads/video.mp4" -b "downloads/video.en.srt" --style box_classic
    ```
*   **仅生成预览**: 快速查看字幕效果：
    ```bash
    python main.py -v "video.mp4" -b "sub.srt" --preview-only
    ```
