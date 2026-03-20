"""
视频音频提取模块

使用 ffmpeg 从视频中提取音频轨道，用于 STT 转写
"""
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Any

from .logging_config import get_logger

logger = get_logger("audio_extractor")


class FFmpegNotAvailableError(Exception):
    """ffmpeg 未安装或不可用"""
    pass


class AudioExtractionError(Exception):
    """音频提取失败"""
    pass


class AudioExtractor:
    """音频提取器，使用 ffmpeg 从视频中提取音频"""

    def __init__(self, ffmpeg_path: Optional[str] = None):
        """
        初始化音频提取器

        Args:
            ffmpeg_path: ffmpeg 可执行文件路径，None 则自动检测
        """
        self._ffmpeg_path = ffmpeg_path
        self._available: Optional[bool] = None

    @property
    def ffmpeg_path(self) -> str:
        """获取 ffmpeg 路径"""
        if self._ffmpeg_path:
            return self._ffmpeg_path

        # 自动检测
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg:
            self._ffmpeg_path = ffmpeg
            return ffmpeg

        raise FFmpegNotAvailableError("ffmpeg 未安装，请先安装 ffmpeg")

    def check_available(self) -> bool:
        """
        检查 ffmpeg 是否可用

        Returns:
            bool: ffmpeg 是否可用
        """
        if self._available is not None:
            return self._available

        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                timeout=5
            )
            self._available = result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError, FFmpegNotAvailableError):
            self._available = False

        return self._available

    def get_video_info(self, video_path: Path) -> Dict[str, Any]:
        """
        获取视频信息

        Args:
            video_path: 视频文件路径

        Returns:
            dict: 包含 duration(秒), format, has_audio 等信息
        """
        if not self.check_available():
            raise FFmpegNotAvailableError("ffmpeg 未安装")

        cmd = [
            self.ffmpeg_path,
            "-i", str(video_path),
            "-hide_banner",
            "-f", "null",
            "-"
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        # ffmpeg 把信息输出到 stderr
        info_str = result.stderr

        info = {
            "duration": 0.0,
            "format": "",
            "has_audio": False,
        }

        # 解析时长
        for line in info_str.split("\n"):
            if "Duration:" in line:
                # 格式: Duration: 00:01:23.45, ...
                try:
                    duration_str = line.split("Duration:")[1].split(",")[0].strip()
                    h, m, s = duration_str.split(":")
                    info["duration"] = float(h) * 3600 + float(m) * 60 + float(s)
                except (IndexError, ValueError):
                    pass

            if "Audio:" in line:
                info["has_audio"] = True

            if "Input #0," in line:
                # 格式: Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'video.mp4'
                try:
                    info["format"] = line.split(",")[1].strip()
                except IndexError:
                    pass

        return info

    def extract_audio(
        self,
        video_path: Path,
        output_path: Optional[Path] = None,
        audio_format: str = "wav",
        sample_rate: int = 16000
    ) -> Path:
        """
        从视频中提取音频

        Args:
            video_path: 视频文件路径
            output_path: 输出音频路径，None 则在视频同目录生成
            audio_format: 输出音频格式 (wav, mp3)
            sample_rate: 采样率，16000 适合语音识别

        Returns:
            Path: 提取的音频文件路径

        Raises:
            AudioExtractionError: 提取失败
            FFmpegNotAvailableError: ffmpeg 不可用
        """
        if not self.check_available():
            raise FFmpegNotAvailableError("ffmpeg 未安装")

        if not video_path.exists():
            raise AudioExtractionError(f"视频文件不存在: {video_path}")

        # 检查视频是否有音轨
        info = self.get_video_info(video_path)
        if not info["has_audio"]:
            raise AudioExtractionError("视频没有音轨")

        # 确定输出路径
        if output_path is None:
            output_path = video_path.with_suffix(f".{audio_format}")

        # 构建 ffmpeg 命令
        cmd = [
            self.ffmpeg_path,
            "-i", str(video_path),
            "-vn",  # 不包含视频
            "-acodec", "pcm_s16le" if audio_format == "wav" else "libmp3lame",
            "-ar", str(sample_rate),  # 采样率
            "-ac", "1",  # 单声道，适合语音识别
            "-y",  # 覆盖已存在的文件
            str(output_path)
        ]

        logger.info("extracting_audio", video=str(video_path), output=str(output_path))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )

            if result.returncode != 0:
                logger.error("ffmpeg_failed", stderr=result.stderr)
                raise AudioExtractionError(f"音频提取失败: {result.stderr[:500]}")

            if not output_path.exists():
                raise AudioExtractionError("音频提取失败：输出文件不存在")

            logger.info("audio_extracted", output=str(output_path), size=output_path.stat().st_size)
            return output_path

        except subprocess.TimeoutExpired:
            raise AudioExtractionError("音频提取超时")
        except Exception as e:
            if isinstance(e, AudioExtractionError):
                raise
            raise AudioExtractionError(f"音频提取失败: {str(e)}")


# 单例
_extractor: Optional[AudioExtractor] = None


def get_audio_extractor() -> AudioExtractor:
    """获取音频提取器单例"""
    global _extractor
    if _extractor is None:
        _extractor = AudioExtractor()
    return _extractor