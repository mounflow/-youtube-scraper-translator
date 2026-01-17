#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI字幕优化器 - GLM 全局上下文版本 (Global Context Version)

特点：
1. 全局上下文感知：不再逐行翻译，而是将大段字幕发送给AI。
2. 智能重组 (Re-segmentation)：AI负责将破碎的字幕行合并为通顺的句子。
3. 结构化JSON输出：确保时间戳和内容的精确对应。
4. 专业术语保留：强制保留技术术语。
"""

import os
import re
import json
import math
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv

# 尝试导入，如果没有安装则稍后报错
try:
    from zhipuai import ZhipuAI
except ImportError:
    ZhipuAI = None

from utils import setup_logger, format_timestamp, parse_timestamp as parse_timestamp_str
from subtitle import parse_srt, SubtitleEntry as BaseSubtitleEntry

logger = setup_logger("subtitle_optimizer_glm_global")

@dataclass
class OptimizedEntry:
    """优化后的字幕条目"""
    start_time: float
    end_time: float
    original_text: str
    translated_text: str

class GLMGlobalOptimizer:
    """使用智谱AI GLM的全局上下文优化器"""
    
    def __init__(self, api_key: Optional[str] = None):
        load_dotenv()
        
        if not api_key:
            api_key = os.getenv("GLM_API_KEY")
        
        if not api_key:
            raise ValueError("未找到 GLM_API_KEY，请在 .env 中配置或直接传入")
        
        if ZhipuAI is None:
            raise ImportError("请先安装 zhipuai 包: pip install zhipuai")
            
        self.client = ZhipuAI(api_key=api_key)
        self.model = "glm-4-flash" # 使用 Flash 模型，速度快且便宜，适合长文本
        logger.info("✅ GLM AI 客户端初始化完成")

    def _format_batch_for_prompt(self, entries: List[BaseSubtitleEntry]) -> str:
        """将字幕条目列表格式化为 Prompt 文本"""
        lines = []
        for e in entries:
            start_str = format_timestamp(e.start_time)
            end_str = format_timestamp(e.end_time)
            # 格式: [ID] start -> end: text
            lines.append(f"[{e.index}] {start_str} --> {end_str}: {e.text}")
        return "\n".join(lines)

    def _call_glm_api(self, prompt: str) -> str:
        """调用 GLM API 获取响应"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1, # 低温度以保证格式稳定
                top_p=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"GLM API 调用失败: {e}")
            raise

    def _parse_json_response(self, response_text: str) -> List[Dict[str, Any]]:
        """解析 API 返回的 JSON 字符串"""
        # 清理 Markdown 代码块标记 ```json ... ```
        clean_text = re.sub(r'```json\s*', '', response_text)
        clean_text = re.sub(r'```\s*$', '', clean_text)
        clean_text = clean_text.strip()
        
        try:
            data = json.loads(clean_text)
            if not isinstance(data, list):
                raise ValueError("API 返回的不是 JSON 列表")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败. 原始响应:\n{response_text}")
            raise ValueError(f"无法解析 JSON: {e}")

    def optimize_batch(self, entries: List[BaseSubtitleEntry], context_summary: str = "") -> List[OptimizedEntry]:
        """优化一批字幕"""
        if not entries:
            return []

        formatted_input = self._format_batch_for_prompt(entries)
        
        prompt = f"""
你是一位专业的视频字幕优化专家。你的任务是重组和翻译字幕。

【任务说明】
1. **重组句子 (Re-segmentation)**：
   - 原始字幕通常将一句话切断。请根据英语语法和上下文，将破碎的片段合并成完整的句子。
   - 不要遗漏任何信息，也不要重复。
2. **翻译**：
   - 将重组后的句子翻译成流畅、自然的简体中文。
   - **严禁翻译技术术语**：必须保留 "Claude Code", "Cursor", "MCP", "AI", "API", "Python", "Agent" 等英文原词。
3. **保留时间戳**：
   - 对于每个新合成的句子，计算其开始和结束时间。
   - `start` 必须是该句第一段原文的开始时间。
   - `end` 必须是该句最后一段原文的结束时间。
4. **输出格式**：
   - 只返回一个纯 JSON 数组，不要包含任何解释性文字。
   - 格式示例：
     [
       {{
         "start": "00:00:00,240",
         "end": "00:00:04,000",
         "text": "Claude Code in 2026 is not what it was when it launched.",
         "translation": "2026年的Claude Code已非当初发布时的模样。"
       }}
     ]

【视频主题背景】：{context_summary}

【原始字幕数据】：
{formatted_input}

请开始处理，返回 JSON 数据：
"""
        logger.info(f"📤 发送批次请求 (包含 {len(entries)} 条原始字幕)...")
        response_text = self._call_glm_api(prompt)
        
        # 解析结果
        try:
            json_data = self._parse_json_response(response_text)
            optimized_results = []
            
            for item in json_data:
                # 转换回对象
                opt_entry = OptimizedEntry(
                    start_time=parse_timestamp_str(item['start']),
                    end_time=parse_timestamp_str(item['end']),
                    original_text=item['text'],
                    translated_text=item['translation']
                )
                optimized_results.append(opt_entry)
            
            logger.info(f"✅ 批次处理成功，生成 {len(optimized_results)} 条优化字幕")
            return optimized_results
            
        except Exception as e:
            logger.error(f"❌ 批次处理出错: {e}")
            # 出错降级策略：至少返回原文，或者这里可以直接抛出让上层重试
            # 为简单起见，这里返回空列表，由上层处理
            return []

    def optimize_full_file(self, input_path: str, output_path: str, context: str = "", batch_size: int = 50):
        """主入口：优化整个文件"""
        logger.info(f"🚀 开始全局上下文优化: {input_path}")
        
        # 1. 读取原始字幕
        raw_entries = parse_srt(Path(input_path))
        logger.info(f"📖 读取到 {len(raw_entries)} 条原始字幕")
        
        # 2. 分批处理
        # 虽然是"全局"，但受限于 Token 窗口，我们按大块切分
        # 50条字幕通常约 1-3 分钟，足以保持局部上下文连贯
        all_optimized = []
        
        total_batches = math.ceil(len(raw_entries) / batch_size)
        
        for i in range(0, len(raw_entries), batch_size):
            batch_entries = raw_entries[i : i + batch_size]
            batch_idx = (i // batch_size) + 1
            
            logger.info(f"📦 处理批次 {batch_idx}/{total_batches} ({len(batch_entries)} 条)...")
            
            results = self.optimize_batch(batch_entries, context)
            
            if not results:
                logger.warning(f"⚠️ 批次 {batch_idx} 处理失败或无结果，尝试降级处理...")
                # 降级：直接把原始的塞进去，避免整段丢失
                for e in batch_entries:
                    all_optimized.append(OptimizedEntry(
                        start_time=e.start_time,
                        end_time=e.end_time,
                        original_text=e.text,
                        translated_text="[AI优化失败，未翻译]" # 标记一下
                    ))
            else:
                all_optimized.extend(results)
                
                # 打印预览
                if results:
                    first = results[0]
                    logger.info(f"   🔎 预览: [{format_timestamp(first.start_time)}] {first.original_text} -> {first.translated_text}")

        # 3. 保存结果
        self._save_srt(all_optimized, output_path)
        logger.info(f"💾 优化完成，已保存至: {output_path}")
        return True

    def _save_srt(self, entries: List[OptimizedEntry], path: str):
        """保存为双语 SRT 格式"""
        with open(path, 'w', encoding='utf-8') as f:
            for i, entry in enumerate(entries):
                f.write(f"{i+1}\n")
                start = format_timestamp(entry.start_time)
                end = format_timestamp(entry.end_time)
                f.write(f"{start} --> {end}\n")
                
                # 双语格式：英文在上，中文在下（符合 Premium 样式要求）
                # Premium 样式会自动把中文放第一行(如果配置了 chi_first)，或者手动在此处控制
                # 按照之前的观察，Premium 样式是读取 SRT 的前两行
                # 所以我们这里写入：
                # Line 1: 英文
                # Line 2: 中文
                # 这样 subtitle_generator.py 可以正常解析
                
                f.write(f"{entry.original_text}\n")
                f.write(f"{entry.translated_text}\n\n")

if __name__ == "__main__":
    import sys
    
    # 简单的命令行入口
    try:
        if len(sys.argv) < 3:
            print("用法: python subtitle_optimizer_glm.py <input_srt> <output_srt> [context]")
            print("\n示例: python subtitle_optimizer_glm.py input.srt output.srt 'Python教程'")
            sys.exit(1)
            
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        ctx = sys.argv[3] if len(sys.argv) > 3 else "通用视频"
        
        optimizer = GLMGlobalOptimizer()
        optimizer.optimize_full_file(input_file, output_file, ctx)
        
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
