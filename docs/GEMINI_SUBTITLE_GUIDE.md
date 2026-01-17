# 🎯 Gemini API字幕优化 - 完整指南

## 📋 你的专业字幕格式分析总结

根据你提供的详细分析，新的**premium**样式实现了以下特点：

### ✅ 已实现的特性

1. **位置与布局**
   - ✅ 居中对齐（Alignment: 2）
   - ✅ 底部叠放（MarginV: 40）
   - ✅ 中文在上，英文在下（order: chi_first）
   - ✅ 极小行间距（line_spacing: 5）

2. **文字视觉设计**
   - ✅ 纯白色文字（&H00FFFFFF）
   - ✅ 黑色描边（Outline: 3, OutlineColour: &H00000000）
   - ✅ 100%不透明度
   - ✅ 无阴影（Shadow: 0）

3. **字体特性**
   - ✅ 中文：黑体（Microsoft YaHei）
   - ✅ 英文：同字体族
   - ✅ 非衬线体，现代简洁

4. **比例与对比度**
   - ✅ 中文字号：85px (1080p优化)
   - ✅ 英文字号：60px (约70%的中文字号)
   - ✅ 大小对比清晰

5. **环境适应性**
   - ✅ 黑色粗描边确保可读性
   - ✅ 适应复杂背景

## 🚀 快速开始

### 步骤1: 配置Gemini API密钥

在项目根目录的 `.env` 文件中添加：

```bash
# Gemini API (Google)
GEMINI_API_KEY=your_gemini_api_key_here
```

**获取API密钥**: https://makersuite.google.com/app/apikey

### 步骤2: 安装依赖

```bash
pip install google-generativeai python-dotenv
```

### 步骤3: 使用新样式

#### 方法1: 直接使用premium样式

```bash
# 下载并使用premium样式
python main.py \
  --url "https://www.youtube.com/watch?v=VIDEO_ID" \
  --style premium \
  --yes
```

#### 方法2: 优化已有字幕

```bash
# 1. 使用Gemini优化翻译
python subtitle_ai_optimizer_v2.py \
  "subs_translated/Claude Code is all you need in 2026_optimized.srt" \
  "subs_translated/Claude Code_gemini_optimized.srt" \
  "Claude Code AI programming tutorial"

# 2. 使用premium样式烧录
python main.py \
  -v "downloads/Claude Code is all you need in 2026.webm" \
  -b "subs_translated/Claude Code_gemini_optimized.srt" \
  --style premium \
  --yes
```

## 🎨 样式对比

### Obama样式（原有）
- 英文在上（大号）
- 中文在下（同样大小）
- 适合：英文为主的内容

### Box Classic样式
- 中文在上（大号）
- 英文在下（小号黄色）
- 黑色背景框
- 适合：需要高对比度的场景

### Premium样式（新增⭐推荐）
```
中文字幕文本（大号85px，白色）
English subtitle text (小号60px，白色)
```
- ✅ 中文在上，字号更大
- ✅ 英文在下，字号适中
- ✅ 极小行间距，视觉块状感强
- ✅ 白字黑边，专业影视级
- ✅ 完全符合你的分析要求

## 💡 完整优化工作流程

### 推荐工作流（最佳质量）

```bash
# 1. 下载视频和原始字幕
python main.py --url "VIDEO_URL" --no-burn --yes

# 2. 使用Gemini AI优化字幕翻译
python subtitle_ai_optimizer_v2.py \
  "subs_translated/video_optimized.srt" \
  "subs_translated/video_gemini.srt" \
  "video context description"

# 3. 使用premium样式烧录
python main.py \
  -v "downloads/video.webm" \
  -b "subs_translated/video_gemini.srt" \
  --style premium \
  --yes
```

### 批量处理脚本

创建 `batch_optimize.sh` (或 .bat on Windows):

```bash
#!/bin/bash

# 批量优化所有字幕
for srt in subs_translated/*_optimized.srt; do
    base=$(basename "$srt" _optimized.srt)
    echo "Processing: $base"
    
    python subtitle_ai_optimizer_v2.py \
        "$srt" \
        "subs_translated/${base}_gemini.srt" \
        "$base video"
done

echo "✅ 所有字幕优化完成！"
```

## 🔧 高级配置

### 自定义字号（基于分辨率）

对于不同分辨率，系统会自动调整字号：

| 分辨率 | 中文字号 | 英文字号 | 样式 |
|--------|---------|---------|------|
| 480p   | 40px    | 28px    | premium |
| 720p   | 60px    | 42px    | premium |
| 1080p  | 85px    | 60px    | premium |
| 4K     | 120px   | 84px    | premium |

### 手动调整样式参数

编辑 `style_config.py` 中的 premium 配置：

```python
"premium": {
    "chi_fontsize": 85,      # 中文字号
    "english_fontsize": 60,  # 英文字号
    "line_spacing": 5,       # 行间距（像素）
    # ... 其他参数
}
```

## 📊 Gemini API vs Claude vs OpenAI

| 特性 | Gemini | Claude | OpenAI |
|------|--------|--------|--------|
| **翻译质量** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **技术术语准确性** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **价格** | **免费额度** | $3-15/M tokens | $10-30/M tokens |
| **速度** | 快 | 快 | 中等 |
| **推荐度** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

**价格对比**（422条字幕）:
- **Gemini**: 免费（有免费额度）→ ¥0
- **Claude**: ~$0.15-0.60 → ¥1-4
- **OpenAI**: ~$0.50-2.00 → ¥4-15

## 🎯 针对Claude Code视频的示例

```bash
# 完整流程示例
cd /path/to/project

# 1. AI优化翻译（使用Gemini免费API）
python subtitle_ai_optimizer_v2.py \
  "subs_translated/Claude Code is all you need in 2026_optimized.srt" \
  "subs_translated/Claude Code_gemini_premium.srt" \
  "Claude Code AI coding assistant tutorial for developers"

# 2. 使用premium样式烧录
python main.py \
  -v "downloads/Claude Code is all you need in 2026.webm" \
  -b "subs_translated/Claude Code_gemini_premium.srt" \
  --style premium \
  --yes

# 3. 查看结果
ls -lh "output/Claude Code is all you need in 2026_subtitled.mp4"
```

## 📝 示例对比

### 优化前（Google Translate）
```
1
00:00:00,240 --> 00:00:04,560
Clog code in 2026 is not what it was  
2026 年的 Clog code 已经不再是一年前推出时的样子了
```

### Gemini优化后 + Premium样式
```
[显示效果]
2026年的Claude Code已经与一年前大不相同
Claude Code in 2026 is not what it was

[特点]
✅ 术语准确（Claude Code）
✅ 翻译自然流畅
✅ 中文大号在上
✅ 英文小号在下
✅ 极小行间距
✅ 白字黑边专业
```

## 🔍 故障排除

### 问题1: Gemini API配额不足
```
Error: Resource exhausted
```
**解决**: 
1. 检查API配额: https://makersuite.google.com/
2. 等待配额重置
3. 或切换到Claude/OpenAI

### 问题2: 字幕重叠仍然存在
**解决**: AI优化器已经内置智能修复算法

### 问题3: 字号显示不对
**解决**: 检查视频分辨率，系统会自动适配

## 🌟 最佳实践

1. **视频上下文**：提供准确的视频主题描述，提高翻译质量
2. **批量处理**：一次性处理多个字幕效率更高
3. **预览检查**：使用 `--preview-only` 先查看效果
4. **备份原文件**：优化前备份原始字幕

## 📚 相关文档

- **AI优化器文档**: `docs/AI_SUBTITLE_OPTIMIZER.md`
- **完整优化指南**: `docs/SUBTITLE_OPTIMIZATION_GUIDE.md`
- **样式配置**: `style_config.py`

---

**总结**: 新的premium样式完全符合你的专业分析要求，配合Gemini API可以达到影视级的字幕质量！🎬
