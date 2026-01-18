#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进度可视化管理模块
使用 Rich 库提供美观的进度条和终端输出
"""

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.console import Console
from rich.logging import RichHandler
import logging


class ProgressManager:
    """统一管理项目中的所有进度显示"""

    def __init__(self):
        self.console = Console()
        self.progress = None

    def setup_logging(self):
        """配置 rich 日志处理器"""
        logging.basicConfig(
            level="INFO",
            format="%(message)s",
            handlers=[RichHandler(console=self.console, rich_tracebacks=True)]
        )

    def create_progress(self):
        """创建进度条实例"""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=self.console
        )
        return self.progress

    def download_task(self, task_id, total=100):
        """
        下载任务进度

        参数:
            task_id: 任务ID字符串
            total: 总进度（默认100）
        """
        return self.progress.add_task(
            "[cyan]下载中...", total=total, task_id=task_id
        )

    def translation_task(self, total):
        """
        翻译任务进度

        参数:
            total: 字幕条目总数
        """
        return self.progress.add_task(
            "[yellow]翻译字幕...", total=total
        )

    def burn_task(self, total_frames):
        """
        视频烧录任务进度

        参数:
            total_frames: 总帧数
        """
        return self.progress.add_task(
            "[green]烧录字幕...", total=total_frames
        )

    def audio_analysis_task(self):
        """音频分析任务（不确定时长，只显示spinner）"""
        return self.progress.add_task(
            "[blue]分析音频波形...", total=None
        )

    def search_task(self, total=None):
        """
        搜索任务进度

        参数:
            total: 预期结果数量（可选）
        """
        return self.progress.add_task(
            "[magenta]搜索视频...", total=total
        )

    def subtitle_optimization_task(self, total):
        """
        字幕优化任务进度

        参数:
            total: 字幕条目总数
        """
        return self.progress.add_task(
            "[cyan]优化字幕...", total=total
        )
