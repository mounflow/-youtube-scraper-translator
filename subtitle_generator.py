# -*- coding: utf-8 -*-
"""
字幕生成器模块
负责将SRT转换为带有特定样式的ASS文件
"""
import sys
import re
from style_config import STYLES, ASS_HEADER_TEMPLATE

# 设置UTF-8编码
# (已移除模块级副作用，仅在 main.py 控制)

def parse_srt_content(content):
    """解析SRT内容字符串为列表对象"""
    entries = []
    blocks = content.strip().split('\n\n')

    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 2:
            timestamp_line = lines[1].strip()

            chinese = ""
            english = ""

            # 修复：匹配新的SRT格式（英文在前，中文在后）
            if len(lines) > 2:
                english = lines[2].strip()  # 第3行 = 英文
            if len(lines) > 3:
                chinese = lines[3].strip()  # 第4行 = 中文

            t_parts = timestamp_line.split(' --> ')
            try:
                start = convert_time(t_parts[0])
                end = convert_time(t_parts[1])

                entries.append({
                    'start': start,
                    'end': end,
                    'chinese': chinese,
                    'english': english
                })
            except Exception as e:
                # print(f"Skipping invalid timestamp: {timestamp_line}")
                continue
    return entries

def convert_time(srt_time):
    """SRT时间 -> ASS时间"""
    parts = srt_time.replace(',', '.').split(':')
    h = int(parts[0])
    m = int(parts[1])
    s = parts[2]
    return f"{h}:{m}:{s[:-1]}" 

def parse_time_to_ms(ass_time):
    parts = ass_time.split(':')
    h = int(parts[0])
    m = int(parts[1])
    s_parts = parts[2].split('.')
    s = int(s_parts[0])
    cs = int(s_parts[1]) if len(s_parts) > 1 else 0
    return (h * 3600 + m * 60 + s) * 1000 + cs * 10

def ms_to_ass_time(ms):
    h = ms // 3600000
    ms %= 3600000
    m = ms // 60000
    ms %= 60000
    s = ms // 1000
    ms %= 1000
    cs = ms // 10
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def fix_overlaps(entries, min_gap_ms=100):
    """改进的时间轴重叠修复算法 - 保守方案

    Args:
        entries: 字幕条目列表
        min_gap_ms: 最小间隙（毫秒），默认100ms
    """
    # 改进的手动算法 - 保守方案
    sorted_entries = sorted(entries, key=lambda x: parse_time_to_ms(x['start']))

    # 增加迭代轮数到5轮（从3轮增加）
    max_iterations = 5
    for iteration in range(max_iterations):
        has_overlap = False
        fixed_count = 0

        for i in range(len(sorted_entries) - 1):
            current = sorted_entries[i]
            next_entry = sorted_entries[i + 1]

            curr_end_ms = parse_time_to_ms(current['end'])
            next_start_ms = parse_time_to_ms(next_entry['start'])

            # 如果当前条目的结束时间超过了下一条的开始时间（减去最小间隙）
            if curr_end_ms > next_start_ms - min_gap_ms:
                has_overlap = True
                fixed_count += 1

                # 提前结束时间，保持最小间隙
                new_end_ms = next_start_ms - min_gap_ms
                # 确保不会早于开始时间（最小500ms）
                new_end_ms = max(parse_time_to_ms(current['start']) + 500, new_end_ms)
                current['end'] = ms_to_ass_time(new_end_ms)

        # 如果这一轮没有发现重叠，提前退出
        if not has_overlap:
            print(f"[INFO] Overlap fix completed after {iteration + 1} iterations")
            break
        else:
            print(f"[INFO] Iteration {iteration + 1}: Fixed {fixed_count} overlaps")

    return sorted_entries

def generate_styled_ass(input_srt_file, output_ass_file, style_name="obama"):
    """
    主函数：生成ASS文件
    """
    if style_name not in STYLES:
        print(f"WARNING: 样式 '{style_name}' 未找到，使用默认 'obama' 样式")
        style_name = "obama"
    
    style_config = STYLES[style_name]
    
    # 1. 读取并解析SRT
    with open(input_srt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    entries = parse_srt_content(content)
    
    # 2. 修复时间重叠
    entries = fix_overlaps(entries)
    
    # 3. 生成ASS内容
    header = ASS_HEADER_TEMPLATE.format(style_line=style_config["ass_style_line"])
    
    with open(output_ass_file, 'w', encoding='utf-8') as f:
        f.write(header)
        
        for entry in entries:
            text = ""
            eng_text = entry['english']
            chi_text = entry['chinese']
            
            # 应用各语言样式
            if style_config.get("english_color"):
                 eng_text = f"{{\\c{style_config['english_color']}}}{eng_text}"
            if style_config.get("english_fontsize"):
                 eng_text = f"{{\\fs{style_config['english_fontsize']}}}{eng_text}"
            
            # 组合顺序
            if style_config["order"] == "eng_first":
                # 英文在上
                if eng_text: text += eng_text
                if eng_text and chi_text: text += r"\N"
                if chi_text: text += chi_text
            else:
                # 中文在上
                if chi_text: text += chi_text
                if eng_text and chi_text: text += r"\N"
                if eng_text: text += eng_text
            
            line = f"Dialogue: 0,{entry['start']},{entry['end']},Default,,0,0,0,,{text}\n"
            f.write(line)
            
    print(f"[SUCCESS] 生成ASS字幕 ({style_name}): {output_ass_file}")
    return True

if __name__ == "__main__":
    # 测试代码
    generate_styled_ass(
        "subs_translated/How I use Claude Code (+ my best tips)_optimized.srt",
        "subs_translated/style_test_obama.ass",
        "obama"
    )
    generate_styled_ass(
        "subs_translated/How I use Claude Code (+ my best tips)_optimized.srt",
        "subs_translated/style_test_box.ass",
        "box_classic"
    )
