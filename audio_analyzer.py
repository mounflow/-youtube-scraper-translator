#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频波形分析模块 - 优化版
基于 FFmpeg 批量提取音频能量特征，检测语音活动边界
性能优化：一次性提取整个视频的音频特征，避免重复调用 FFmpeg
"""

import re
import json
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from utils import setup_logger

logger = setup_logger("audio_analyzer")


class AudioAnalyzer:
    """音频分析器 - 使用 FFmpeg 批量提取音频特征并检测语音活动"""

    def __init__(self, video_path: str):
        """
        初始化音频分析器

        参数:
            video_path: 视频文件路径
        """
        self.video_path = Path(video_path)
        self.cache_dir = self.video_path.parent / ".audio_cache"
        self.cache_file = self.cache_dir / f"{self.video_path.stem}_audio_features.json"

        # 确保缓存目录存在
        self.cache_dir.mkdir(exist_ok=True)

        # 批量音频特征缓存
        self.audio_features: Optional[Dict] = None
        self.video_duration_ms: int = 0

    def load_or_extract_audio_features(self) -> bool:
        """
        加载或批量提取音频特征

        返回:
            bool: 是否成功
        """
        # 检查缓存
        if self._load_from_cache():
            logger.info("从缓存加载音频特征")
            return True

        # 批量提取音频特征
        logger.info("批量提取音频特征（这可能需要30-60秒）...")
        self.audio_features = self._extract_full_audio_features()

        if self.audio_features:
            # 保存到缓存
            self._save_to_cache()
            logger.info(f"音频特征提取完成：{len(self.audio_features['frames'])} 帧")
            return True

        return False

    def _load_from_cache(self) -> bool:
        """
        从缓存加载音频特征

        返回:
            bool: 是否成功加载
        """
        if not self.cache_file.exists():
            return False

        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 验证缓存完整性
            if 'frames' in data and 'video_duration_ms' in data:
                self.audio_features = data
                self.video_duration_ms = data['video_duration_ms']
                logger.debug(f"从缓存加载了 {len(data['frames'])} 帧音频特征")
                return True

        except Exception as e:
            logger.warning(f"缓存加载失败: {e}")

        return False

    def _save_to_cache(self):
        """保存音频特征到缓存"""
        if not self.audio_features:
            return

        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.audio_features, f, ensure_ascii=False, indent=2)
            logger.debug(f"音频特征已缓存到: {self.cache_file}")
        except Exception as e:
            logger.warning(f"缓存保存失败: {e}")

    def _extract_full_audio_features(self) -> Optional[Dict]:
        """
        批量提取整个视频的音频特征

        返回:
            Dict: 包含 'frames' (RMS值列表) 和 'video_duration_ms' (视频时长)
        """
        # 使用 FFmpeg 提取音频的 RMS 级别
        cmd = [
            "ffmpeg",
            "-i", str(self.video_path),
            "-filter:a", "astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level",
            "-f", "null",
            "-"
        ]

        logger.debug("执行批量音频提取...")

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=120  # 2分钟超时
            )

            # 解析所有 RMS 值和时间戳
            frames_data = self._parse_full_rms_output(result.stderr)

            if not frames_data:
                logger.warning("未能提取到音频特征")
                return None

            # 计算视频时长（基于最后一帧）
            self.video_duration_ms = int(frames_data[-1]['time_ms'] + 23)  # +23ms (一帧时长)

            return {
                'frames': frames_data,
                'video_duration_ms': self.video_duration_ms
            }

        except subprocess.TimeoutExpired:
            logger.error("音频提取超时（120秒）")
            return None
        except Exception as e:
            logger.error(f"音频提取失败: {e}")
            return None

    def _parse_full_rms_output(self, ffmpeg_output: str) -> List[Dict]:
        """
        解析 FFmpeg 输出，提取所有帧的 RMS 能级值和时间戳

        参数:
            ffmpeg_output: FFmpeg stderr 输出

        返回:
            List[Dict]: [{'time_ms': 时间戳(ms), 'rms_db': RMS值}, ...]
        """
        frames = []

        # 正则表达式匹配帧时间和 RMS 行
        time_pattern = re.compile(r'pts_time:(\d+\.?\d*)')
        rms_pattern = re.compile(r'lavfi\.astats\.Overall\.RMS_level=([-]?\d+\.?\d*)')

        current_time_ms = None

        for line in ffmpeg_output.split('\n'):
            # 检查是否包含时间戳
            time_match = time_pattern.search(line)
            if time_match:
                current_time_ms = int(float(time_match.group(1)) * 1000)
                continue

            # 检查是否包含 RMS 值
            rms_match = rms_pattern.search(line)
            if rms_match and current_time_ms is not None:
                try:
                    rms_db = float(rms_match.group(1))
                    # 只保留有效范围内的值（-60dB 到 0dB）
                    if -60 <= rms_db <= 0:
                        frames.append({
                            'time_ms': current_time_ms,
                            'rms_db': rms_db
                        })
                except ValueError:
                    continue

        logger.debug(f"解析了 {len(frames)} 帧音频数据")
        return frames

    def _get_frames_in_range(self, start_ms: int, end_ms: int) -> List[float]:
        """
        从预加载的音频特征中获取指定时间范围内的帧

        参数:
            start_ms: 开始时间（毫秒）
            end_ms: 结束时间（毫秒）

        返回:
            List[float]: RMS 能级列表（dB）
        """
        if not self.audio_features:
            return []

        frames = self.audio_features['frames']

        # 二分查找找到起始帧
        start_idx = 0
        end_idx = len(frames)

        for i, frame in enumerate(frames):
            if frame['time_ms'] >= start_ms:
                start_idx = i
                break

        for i in range(len(frames) - 1, -1, -1):
            if frames[i]['time_ms'] <= end_ms:
                end_idx = i + 1
                break

        # 提取范围内的 RMS 值
        rms_values = [frame['rms_db'] for frame in frames[start_idx:end_idx]]

        logger.debug(f"从缓存提取 {start_ms}ms -> {end_ms}ms: {len(rms_values)} 帧")

        return rms_values

    def extract_audio_features(self, start_ms: int, end_ms: int) -> List[float]:
        """
        提取指定时间段的音频 RMS 能量值（使用缓存）

        参数:
            start_ms: 开始时间（毫秒）
            end_ms: 结束时间（毫秒）

        返回:
            RMS 能级列表（dB）
        """
        # 如果音频特征未加载，先加载
        if self.audio_features is None:
            if not self.load_or_extract_audio_features():
                return []

        # 从缓存中获取范围内的帧
        return self._get_frames_in_range(start_ms, end_ms)

    def _parse_rms_output(self, ffmpeg_output: str) -> List[float]:
        """
        解析 FFmpeg 输出，提取 RMS 能级值（保留用于兼容性）

        参数:
            ffmpeg_output: FFmpeg stderr 输出

        返回:
            RMS 能级列表（dB）
        """
        rms_values = []

        # 正则表达式匹配 RMS 行
        # 格式: lavfi.astats.Overall.RMS_level=-12.5
        pattern = re.compile(r'lavfi\.astats\.Overall\.RMS_level=([-]?\d+\.?\d*)')

        for line in ffmpeg_output.split('\n'):
            match = pattern.search(line)
            if match:
                try:
                    rms_db = float(match.group(1))
                    # 只保留有效范围内的值（-60dB 到 0dB）
                    if -60 <= rms_db <= 0:
                        rms_values.append(rms_db)
                except ValueError:
                    continue

        return rms_values

    def detect_speech_boundaries(
        self,
        start_ms: int,
        end_ms: int,
        threshold_ratio: float = 0.1
    ) -> Tuple[int, int]:
        """
        检测指定时间段内的语音活动边界

        参数:
            start_ms: 字幕开始时间（毫秒）
            end_ms: 字幕结束时间（毫秒）
            threshold_ratio: 噪声底比例（默认0.1，即最小10%能量值）

        返回:
            (speech_start_ms, speech_end_ms) 实际语音起止时间
        """
        # 提取音频特征（使用缓存）
        rms_values = self.extract_audio_features(start_ms, end_ms)

        if not rms_values:
            # 如果没有音频数据，返回原始时间
            logger.debug(f"无音频数据，使用原始时间: {start_ms}ms -> {end_ms}ms")
            return start_ms, end_ms

        # 检测语音活动
        speech_start_idx, speech_end_idx = self._detect_speech_activity(
            rms_values, threshold_ratio
        )

        # 将索引转换为时间偏移
        duration_ms = end_ms - start_ms
        total_frames = len(rms_values)

        if total_frames == 0:
            return start_ms, end_ms

        # 计算实际语音时间
        speech_start_offset = int((speech_start_idx / total_frames) * duration_ms)
        speech_end_offset = int((speech_end_idx / total_frames) * duration_ms)

        speech_start_ms = start_ms + speech_start_offset
        speech_end_ms = start_ms + speech_end_offset

        logger.debug(f"检测到语音边界: {speech_start_ms}ms -> {speech_end_ms}ms")

        return speech_start_ms, speech_end_ms

    def _detect_speech_activity(
        self,
        rms_values: List[float],
        threshold_ratio: float
    ) -> Tuple[int, int]:
        """
        检测音频帧中的语音活动

        参数:
            rms_values: RMS 能级列表（dB）
            threshold_ratio: 噪声底比例

        返回:
            (start_idx, end_idx) 语音活动的起止帧索引
        """
        if not rms_values:
            return 0, 0

        # 计算噪声底（最小10%能量值）
        noise_floor = sorted(rms_values)[:max(1, int(len(rms_values) * threshold_ratio))][-1]

        # 检测语音阈值（噪声底 + 10dB）
        threshold = noise_floor + 10

        # 找到第一个超过阈值的点（语音开始）
        speech_start_idx = 0
        for i, rms in enumerate(rms_values):
            if rms > threshold:
                speech_start_idx = i
                break

        # 找到最后一个超过阈值的点（语音结束）
        speech_end_idx = len(rms_values) - 1
        for i in range(len(rms_values) - 1, -1, -1):
            if rms_values[i] > threshold:
                speech_end_idx = i
                break

        # 确保至少有一些帧
        if speech_end_idx <= speech_start_idx:
            speech_end_idx = min(speech_start_idx + 10, len(rms_values) - 1)

        return speech_start_idx, speech_end_idx

    def adjust_subtitle_timing(
        self,
        subtitle_start: int,
        subtitle_end: int,
        max_delay_start: int = 500,
        max_advance_end: int = 300,
        min_duration: int = 1000
    ) -> Tuple[int, int]:
        """
        根据语音活动调整字幕时间戳

        策略:
        - 延迟开始：匹配语音开始（最多延迟max_delay_start毫秒）
        - 提前结束：匹配语音结束（最多提前max_advance_end毫秒）
        - 保持最小显示时长：至少min_duration毫秒

        参数:
            subtitle_start: 原始字幕开始时间（毫秒）
            subtitle_end: 原始字幕结束时间（毫秒）
            max_delay_start: 最大延迟开始时间（默认500ms）
            max_advance_end: 最大提前结束时间（默认300ms）
            min_duration: 最小显示时长（默认1000ms）

        返回:
            (new_start, new_end) 调整后的时间戳
        """
        # 检测语音边界
        speech_start, speech_end = self.detect_speech_boundaries(
            subtitle_start, subtitle_end
        )

        # 计算新的开始时间（延迟到语音开始）
        new_start = min(subtitle_start + max_delay_start, speech_start)

        # 计算新的结束时间（提前到语音结束）
        new_end = max(subtitle_end - max_advance_end, speech_end)

        # 确保最小时长
        if new_end - new_start < min_duration:
            new_end = new_start + min_duration

        # 确保不超出原始范围太多
        if new_start < subtitle_start:
            new_start = subtitle_start
        if new_end > subtitle_end:
            new_end = subtitle_end

        logger.debug(
            f"调整时间戳: {subtitle_start}ms->{new_start}ms, "
            f"{subtitle_end}ms->{new_end}ms"
        )

        return new_start, new_end


def test_audio_analyzer(video_path: str):
    """
    测试音频分析器

    参数:
        video_path: 视频文件路径
    """
    print(f"\n测试音频分析器: {video_path}")
    print("=" * 80)

    analyzer = AudioAnalyzer(video_path)

    # 批量加载音频特征
    print("\n[步骤1] 批量加载音频特征")
    if analyzer.load_or_extract_audio_features():
        print(f"成功加载 {len(analyzer.audio_features['frames'])} 帧音频数据")
        print(f"视频时长: {analyzer.video_duration_ms / 1000:.1f} 秒")

        # 测试1: 提取0-5秒的音频特征（从缓存）
        print("\n[测试1] 提取0-5秒音频特征（从缓存）")
        rms_values = analyzer.extract_audio_features(0, 5000)
        print(f"提取到 {len(rms_values)} 个音频帧")
        if rms_values:
            print(f"RMS 范围: {min(rms_values):.1f}dB 到 {max(rms_values):.1f}dB")
            print(f"平均 RMS: {sum(rms_values)/len(rms_values):.1f}dB")

        # 测试2: 检测语音边界
        print("\n[测试2] 检测语音边界 (0-5秒)")
        speech_start, speech_end = analyzer.detect_speech_boundaries(0, 5000)
        print(f"语音开始: {speech_start}ms")
        print(f"语音结束: {speech_end}ms")
        print(f"实际语音时长: {speech_end - speech_start}ms")

        # 测试3: 调整字幕时间
        print("\n[测试3] 调整字幕时间 (0-5000ms)")
        new_start, new_end = analyzer.adjust_subtitle_timing(0, 5000)
        print(f"原始时间: 0ms -> 5000ms")
        print(f"调整后: {new_start}ms -> {new_end}ms")
        print(f"时长变化: {5000}ms -> {new_end - new_start}ms")
    else:
        print("音频特征加载失败")

    print("\n" + "=" * 80)
    print("测试完成！")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        test_audio_analyzer(sys.argv[1])
    else:
        print("用法: python audio_analyzer.py <video_path>")
