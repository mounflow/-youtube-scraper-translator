# 🎯 GLM API 字幕优化完整指南

## ✅ GLM API 的优势

智谱AI的GLM（通用语言模型）非常适合字幕翻译：

| 特性 | GLM | Gemini | Claude |
|------|-----|--------|--------|
| **中文翻译质量** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **技术术语** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **访问速度（国内）** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **免费额度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **价格** | 很便宜 | 免费受限 | 中等 |
| **推荐度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## 🚀 快速开始

### 步骤1: 获取GLM API密钥

1. 访问：https://open.bigmodel.cn/
2. 注册/登录账号
3. 进入"API管理" → "创建API Key"
4. 复制API密钥

### 步骤2: 配置API密钥

在 `.env` 文件中添加（或直接编辑最后一行）：

```bash
GLM_API_KEY=your_glm_api_key_here
```

### 步骤3: 安装依赖

```bash
pip install zhipuai
```

### 步骤4: 运行优化

```bash
python subtitle_optimizer_glm.py \
  "subs_translated/Claude Code is all you need in 2026_optimized.srt" \
  "subs_translated/Claude Code_glm_fixed.srt" \
  "Claude Code AI编程助手教程"
```

### 步骤5: 使用Premium样式烧录

```bash
python main.py \
  -v "downloads/Claude Code is all you need in 2026.webm" \
  -b "subs_translated/Claude Code_glm_fixed.srt" \
  --style premium \
  --yes
```

## ✨ GLM优化器特点

### 1. 智能句子合并 ✅
**解决的问题**：一句话被分成多个字幕

**示例**：
```
优化前：
  条目1: "Claude Code in 2026 is not what it was"
  条目2: "when it launched almost a year ago."

优化后：
  条目1: "Claude Code in 2026 is not what it was when it launched almost a year ago."
```

### 2. 专业术语准确 ✅
**保持英文**：
- Claude Code → Claude Code
- Cursor → Cursor  
- API → API
- AI → AI
- MCP → MCP

**翻译示例**：
```
英文: "Claude Code in 2026 is not what it was"
GLM: "2026年的Claude Code已经不是当初的样子了"
```

### 3. 时间戳智能修复 ✅
- 自动修复重叠
- 添加最小间隔（84ms）
- 确保最小/最大时长

### 4. 中文表达自然 ✅
GLM专门针对中文优化，翻译更符合中文表达习惯

## 📊 预期效果

### 内容质量（GLM优化后）

```srt
1
00:00:00,240 --> 00:00:06,476
Claude Code in 2026 is not what it was when it launched almost a year ago.
2026年的Claude Code已经不是一年前刚推出时的样子了。

2
00:00:06,560 --> 00:00:09,835
And if you're just coming into AI assisted development right now
如果你现在刚刚开始接触AI辅助开发

3
00:00:09,919 --> 00:00:12,236
I get why it might feel overwhelming with all the noise of the past year.
我理解为什么过去一年的各种信息会让人不知所措。
```

**改进点**：
✅ "cloud code" → "Claude Code"（不再误译为"云代码"）
✅ "cursor" → "Cursor"（不再误译为"Curso r"）  
✅ 一句话不再被切分
✅ 翻译自然流畅

### 格式质量（Premium样式）

```
[视频显示效果]
2026年的Claude Code已经不是一年前刚推出时的样子了。  [85px 白色 粗黑边]
Claude Code in 2026 is not what it was when it launched...  [60px 白色 粗黑边]
```

**特点**：
✅ 中文大号在上
✅ 英文小号在下
✅ 白色文字 + 黑色描边
✅ 极小行间距

## 🔧 高级配置

### 调整批次大小

如果遇到长字幕或API限制，可以调整batch_size：

```python
# 在 subtitle_optimizer_glm.py 的 optimize_subtitles 函数
optimizer.optimize_subtitles(
    input_file,
    output_file,
    context,
    batch_size=5  # 改小一点，每次翻译少一些
)
```

### 选择不同的GLM模型

```python
# 在 GLMSubtitleOptimizer.__init__ 中
self.model = "glm-4-flash"     # 快速版，推荐
# 或
self.model = "glm-4"           # 标准版，更准确但慢一点
```

## 💰 成本估算

### GLM免费额度
- 新用户：赠送大量token
- 持续免费额度：每月刷新

### 付费价格（如果超出免费额度）
- glm-4-flash: 约¥0.001/千tokens
- 422条字幕约需：50k tokens
- **预计成本**: ¥0.05-0.20（几乎免费）

对比：
- Claude: ¥1-4/视频
- OpenAI: ¥4-15/视频
- **GLM: ¥0.05-0.20/视频** ⭐

## 📝 完整工作流程示例

```bash
# 1. 配置GLM API密钥（只需一次）
echo "GLM_API_KEY=your_api_key_here" >> .env

# 2. 安装依赖（只需一次）
pip install zhipuai

# 3. GLM优化翻译（解决内容问题）
python subtitle_optimizer_glm.py \
  "subs_translated/Claude Code is all you need in 2026_optimized.srt" \
  "subs_translated/Claude Code_glm.srt" \
  "Claude Code AI编程助手教程"

# 4. 使用Premium样式烧录（解决格式问题）
python main.py \
  -v "downloads/Claude Code is all you need in 2026.webm" \
  -b "subs_translated/Claude Code_glm.srt" \
  --style premium \
  --yes

# 5. 查看结果
# output/Claude Code is all you need in 2026_subtitled.mp4
```

## ❓ 故障排除

### 问题1: zhipuai包未安装
```bash
pip install zhipuai
```

### 问题2: API密钥错误
检查.env文件中的GLM_API_KEY是否正确

### 问题3: 翻译失败
- 检查网络连接
- 查看API配额是否用完
- 访问 https://open.bigmodel.cn/usercenter/apikeys 查看使用情况

### 问题4: 翻译质量不满意
- 修改video_context，提供更详细的视频描述
- 调整temperature参数（在代码中）

## 🎯 总结

**GLM API** 是目前最适合你的方案：

✅ **内容问题** - GLM智能翻译，术语准确
✅ **格式问题** - Premium样式，专业影视级
✅ **句子切分** - 智能合并，一句话完整显示
✅ **国内优势** - 访问快，免费额度足
✅ **性价比** - 几乎免费

立即开始使用吧！🚀
