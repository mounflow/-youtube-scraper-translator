# -*- coding: utf-8 -*-
"""
翻译优化器模块
负责提升字幕翻译质量：合并长句 -> 上下文翻译 -> 智能切分
"""
import sys
import time
from deep_translator import GoogleTranslator

# 设置UTF-8编码
# (已移除模块级副作用，仅在 main.py 控制)

# 专有名词修正表
TERM_CORRECTIONS = {
    "Windsurf": "Windsurf IDE",
    "cursor": "Cursor IDE",
    "Cursor": "Cursor IDE",
    "claude code": "Claude Code",
    "Claude code": "Claude Code"
}

def parse_srt(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    entries = []
    blocks = content.strip().split('\n\n')
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            # 尝试解析文本行
            text_lines = lines[2:]
            chinese = ""
            english = ""
            
            if len(text_lines) == 1:
                # 只有一行，默认为英文原文
                english = text_lines[0]
            elif len(text_lines) >= 2:
                # 两行，假设第一行中文第二行英文（或反之，需统一）
                # 这里假设标准的srt格式：上面中文下面英文，或者单行英文
                # 为了优化器工作，我们主要关心英文
                # 简单起见，假设最后一行是英文
                english = text_lines[-1]
                chinese = "\n".join(text_lines[:-1])
                
            entries.append({
                'index': lines[0],
                'time': lines[1],
                'chinese': chinese,
                'english': english
            })
    return entries

def is_sentence_end(text):
    return text.strip().endswith(('.', '?', '!', '。', '？', '！'))

def optimize_srt_translation(input_srt, output_srt, source_lang='en', target_lang='zh-CN'):
    """主函数：优化SRT翻译"""
    
    entries = parse_srt(input_srt)
    translator = GoogleTranslator(source=source_lang, target=target_lang)
    
    print(f"[*] 开始优化翻译 ({len(entries)} 条)...")
    
    i = 0
    while i < len(entries):
        group = [entries[i]]
        current_text = entries[i]['english']
        
        # 1. 向后合并直至句尾或达到最大合并数
        j = i + 1
        while j < len(entries) and not is_sentence_end(current_text) and len(group) < 4:
            next_entry = entries[j]
            next_text = next_entry['english']
            
            group.append(next_entry)
            current_text += " " + next_text
            j += 1
            
            if is_sentence_end(next_text):
                break
        
        # 2. 预处理文本
        full_english = current_text.replace('\n', ' ').strip()
        for term, replacement in TERM_CORRECTIONS.items():
            full_english = full_english.replace(term, replacement)
            
        # 3. 翻译
        try:
            # print(f"  合并原文: {full_english}")
            translated_text = translator.translate(full_english)
            
            # 4. 回填 - 改进为智能断句
            total_len = len(translated_text)
            assigned_len = 0

            for k, entry in enumerate(group):
                if k == len(group) - 1:
                    entry['chinese'] = translated_text[assigned_len:].strip()
                else:
                    # 使用时间占比而非字符比例（更合理）
                    try:
                        # 解析时间戳获取持续时间
                        time_parts = entry['time'].split(' --> ')
                        start_time = time_parts[0].replace(',', '.')
                        end_time = time_parts[1].replace(',', '.')

                        # 简单计算：将 HH:MM:SS.mmm 转换为秒
                        def time_to_seconds(t):
                            parts = t.split(':')
                            h = int(parts[0])
                            m = int(parts[1])
                            s = float(parts[2])
                            return h * 3600 + m * 60 + s

                        entry_duration = time_to_seconds(end_time) - time_to_seconds(start_time)

                        # 计算总时长
                        total_duration = sum([
                            time_to_seconds(e['time'].split(' --> ')[1].replace(',', '.')) -
                            time_to_seconds(e['time'].split(' --> ')[0].replace(',', '.'))
                            for e in group
                        ])

                        ratio = entry_duration / total_duration if total_duration > 0 else 1.0 / len(group)
                        char_count = int(total_len * ratio)
                        char_count = max(1, char_count)

                        # 智能断句：在标点符号处切分，避免破坏语义
                        if assigned_len + char_count < len(translated_text):
                            # 寻找最近的断句点（标点符号）
                            for i in range(min(15, char_count), 0, -1):
                                char = translated_text[assigned_len + char_count - i]
                                if char in '，。！？、；：':
                                    char_count -= i - 1
                                    break

                        sub_text = translated_text[assigned_len:assigned_len + char_count]
                        entry['chinese'] = sub_text.strip()
                        assigned_len += char_count

                    except Exception as e:
                        # 降级到字符比例算法
                        ratio = len(entry['english']) / len(full_english)
                        char_count = int(total_len * ratio)
                        char_count = max(1, char_count) if entry['english'] else 0

                        sub_text = translated_text[assigned_len:assigned_len + char_count]
                        entry['chinese'] = sub_text
                        assigned_len += char_count
                    
        except Exception as e:
            print(f"WARNING: 翻译段落失败 (Index {entries[i]['index']}): {e}")
            print(f"  原文: {full_english[:100]}{'...' if len(full_english) > 100 else ''}")
            print(f"  将保留原文")
        
        i = j # 跳过已处理的组
        time.sleep(0.2) # 速率限制保护

    # 5. 保存结果
    with open(output_srt, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(f"{entry['index']}\n")
            f.write(f"{entry['time']}\n")
            f.write(f"{entry['english']}\n")  # 英文在前（原文）
            f.write(f"{entry['chinese']}\n")  # 中文在后（翻译）
            f.write("\n")
            
    print(f"[SUCCESS] 字幕优化完成: {output_srt}")
    return True

if __name__ == "__main__":
    # 测试代码
    optimize_srt_translation(
        "subs_translated/How I use Claude Code (+ my best tips)_clean.srt",
        "subs_translated/test_optimized.srt"
    )
