# -*- coding: utf-8 -*-
"""
字幕样式配置文件
定义不同的ASS字幕样式模板
"""

STYLES = {
    # 风格1: 奥巴马演讲图风格 (英文在上, 中文在下, 无框, 纯白强描边)
    "obama": {
        "description": "Eng Top, Chi Bottom, No Box, Thick Outline, All White",
        # 字体从45号改为75号
        "ass_style_line": "Style: Default,Microsoft YaHei,75,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,20,20,35,1",
        "order": "eng_first", # 英文在前/上
        "english_color": None, # 使用Style默认颜色(白)
        "english_fontsize": None # 使用Style默认大小
    },

    # 风格2: 经典黑底框 (中文在上, 英文在下, 黑底矩形, 英文黄色)
    "box_classic": {
        "description": "Chi Top, Eng Bottom, Black Box, Eng Yellow",
        # BorderStyle=3 (不透明背景框), BackColour=&H20000000 (87%不透明黑色)
        # 字体从50号改为75号，英文从35号改为45号
        "ass_style_line": "Style: Default,Microsoft YaHei,75,&H00FFFFFF,&H000000FF,&H00000000,&H20000000,-1,0,0,0,100,100,0,0,3,0,0,2,20,20,35,1",
        "order": "chi_first", # 中文在前/上
        "english_color": "&H00FFFF&", # 黄色
        "english_fontsize": 45  # 从35改为45
    }
}

ASS_HEADER_TEMPLATE = """[Script Info]
Title: Bilingual Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{style_line}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
