# AI字幕优化器 - 使用指南

## 功能特点

### 🎯 核心功能
1. **时间戳智能修复** - 使用专业算法修复重叠和间隙
2. **AI高质量翻译** - 支持Claude API / OpenAI GPT-4
3. **术语准确性** - 保持技术术语和品牌名称准确
4. **可读性优化** - 自动调整字幕时长和阅读速度
5. **质量分析** - 提供详细的字幕质量报告

### 📊 优化内容
- ✅ 修复时间戳重叠（使用智能算法，而非简单裁剪）
- ✅ AI翻译（Claude 3.5 Sonnet / GPT-4 Turbo）
- ✅ 专业术语保持准确（Claude Code, API等）
- ✅ 合理的句子切分
- ✅ 阅读速度优化（15字符/秒）
- ✅ 最小间隔保证（84ms - 2帧）

## 快速开始

### 1. 配置API密钥

创建或编辑 `.env` 文件：

```bash
# 使用Claude API（推荐）
ANTHROPIC_API_KEY=your_claude_api_key_here

# 或使用OpenAI API
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. 安装依赖

```bash
pip install anthropic python-dotenv
# 或者使用OpenAI
pip install openai python-dotenv
```

### 3. 使用方法

#### 方法1: 命令行直接使用

```bash
# 基本用法
python subtitle_ai_optimizer.py input.srt output.srt

# 带上下文信息（提高翻译准确性）
python subtitle_ai_optimizer.py "Claude Code is all you need in 2026.en.srt" "optimized.srt" "Claude Code programming tutorial"
```

#### 方法2: 集成到主流程

修改 `main.py`，添加AI优化步骤：

```python
from subtitle_ai_optimizer import AISubtitleOptimizer

# 在翻译之后，烧录之前
optimizer = AISubtitleOptimizer()
optimizer.optimize_subtitles(
    input_srt="subs_translated/video_optimized.srt",
    output_srt="subs_translated/video_ai_optimized.srt",
    video_context="Claude Code tutorial"
)
```

## 实际使用示例

### 示例1: 优化Claude Code视频字幕

```bash
python subtitle_ai_optimizer.py \
  "subs_translated/Claude Code is all you need in 2026_optimized.srt" \
  "subs_translated/Claude Code is all you need in 2026_ai_optimized.srt" \
  "Claude Code AI programming tutorial video"
```

### 示例2: 批量优化

```python
from subtitle_ai_optimizer import AISubtitleOptimizer
from pathlib import Path

optimizer = AISubtitleOptimizer()

# 批量处理所有字幕
for srt_file in Path("subs_translated").glob("*_optimized.srt"):
    output_file = srt_file.parent / f"{srt_file.stem}_ai_optimized.srt"
    print(f"Processing: {srt_file.name}")
    
    optimizer.optimize_subtitles(
        str(srt_file),
        str(output_file),
        video_context="Technical video"
    )
```

### 示例3: 质量分析

```python
from subtitle_ai_optimizer import AISubtitleOptimizer

optimizer = AISubtitleOptimizer()

# 分析字幕质量
report = optimizer.analyze_subtitle_quality("input.srt")

print(f"总条目: {report['total_entries']}")
print(f"重叠问题: {report['overlaps']}")
print(f"时长过短: {report['too_short']}")
print(f"时长过长: {report['too_long']}")
print(f"阅读速度过快: {report['fast_reading']}")
```

## API选择建议

### Claude API (推荐)
- ✅ **优点**: 翻译质量高，理解技术内容好，价格合理
- ✅ **模型**: claude-3-5-sonnet-20241022
- 💰 **价格**: $3/百万输入token，$15/百万输出token
- 🔗 **获取**: https://console.anthropic.com/

### OpenAI GPT-4 Turbo
- ✅ **优点**: 生态成熟，API稳定
- ⚠️ **缺点**: 价格较高
- 💰 **价格**: $10/百万输入token，$30/百万输出token
- 🔗 **获取**: https://platform.openai.com/

## 优化对比

### 优化前
```
1
00:00:00,240 --> 00:00:04,560
Clog code in 2026 is not what it was  
2026 年的 Clog cod

2
00:00:02,639 --> 00:00:06,560
when it launched almost a year ago. And
e 已经不再是一年前推出时的
```

**问题**:
- ❌ 时间戳重叠（0.24-2.639秒）
- ❌ 翻译错误（"Clog code"应该是"Claude Code"）
- ❌ 句子被切断

### 优化后
```
1
00:00:00,240 --> 00:00:02,555
Claude code in 2026 is not what it was
2026年的Claude Code已经不是

2
00:00:02,639 --> 00:00:06,560
when it launched almost a year ago. And
一年前刚推出时的样子了。而且
```

**改进**:
- ✅ 无重叠（0.084秒间隔）
- ✅ 专业术语准确
- ✅ 完整的句子

## 参数调整

可以在代码中调整以下参数：

```python
class AISubtitleOptimizer:
    MIN_DURATION = 0.7      # 最短字幕时长
    MAX_DURATION = 7.0      # 最长字幕时长
    IDEAL_CHARS_PER_SECOND = 15  # 理想阅读速度
    MIN_GAP = 0.084         # 最小间隔（2帧）
```

## 成本估算

### Claude API
- **字幕数量**: 422条
- **预估token**: ~50k输入 + ~30k输出
- **预估成本**: $0.15-0.60 USD

### OpenAI GPT-4
- **预估成本**: $0.50-2.00 USD

💡 **建议**: 对于专业项目，这个成本完全值得投资！

## 故障排除

### 问题1: API密钥错误
```bash
Error: API key not found
```
**解决**: 检查`.env`文件是否正确配置

### 问题2: 翻译失败降级
```bash
WARNING: AI translation failed: ...
WARNING: Falling back to simple translation
```
**解决**: 
1. 检查网络连接
2. 验证API密钥有效性
3. 检查API额度

### 问题3: 字幕数量不匹配
```bash
WARNING: Translation count mismatch: 420 vs 422
```
**解决**: 自动补齐或截断（已内置处理）

## 下一步计划

### 🚀 未来改进
1. [ ] 添加语音识别优化（使用Whisper重新生成时间戳）
2. [ ] 支持更多AI提供商（DeepL, Google Cloud Translation等）
3. [ ] 字幕断句优化（基于语义边界）
4. [ ] 多语言支持
5. [ ] Web UI界面

### 💡 建议功能
欢迎提Issue或PR！

## 许可证

MIT License
