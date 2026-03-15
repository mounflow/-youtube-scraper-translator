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
            SpinnerColumn(spinner_name="dots"),
            TextColumn("{task.description}"),
            BarColumn(bar_width=None),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=self.console,
            expand=True
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
            f"下载中... {task_id}", total=total
        )

    def translation_task(self, total):
        """
        翻译任务进度

        参数:
            total: 字幕条目总数
        """
        return self.progress.add_task(
            f"翻译字幕... ({total}条)", total=total
        )

    def burn_task(self, total_frames):
        """
        视频烧录任务进度

        参数:
            total_frames: 总帧数
        """
        return self.progress.add_task(
            f"烧录字幕...", total=total_frames
        )

    def audio_analysis_task(self):
        """音频分析任务（不确定时长，只显示spinner）"""
        return self.progress.add_task(
            "分析音频波形...", total=None
        )

    def search_task(self, total=None):
        """
        搜索任务进度

        参数:
            total: 预期结果数量（可选）
        """
        return self.progress.add_task(
            "搜索视频...", total=total
        )

    def subtitle_optimization_task(self, total):
        """
        字幕优化任务进度

        参数:
            total: 字幕条目总数
        """
        return self.progress.add_task(
            f"优化字幕... ({total}条)", total=total
        )

    def batch_task(self, total_videos: int) -> int:
        """
        批处理任务进度条

        参数:
            total_videos: 总视频数量

        返回:
            任务ID
        """
        return self.progress.add_task(
            f"批处理视频... ({total_videos}个)", total=total_videos
        )

    def concurrent_download_task(self, video_id: str) -> int:
        """
        单个并发下载任务

        参数:
            video_id: 视频标识字符串

        返回:
            任务ID
        """
        return self.progress.add_task(
            f"下载视频 {video_id}", total=None
        )
