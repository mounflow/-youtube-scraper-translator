#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于完整句子的字幕优化器
核心思想：每次显示一句完整的话（一句英文+一句中文）
不再切分破碎的字幕片段
"""

import re
import time
from pathlib import Path
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from deep_translator import GoogleTranslator
from utils import setup_logger

logger = setup_logger("sentence_optimizer")

# 并发翻译配置
MAX_CONCURRENT_TRANSLATIONS = 10  # 最大并发数
TRANSLATION_BATCH_SIZE = 20  # 每批处理数量

# 专有名词修正表
TERM_CORRECTIONS = {
    "Clog code": "Claude Code",
    "clog code": "Claude Code",
    "claude code": "Claude Code",
    "Claude code": "Claude Code",
    "cloud code": "Claude Code",
    "Cloud code": "Claude Code",
    "Cursor": "Cursor IDE",
    "cursor": "Cursor IDE",
    "Windsurf": "Windsurf IDE",
    "MCP": "MCP",
    "Agent OS": "Agent OS",
    "Agent os": "Agent OS",
}

class SubtitleEntry:
    def __init__(self, index: int, start_ms: int, end_ms: int, text: str):
        self.index = index
        self.start_ms = start_ms
        self.end_ms = end_ms
        self.text = text.strip()

    @property
    def duration(self) -> int:
        return self.end_ms - self.start_ms

    def __repr__(self):
        return f"[{self.index}] {self.start_ms}ms-{self.end_ms}ms: {self.text[:50]}..."


def parse_srt_file(srt_path: str) -> List[SubtitleEntry]:
    """解析SRT文件"""
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    entries = []
    blocks = content.strip().split('\n\n')

    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            try:
                index = int(lines[0].strip())

                # 解析时间戳
                time_line = lines[1].strip()
                start_str, end_str = time_line.split(' --> ')

                start_ms = parse_timestamp_ms(start_str)
                end_ms = parse_timestamp_ms(end_str)

                # 提取文本（可能有中文和英文多行）
                text_lines = lines[2:]
                text = ' '.join(line.strip() for line in text_lines)

                entries.append(SubtitleEntry(index, start_ms, end_ms, text))

            except Exception as e:
                logger.warning(f"跳过无效字幕块: {e}")
                continue

    return entries


def parse_timestamp_ms(ts: str) -> int:
    """将 SRT 时间戳转换为毫秒
    例如: 00:00:01,234 -> 1234
    """
    ts = ts.replace(',', '.')
    parts = ts.split(':')
    h = int(parts[0])
    m = int(parts[1])
    s_parts = parts[2].split('.')
    s = int(s_parts[0])
    ms = int(s_parts[1]) if len(s_parts) > 1 else 0
    return h * 3600000 + m * 60000 + s * 1000 + ms


def ms_to_srt_timestamp(ms: int) -> str:
    """将毫秒转换为 SRT 时间戳"""
    h = ms // 3600000
    ms %= 3600000
    m = ms // 60000
    ms %= 60000
    s = ms // 1000
    ms %= 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def is_sentence_end(text: str) -> bool:
    """判断是否是句子结尾"""
    text = text.strip()
    end_markers = ('.', '!', '?', '。', '！', '？', '...', '…')
    return any(text.endswith(marker) for marker in end_markers)


def merge_subtitles_by_sentence(entries: List[SubtitleEntry]) -> List[Tuple[int, int, str]]:
    """将破碎的字幕合并为完整句子

    返回: [(start_ms, end_ms, merged_text), ...]
    """
    if not entries:
        return []

    merged = []
    current_group = [entries[0]]
    current_text = entries[0].text

    for i in range(1, len(entries)):
        entry = entries[i]

        # 如果当前文本已经以句号结尾，或者是新的句子开始
        if is_sentence_end(current_text) or current_text.endswith('"'):
            # 保存当前组
            start_ms = current_group[0].start_ms
            end_ms = current_group[-1].end_ms
            merged_text = ' '.join(e.text for e in current_group)
            merged.append((start_ms, end_ms, merged_text))

            # 开始新组
            current_group = [entry]
            current_text = entry.text
        else:
            # 继续累积
            current_group.append(entry)
            current_text += ' ' + entry.text

            # 防止句子过长（最多合并5条原始字幕）
            if len(current_group) >= 5:
                start_ms = current_group[0].start_ms
                end_ms = current_group[-1].end_ms
                merged_text = ' '.join(e.text for e in current_group)
                merged.append((start_ms, end_ms, merged_text))
                current_group = []
                current_text = ""

    # 保存最后一组
    if current_group:
        start_ms = current_group[0].start_ms
        end_ms = current_group[-1].end_ms
        merged_text = ' '.join(e.text for e in current_group)
        merged.append((start_ms, end_ms, merged_text))

    logger.info(f"合并字幕: {len(entries)} 条原始 -> {len(merged)} 条完整句子")
    return merged


def split_long_sentence_by_duration(start_ms: int, end_ms: int, text: str,
                                    video_path: str = None,
                                    audio_sync: bool = False,
                                    progress_mgr=None) -> List[Tuple[int, int, str]]:
    """根据时长智能切分长句子

    新增：
    - 最大字数限制 (中英文混合) -> 避免超出屏幕边界
    - 声波能量检测 -> 寻找静音/停顿点切分

    参数:
        video_path: 视频文件路径（用于音频分析）
        audio_sync: 是否启用音频同步

    返回: [(start_ms, end_ms, text_segment), ...]
    """
    duration_sec = (end_ms - start_ms) / 1000
    
    # 统计可见字符数（粗略，这里简单当做字符长度）
    char_count = len(text)
    max_chars = 38 # 最大行长设定
    
    # 如果既短又不长，直接返回
    if duration_sec < 5 and char_count <= max_chars:
        return [(start_ms, end_ms, text)]

    # 初始化音频分析器
    audio_analyzer = None
    silence_points = []
    if audio_sync and video_path:
        try:
            from audio_analyzer import AudioAnalyzer
            audio_analyzer = AudioAnalyzer(video_path)
            # 加载特征并寻找静音点
            if audio_analyzer.load_or_extract_audio_features(progress_mgr):
                silence_points = audio_analyzer.find_silence_points(start_ms, end_ms)
                if silence_points:
                    logger.debug(f"找到 {len(silence_points)} 个潜在静音切分点")
        except Exception as e:
            logger.warning(f"[音频同步] 初始化/寻点失败: {e}")

    # 寻找切分点 (标点符号始终是首选切分点)
    segments = []
    split_chars = ('.', '!', '?', '。', '！', '？', ',', '，', ';', '；', ':', '：')
    
    parts = []
    current_part = ""

    # 首先按标点大致分段
    for char in text:
        current_part += char
        if char in split_chars:
            parts.append(current_part.strip())
            current_part = ""

    if current_part.strip():
        parts.append(current_part.strip())
        
    # 如果标点依然分不出，或者某一段还是超长，进一步按空格或者硬切分
    final_parts = []
    for part in parts:
        while len(part) > max_chars:
            # 找空格切分
            split_idx = part.rfind(' ', 0, max_chars)
            if split_idx == -1:
                split_idx = max_chars
            final_parts.append(part[:split_idx].strip())
            part = part[split_idx:].strip()
        if part:
            final_parts.append(part)

    if len(final_parts) <= 1:
        return [(start_ms, end_ms, text)]

    # 时间分配逻辑
    total_chars = sum(len(p) for p in final_parts)
    current_time = start_ms

    for i, part in enumerate(final_parts):
        if i == len(final_parts) - 1:
            part_end = end_ms
        else:
            # 默认：按字符成比例分配
            part_duration = int((end_ms - start_ms) * (len(part) / total_chars))
            expected_end = current_time + part_duration
            
            # 智能声音对齐：如果周围有静音点，贴合静音点
            best_end = expected_end
            if silence_points:
                # 寻找距离 expected_end 最近的静音点（距离要求不超过 1.5 秒）
                closest_silence = min(silence_points, key=lambda x: abs(x - expected_end))
                if abs(closest_silence - expected_end) < 1500:
                    best_end = closest_silence
                    logger.debug(f"通过声波静音点修正断句时间: {expected_end} -> {best_end}")
                    
            part_end = best_end

            # 兜底：最小时间
            if part_end - current_time < 800:
                part_end = current_time + 800
                
        segments.append((current_time, part_end, part))
        current_time = part_end

    # 修正最后一截
    if segments:
        segments[-1] = (segments[-1][0], end_ms, segments[-1][2])

    logger.debug(f"智能切分长句子 ({duration_sec:.1f}秒, {char_count}字) 为 {len(segments)} 段")
    return segments


def correct_terms(text: str) -> str:
    """修正专有名词"""
    for wrong, correct in TERM_CORRECTIONS.items():
        text = re.sub(r'\b' + re.escape(wrong) + r'\b', correct, text, flags=re.IGNORECASE)
    return text


def _translate_single(args: Tuple) -> Dict:
    """翻译单个句子（用于并发）"""
    start_ms, end_ms, english, source_lang, target_lang = args

    try:
        # 修正专有名词
        english = correct_terms(english)

        # 创建新的翻译器实例（线程安全）
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        chinese = translator.translate(english)

        # 清理翻译结果
        chinese = chinese.strip() if chinese else "[翻译失败]"

        return {
            'start': start_ms,
            'end': end_ms,
            'english': english,
            'chinese': chinese,
            'success': True
        }
    except Exception as e:
        logger.error(f"翻译失败: {english[:30]}... -> {e}")
        return {
            'start': start_ms,
            'end': end_ms,
            'english': english,
            'chinese': "[翻译失败]",
            'success': False
        }


def translate_sentences_concurrent(sentences: List[Tuple[int, int, str]],
                                   source_lang: str = 'en',
                                   target_lang: str = 'zh-CN',
                                   progress_mgr=None) -> List[Dict]:
    """并发翻译句子列表（比顺序翻译快 5-10 倍）"""

    total = len(sentences)
    logger.info(f"开始并发翻译 {total} 条句子 (并发数: {MAX_CONCURRENT_TRANSLATIONS})")

    results = []
    completed = 0

    # 创建翻译任务
    task_id = None
    if progress_mgr:
        task_id = progress_mgr.translation_task(total)

    # 使用线程池并发翻译
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_TRANSLATIONS) as executor:
        # 提交所有翻译任务
        future_to_idx = {}
        for idx, (start_ms, end_ms, english) in enumerate(sentences):
            future = executor.submit(_translate_single,
                                   (start_ms, end_ms, english, source_lang, target_lang))
            future_to_idx[future] = idx

        # 收集结果（按顺序）
        results_dict = {}
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            result = future.result()
            results_dict[idx] = result
            completed += 1

            # 更新进度
            if progress_mgr and task_id:
                progress_mgr.progress.update(
                    task_id,
                    advance=1,
                    description=f"翻译 {completed}/{total}"
                )

            # 每10条输出一次日志
            if completed % 10 == 0:
                logger.info(f"翻译进度: {completed}/{total} ({completed*100//total}%)")

        # 按原始顺序排序结果
        results = [results_dict[i] for i in range(len(sentences))]

    logger.info(f"并发翻译完成: {len(results)} 条")
    return results


def translate_sentences(sentences: List[Tuple[int, int, str]],
                        source_lang: str = 'en',
                        target_lang: str = 'zh-CN',
                        video_path: str = None,
                        audio_sync: bool = False,
                        progress_mgr=None) -> List[Dict]:
    """翻译句子列表（包含智能切分）

    参数:
        video_path: 视频文件路径（用于音频分析）
        audio_sync: 是否启用音频同步
        progress_mgr: ProgressManager 实例（可选）

    返回: [{'start': ms, 'end': ms, 'english': str, 'chinese': str}, ...]
    """
    translator = GoogleTranslator(source=source_lang, target=target_lang)

    results = []

    # 创建翻译任务
    task_id = None
    if progress_mgr:
        task_id = progress_mgr.translation_task(len(sentences))

    for i, (start_ms, end_ms, english) in enumerate(sentences):
        try:
            # 修正专有名词
            english = correct_terms(english)

            # 智能切分长句子
            split_sentences = split_long_sentence_by_duration(
                start_ms, end_ms, english, video_path, audio_sync, progress_mgr
            )

            for seg_start, seg_end, seg_english in split_sentences:
                # 翻译
                chinese = translator.translate(seg_english)

                # 清理翻译结果
                chinese = chinese.strip()

                results.append({
                    'start': seg_start,
                    'end': seg_end,
                    'english': seg_english,
                    'chinese': chinese
                })

                logger.info(f"[{len(results)}] {seg_english[:60]}... -> {chinese[:60]}...")

            # 更新 Rich 进度条
            if progress_mgr and task_id:
                progress_mgr.progress.update(
                    task_id,
                    advance=1,
                    description=f"翻译句子 {i+1}/{len(sentences)}: {english[:40]}..."
                )

            # 速率限制
            time.sleep(0.2)

        except Exception as e:
            logger.error(f"翻译失败: {e}")
            # 失败时保留英文
            results.append({
                'start': start_ms,
                'end': end_ms,
                'english': english,
                'chinese': "[翻译失败]"
            })

    return results


def fix_overlaps_gentle(subtitles: List[Dict], min_gap_ms: int = 200):
    """温和地修复重叠 - 只缩短过长的字幕，保持足够时长

    策略：
    1. 如果两条字幕重叠，缩短前一条
    2. 确保每条字幕至少有 1 秒的显示时间
    3. 如果无法缩短（时长不足），则让下一条延迟开始
    """
    if len(subtitles) <= 1:
        return

    for i in range(len(subtitles) - 1):
        current = subtitles[i]
        next_sub = subtitles[i + 1]

        current_end = current['end']
        next_start = next_sub['start']

        # 检测重叠
        if current_end > next_start - min_gap_ms:
            # 尝试缩短当前字幕
            min_duration = 1000  # 最少 1 秒
            ideal_end = next_start - min_gap_ms

            if ideal_end >= current['start'] + min_duration:
                # 可以缩短
                current['end'] = ideal_end
                logger.debug(f"缩短字幕 {i+1}: {current_end}ms -> {ideal_end}ms")
            else:
                # 不能缩短，延迟下一条
                next_sub['start'] = current_end + min_gap_ms
                logger.debug(f"延迟字幕 {i+2}: {next_start}ms -> {next_sub['start']}ms")


def save_bilingual_srt(subtitles: List[Dict], output_path: str):
    """保存双语 SRT 文件

    格式：
    1
    00:00:00,240 --> 00:00:04,560
    English text here
    中文翻译在这里
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, sub in enumerate(subtitles, 1):
            start_ts = ms_to_srt_timestamp(sub['start'])
            end_ts = ms_to_srt_timestamp(sub['end'])

            f.write(f"{i}\n")
            f.write(f"{start_ts} --> {end_ts}\n")
            f.write(f"{sub['english']}\n")
            f.write(f"{sub['chinese']}\n")
            f.write("\n")

    logger.info(f"✅ 字幕已保存: {output_path}")
    logger.info(f"   总计 {len(subtitles)} 条字幕")


def optimize_srt(input_srt: str, output_srt: str, video_path: str = None, audio_sync: bool = False, progress_mgr=None) -> bool:
    """主函数：优化 SRT 字幕

    Args:
        input_srt: 输入的原始 SRT 文件路径
        output_srt: 输出的优化后 SRT 文件路径
        video_path: 视频文件路径（用于音频分析）
        audio_sync: 是否启用音频同步
        progress_mgr: ProgressManager 实例（可选）

    Returns:
        bool: 是否成功
    """
    logger.info(f"🚀 开始优化字幕: {input_srt}")

    if audio_sync and video_path:
        logger.info("🎵 音频同步模式：已启用")

    # 1. 解析原始字幕
    entries = parse_srt_file(input_srt)
    logger.info(f"📖 读取到 {len(entries)} 条原始字幕")

    if not entries:
        logger.error("❌ 没有读取到字幕")
        return False

    # 2. 合并为完整句子
    sentences = merge_subtitles_by_sentence(entries)
    logger.info(f"📝 合并后: {len(sentences)} 条句子")

    # 3. 智能切分（逐条处理，需要音频分析）
    logger.info("✂️ 开始智能切分长句子...")
    split_tasks = []
    for i, (start_ms, end_ms, english) in enumerate(sentences):
        english = correct_terms(english)
        split_sentences = split_long_sentence_by_duration(
            start_ms, end_ms, english, video_path, audio_sync, progress_mgr
        )
        for seg_start, seg_end, seg_english in split_sentences:
            split_tasks.append((seg_start, seg_end, seg_english))

    logger.info(f"✂️ 切分完成: {len(split_tasks)} 条待翻译")

    # 4. 并发翻译
    translated = translate_sentences_concurrent(split_tasks, progress_mgr=progress_mgr)

    # 5. 修复重叠
    fix_overlaps_gentle(translated, min_gap_ms=200)

    # 6. 保存
    save_bilingual_srt(translated, output_srt)

    # 打印预览
    logger.info("\n🔍 预览前 3 条字幕:")
    for i, sub in enumerate(translated[:3], 1):
        logger.info(f"\n[{i}] {ms_to_srt_timestamp(sub['start'])} --> {ms_to_srt_timestamp(sub['end'])}")
        logger.info(f"  EN: {sub['english']}")
        logger.info(f"  ZH: {sub['chinese']}")

    return True


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("用法: python sentence_subtitle_optimizer.py <input.srt> <output.srt>")
        print("\n示例:")
        print('  python sentence_subtitle_optimizer.py "subs_raw/video.en.srt" "subs_translated/video_optimized.srt"')
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    if not Path(input_file).exists():
        logger.error(f"❌ 输入文件不存在: {input_file}")
        sys.exit(1)

    try:
        success = optimize_srt(input_file, output_file)
        if success:
            logger.info("\n✅ 优化完成!")
        else:
            logger.error("\n❌ 优化失败")
            sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 发生错误: {e}", exc_info=True)
        sys.exit(1)
