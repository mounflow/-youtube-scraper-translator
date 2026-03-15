# YouTube 视频中文化工具

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![React](https://img.shields.io/badge/React-19-blue.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)

一键下载 YouTube 视频，自动生成中英双语字幕，支持智能优化和中文配音。

## ✨ 主要功能

### 🖥️ Web 界面（新版）
- [x] React + TypeScript 现代前端界面
- [x] FastAPI 高性能后端服务
- [x] 实时任务进度监控
- [x] 搜索/添加/管理任务队列
- [x] 日志实时查看
- [x] 输出文件管理

### 🎬 视频下载与处理
- [x] 按主题搜索 YouTube 视频
- [x] 高清视频下载（最高 4K）
- [x] 多源字幕提取（原生字幕 + Whisper 语音识别）
- [x] 自动处理机器人检测（使用浏览器 Cookies）

### 🈹 智能翻译优化
- [x] AI 驱动的上下文感知翻译
- [x] 支持 Claude 3.5、GPT-4、GLM-4 等多种翻译引擎
- [x] 句子合并与智能切分
- [x] 专业术语保留（品牌名、技术名词）

### 🎵 字幕优化与同步
- [x] 音频波形分析实现精确时间同步
- [x] 自动解决字幕重叠问题
- [x] 阅读速度优化（15 字/秒）
- [x] 多种字幕样式（奥巴马风格、经典盒式等）

### 🎙️ 中文配音
- [x] Microsoft Edge TTS 文字转语音
- [x] 多种中文发音（云希、晓晓、晓墨等）
- [x] 自动音轨混合

### 🖼️ 专业输出
- [x] 双语字幕烧录（英文 + 中文）
- [x] ASS 高级字幕格式支持
- [x] 预览图生成
- [x] 批量处理模式

## 📦 安装

### 环境要求

- Python 3.9 或更高版本
- FFmpeg（视频处理必需）
- Google Chrome + Cookie 导出扩展

### 快速安装

#### 1. 克隆项目
```bash
git clone https://github.com/YOUR_USERNAME/youtube-scraper-translator.git
cd youtube-scraper-translator
```

#### 2. 安装 Python 依赖
```bash
pip install -r requirements.txt
```

#### 3. 安装 FFmpeg

**Windows:**
```powershell
# 以管理员身份运行 PowerShell
.\scripts\install_ffmpeg.ps1
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt update && sudo apt install ffmpeg
```

#### 4. 准备 YouTube Cookies

YouTube 需要登录才能避免机器人检测，需要导出浏览器 Cookies：

1. 安装 Chrome 扩展：[Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)

2. 访问 [YouTube.com](https://www.youtube.com) 并登录

3. 点击扩展图标 → 点击 "Export" → 选择 "Netscape格式" → 保存为项目根目录的 `cookies.txt`

4. 验证文件：第一行应该包含 `# Netscape HTTP Cookie File`

详细指南请参考项目文档

## 🚀 快速开始

### Web 界面（推荐）

启动 Web 界面服务：
```bash
# 方式1: 使用快捷脚本
start_web.bat

# 方式2: 手动启动
# 终端1: 启动后端
python server.py

# 终端2: 启动前端
cd frontend && npm run dev
```

然后访问：
- 前端：http://localhost:5173
- 后端API：http://localhost:3617

### 基础用法（CLI）

#### 按主题搜索并下载视频
```bash
python main.py -s "量子计算" -c cookies.txt
```

#### 下载指定视频
```bash
python main.py -u "https://www.youtube.com/watch?v=VIDEO_ID" -c cookies.txt
```

#### 自动确认模式（无需交互）
```bash
python main.py -s "Claude AI 教程" -c cookies.txt -y
```

### 高级功能

#### 启用音频波形同步
```bash
# 让字幕精确匹配语音节奏（推荐）
python main.py -s "TED 演讲" -c cookies.txt --audio-sync -y
```

#### 生成中文配音
```bash
# 添加中文语音轨
python main.py -s "科普视频" -c cookies.txt --dub --voice zh-CN-YunxiNeural -y
```

#### 使用 AI 翻译引擎
```bash
# 使用 Claude API 翻译（需要设置 CLAUDE_API_KEY）
python main.py -s "技术教程" -c cookies.txt --translation-engine claude -y

# 使用 GLM-4 翻译（需要设置 GLM_API_KEY）
python main.py -s "历史纪录片" -c cookies.txt --translation-engine glm -y
```

#### 选择字幕样式
```bash
# 奥巴马风格（白色文字+黑色描边）
python main.py -s "新闻视频" -c cookies.txt --style obama -y

# 经典盒式风格（深色背景）
python main.py -s "电影" -c cookies.txt --style box_classic -y
```

#### 只生成预览图
```bash
# 快速查看效果，不生成完整视频
python main.py -s "测试视频" -c cookies.txt --preview-only -y
```

## 📋 完整参数列表

```
必需参数:
  -c, --cookies-file    YouTube Cookies 文件路径（必需）

操作模式（三选一）:
  -s, --search          按主题搜索 YouTube 视频
  -u, --url             直接指定 YouTube 视频链接
  -v, --video           处理本地视频文件（需配合 -b 参数）

字幕相关:
  -b, --subtitle        字幕文件路径（.srt/.vtt）（配合 -v 使用）
  --whisper-model       Whisper 模型大小（base/small/medium/large，默认：base）
  --translation-engine  翻译引擎（google/claude/openai/glm，默认：google）
  --no-optimize         跳过字幕优化
  --no-translate        跳过翻译步骤

音频与同步:
  --audio-sync          启用音频波形同步（让字幕匹配实际语音节奏）
  --dub                 生成中文配音
  --voice               TTS 发音（默认：zh-CN-YunxiNeural）

输出控制:
  -q, --quality         视频质量（360/480/720/1080/2160，默认：1080）
  --style               字幕样式（obama/box_classic/premium，默认：obama）
  --preview-only        只生成预览图
  --no-burn             不烧录字幕到视频
  --cleanup             处理完成后清理临时文件

交互控制:
  -y, --yes             自动确认所有提示（批处理模式）
  --cookies-from-browser  从浏览器读取 Cookies（chrome/edge/firefox）
```

## 🎯 典型使用场景

### 场景 1：学习资料中文化

将英文教育视频翻译成带中文字幕的视频：

```bash
python main.py -s "机器学习入门" -c cookies.txt --audio-sync --style box_classic -y
```

**效果**：
- 自动下载高清视频
- 提取英文字幕
- 使用 AI 翻译成自然中文
- 字幕精确匹配语音节奏
- 深色背景方便阅读

### 场景 2：新闻视频快速处理

批量处理新闻视频，生成双语字幕：

```bash
python main.py -s "tech news" -c cookies.txt --translation-engine claude -y
```

**优势**：
- Claude 3.5 翻译质量更高
- 保持专业术语准确
- 快速生成双语版本

### 场景 3：中文配音制作

为视频添加中文语音轨：

```bash
python main.py -u "VIDEO_URL" -c cookies.txt --dub --voice zh-CN-XiaoxiaoNeural -y
```

**应用**：
- 制作无障碍版本
- 适合移动端观看
- 保留原视频背景音

### 场景 4：本地视频重新处理

已有视频和字幕，想要优化字幕效果：

```bash
python main.py -v "downloads/video.mp4" \
               -b "downloads/video.en.srt" \
               --audio-sync \
               --style premium \
               -y
```

## 📁 项目结构

```
youtube-scraper-translator/
├── main.py                          # CLI 主入口
├── server.py                        # Web API 服务器（FastAPI）
├── search.py                        # YouTube 搜索
├── download.py                      # 视频下载
├── subtitle.py                      # 字幕提取与解析
├── translate.py                     # 翻译引擎
├── translation_optimizer.py         # AI 字幕优化
├── sentence_subtitle_optimizer.py   # 句子级优化
├── subtitle_optimizer_glm.py        # GLM 专用优化器
├── subtitle_generator.py            # ASS 字幕生成
├── burn.py                          # 字幕烧录
├── dubbing.py                       # 中文配音
├── audio_analyzer.py                # 音频波形分析
├── style_config.py                  # 字幕样式定义
├── config.py                        # 配置管理
├── utils.py                         # 工具函数
├── progress_manager.py              # 进度可视化管理
├── requirements.txt                 # Python 依赖
├── .env                             # 环境变量（API 密钥等）
├── .env.example                     # 环境变量示例
├── .gitignore                       # Git 忽略规则
├── README.md                        # 本文档
├── scripts/                         # 辅助脚本
│   └── install_ffmpeg.ps1          # Windows FFmpeg 安装
├── frontend/                        # React 前端
│   ├── src/
│   │   ├── App.tsx                 # 主组件
│   │   ├── index.css               # 样式
│   │   └── main.tsx                # 入口
│   ├── package.json
│   └── vite.config.ts
├── start_web.bat                    # 快速启动 Web 界面
├── run_video.bat                    # 快捷运行脚本
├── downloads/                       # 下载的视频（gitignored）
├── subs_raw/                        # 原始字幕（gitignored）
├── subs_translated/                 # 翻译后字幕（gitignored）
├── audio_cache/                     # 音频特征缓存（gitignored）
└── output/                          # 最终输出视频（gitignored）
```

## 🔧 配置说明

### API 密钥配置（可选）

使用高级翻译引擎时需要配置 API 密钥：

创建 `.env` 文件：
```bash
# Claude API（用于 claude 翻译引擎）
CLAUDE_API_KEY=your_claude_api_key_here

# OpenAI API（用于 openai 翻译引擎）
OPENAI_API_KEY=your_openai_api_key_here

# GLM API（用于 glm 翻译引擎）
GLM_API_KEY=your_glm_api_key_here
```

### 字幕样式自定义

编辑 `style_config.py` 添加自定义样式：

```python
STYLES["mystyle"] = {
    "ass_style_line": "Style: Default,Microsoft YaHei,45,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,2,2,3,2,1,2,10,10,10,1",
    "description": "我的自定义样式 - 微软雅黑字体"
}
```

### 翻译优化参数

编辑 `sentence_subtitle_optimizer.py` 调整优化行为：

- **第 45 行**：句子合并数量（`< 4` 表示最多合并3条字幕）
- **第 208 行**：字符比例分配时间（改为使用音频同步）
- **第 50 行**：最小时长（毫秒）

## 🔍 工作原理

### 完整处理流程

```
1. [搜索/下载] YouTube 视频
   ├─ yt-dlp 下载视频文件
   ├─ 提取原生字幕（如有）
   └─ 下载视频缩略图

2. [字幕生成] 提取或生成英文字幕
   ├─ 优先使用 YouTube 原生字幕
   └─ 回退到 Whisper 语音识别

3. [句子优化] 合并碎片字幕
   ├─ 按标点符号合并短句
   ├─ 保留完整句子结构
   └─ 计算句子显示时长

4. [音频分析] 波形同步（可选）
   ├─ FFmpeg 批量提取音频能量
   ├─ 检测语音活动边界
   └─ 调整字幕时间戳匹配实际语音

5. [AI 翻译] 上下文感知翻译
   ├─ Claude/GPT/GLM 翻译完整句子
   ├─ 保留专业术语不翻译
   └─ 智能切分长翻译

6. [重叠修复] 解决时间冲突
   ├─ 5 轮迭代算法
   ├─ 等比例压缩重叠时间
   └─ 确保最小时长和阅读速度

7. [字幕生成] 创建 ASS 格式
   ├─ 应用样式配置
   ├─ 双语字幕布局
   └─ 生成 .ass 文件

8. [视频烧录] FFmpeg 合成
   ├─ 烧录字幕到视频
   ├─ 生成预览图
   └─ (可选) 添加中文配音轨

9. [清理] 自动清理临时文件
   └─ 删除中间文件和缓存
```

### 技术栈

| 组件 | 技术选型 | 用途 |
|------|---------|------|
| 视频下载 | [yt-dlp](https://github.com/yt-dlp/yt-dlp) | YouTube 视频/音频提取 |
| 语音识别 | [OpenAI Whisper](https://github.com/openai/whisper) | ASR 字幕生成 |
| 翻译引擎 | deep-translator / Claude API / OpenAI API / GLM API | 多种翻译方案 |
| AI 优化 | Claude 3.5 Sonnet / GPT-4 / GLM-4 | 上下文感知优化 |
| 视频处理 | [FFmpeg](https://ffmpeg.org/) | 字幕烧录、格式转换 |
| 文字转语音 | [Edge-TTS](https://github.com/rany2/edge-tts) | 中文配音生成 |
| 音频处理 | [pydub](https://github.com/jiaaro/pydub) | 音频分析与编辑 |
| 进度显示 | [Rich](https://github.com/Textualize/rich) | 终端美化与进度条 |
| 字幕处理 | pysrt / custom ASS 生成器 | SRT/ASS 格式处理 |

## ❓ 常见问题

### Q: 为什么需要 Cookies？
A: YouTube 有反爬虫机制，没有 Cookies 容易触发机器人检测。使用浏览器登录后的 Cookies 可以模拟正常用户行为。

### Q: 可以使用其他翻译引擎吗？
A: 支持！本工具提供四种翻译引擎：
- **Google Translate**（免费，无需配置）
- **Claude 3.5**（质量最高，需 API Key）
- **GPT-4**（质量优秀，需 API Key）
- **GLM-4**（适合中文，需 API Key）

### Q: 音频同步功能有什么用？
A: 传统字幕按时长比例分配时间，可能与实际语音不同步。音频波形分析会检测实际的语音停顿，让字幕精确匹配说话节奏，提升观看体验。

### Q: 如何提高翻译质量？
A: 建议使用 AI 翻译引擎（Claude/GPT-4/GLM），它们能理解上下文，翻译更自然。同时启用 `--audio-sync` 可以改善字幕时间匹配。

### Q: 处理速度慢怎么办？
A: 主要耗时步骤：
1. **Whisper 识别**：使用 `--whisper-model base` 加速
2. **音频分析**：首次会缓存，后续处理秒级完成
3. **AI 翻译**：使用 Google Translate 比 Claude 快

### Q: 可以批量处理多个视频吗？
A: 可以使用 `-y` 参数配合脚本：
```bash
# 批量处理
cat video_list.txt | while read url; do
    python main.py -u "$url" -c cookies.txt -y
done
```

## 📊 性能参考

| 操作 | 耗时（10分钟视频） | 备注 |
|------|------------------|------|
| 视频下载 | 1-3 分钟 | 取决于网速和视频质量 |
| Whisper 识别 | 2-5 分钟 | base 模型，GPU 更快 |
| 音频分析（首次） | 30-60 秒 | 后续从缓存秒级完成 |
| Google 翻译 | 30-60 秒 | 免费版有速率限制 |
| Claude 翻译 | 1-2 分钟 | 质量更高，API 调用 |
| 字幕烧录 | 1-2 分钟 | 取决于 CPU 性能 |
| **总计** | **5-15 分钟** | 无音频同步 |
| **总计** | **6-16 分钟** | 含音频同步（首次） |

## 🤝 贡献指南

欢迎贡献代码、报告 Bug 或提出新功能建议！

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

## 🙏 致谢

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 强大的 YouTube 下载工具
- [OpenAI Whisper](https://github.com/openai/whisper) - 优秀的语音识别模型
- [Anthropic Claude](https://www.anthropic.com/) - AI 驱动的翻译优化
- [FFmpeg](https://ffmpeg.org/) - 视频处理瑞士军刀
- [Rich](https://github.com/Textualize/rich) - 让终端输出更美观

## ⚠️ 免责声明

本工具仅供学习和个人使用。请遵守 YouTube 服务条款和版权法律。作者不对本软件的误用承担责任。

## 📮 联系方式

- 项目主页：[GitHub Repository](https://github.com/YOUR_USERNAME/youtube-scraper-translator)
- 问题反馈：[Issues](https://github.com/YOUR_USERNAME/youtube-scraper-translator/issues)

---

**Made with ❤️ for Chinese-speaking developers and learners**
