# 故障排除指南 (Troubleshooting Guide)

## 1. YouTube 下载 403 Forbidden 错误

### 问题描述
下载 YouTube 视频时出现 `HTTP error 403 Forbidden` 错误，通常是由于：
- YouTube 的机器人检测机制
- IP 被临时限制
- 网络环境不稳定（VPN/代理）

### 解决方案

#### 方案一：使用浏览器 Cookies（推荐）✅

利用您浏览器中的 YouTube 登录状态来绕过检测：

```bash
# 使用 Chrome 浏览器的 cookies
python main.py -u "https://youtube.com/watch?v=VIDEO_ID" --cookies chrome -y

# 使用 Firefox 浏览器的 cookies
python main.py -u "https://youtube.com/watch?v=VIDEO_ID" --cookies firefox -y

# 使用 Edge 浏览器的 cookies
python main.py -u "https://youtube.com/watch?v=VIDEO_ID" --cookies edge -y
```

**支持的浏览器**：`chrome`, `firefox`, `edge`, `opera`, `brave`, `chromium`

#### 方案二：使用 Cookie 文件

如果方案一不适用，可以手动导出 cookies：

1. 安装浏览器扩展（如 "Get cookies.txt"）
2. 登录 YouTube 后导出 cookies 为 Netscape 格式
3. 保存为 `cookies.txt` 并使用：

```bash
python main.py -u "https://youtube.com/watch?v=VIDEO_ID" --cookies-file cookies.txt -y
```

#### 方案三：等待并重试

程序内置了自动重试机制（默认 3 次）。如果是临时限制，通常会在重试中恢复。

---

## 2. 文件名包含特殊字符导致找不到文件

### 问题描述
视频标题包含 `:`, `/`, `?` 等特殊字符时，下载后无法找到文件。

### 解决方案
程序已内置自动处理：
- 下载前会预获取视频标题
- 自动将特殊字符替换为 `_`（下划线）
- 强制使用安全文件名保存

**无需手动干预，程序会自动处理。**

---

## 3. ffmpeg-python 未安装警告

### 问题描述
```
WARNING: ffmpeg-python not available, using subprocess fallback
ERROR: ffmpeg-python not installed. Run: pip install ffmpeg-python
```

### 解决方案
这只是警告，程序会自动使用 subprocess 调用 FFmpeg。如需消除警告：

```bash
pip install ffmpeg-python
```

---

## 4. 字幕翻译失败

### 问题描述
部分字幕条目显示 "翻译失败，保留原文"。

### 可能原因
- 单条字幕过长（超过翻译 API 限制）
- 网络连接不稳定
- 翻译 API 临时限流

### 解决方案
这是正常的边界情况处理，失败的条目会保留英文原文，不影响整体效果。

---

## 5. 视频压制速度慢

### 影响因素
- 视频时长（24分钟视频 ≈ 2-5分钟压制）
- 视频分辨率（1080p 比 720p 慢）
- CPU 性能

### 优化建议
- 使用 `--preview-only` 先预览效果
- 确认满意后再进行完整压制

```bash
# 仅生成预览图
python main.py -u "VIDEO_URL" --style box_classic --preview-only -y

# 确认后完整压制
python main.py -u "VIDEO_URL" --style box_classic -y
```

---

## 6. 原视频自带硬编码字幕冲突

### 问题描述
某些视频（如励志演讲类）本身已有烧录在画面中的英文字幕，与我们生成的字幕重叠。

### 解决方案
目前暂无自动去除方案（硬编码字幕无法程序化移除）。建议：
1. 选择无硬编码字幕的视频源
2. 或仅生成中文字幕，英文使用原视频自带的

---

## 7. [hls] Fragment not found 错误

### 问题描述
在下载过程中，进度条突然报错 `[hls] Fragment not found: ...`。这通常发生在使用 VPN 下载 HLS 流视频时，由于网络波动导致某个分段下载失败。

### 解决方案
程序已针对此问题进行了优化：
- **强制 MP4 格式**: 绕过脆弱的 HLS 分段下载，降低对分段完整性的要求。
- **禁用 hlsnative**: 使用 `yt-dlp` 内建更稳定的下载方式。
- **增加容错**: 设置了较长的超时时间 (`600s`) 和 10MB 的分块大小。

如果依然出现此报错：
1. 请尝试切换 VPN 节点到更稳定的地区（如日本或新加坡）。
2. 尝试使用 `--cookies chrome` 参数辅助下载。

---

## 常用命令速查

```bash
# 搜索视频
python main.py -s "关键词" --cookies chrome

# 下载并处理（默认样式）
python main.py -u "VIDEO_URL" -y

# 使用 box_classic 样式
python main.py -u "VIDEO_URL" --style box_classic -y

# 仅预览不压制
python main.py -u "VIDEO_URL" --preview-only -y

# 处理本地视频
python main.py -v "downloads/video.mp4" -b "downloads/video.en.srt" --style obama -y
```

---

*最后更新: 2026-01-11*
