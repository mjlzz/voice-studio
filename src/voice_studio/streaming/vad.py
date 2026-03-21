"""
语音活动检测 (VAD)
基于 Silero VAD 实现
"""
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path


class VADDetector:
    """
    语音活动检测器

    使用 Silero VAD 模型检测音频中的语音段。
    """

    _model = None
    _utils = None

    def __init__(
        self,
        sample_rate: int = 16000,
        threshold: float = 0.5,
        min_silence_ms: int = 500,
        speech_pad_ms: int = 200,
    ):
        """
        初始化 VAD 检测器

        Args:
            sample_rate: 采样率（支持 8000 或 16000）
            threshold: 语音检测阈值 (0-1)
            min_silence_ms: 最小静音时长（毫秒）
            speech_pad_ms: 语音段前后填充（毫秒）
        """
        self._sample_rate = sample_rate
        self._threshold = threshold
        self._min_silence_ms = min_silence_ms
        self._speech_pad_ms = speech_pad_ms

        # 状态变量
        self._reset_state()

        # 加载模型
        self._load_model()

    def _load_model(self):
        """加载 Silero VAD 模型"""
        if VADDetector._model is None:
            import torch
            import torch.hub

            model_dir = Path.home() / ".voicestudio" / "models"
            model_dir.mkdir(parents=True, exist_ok=True)
            torch.hub.set_dir(str(model_dir))

            print("加载 Silero VAD 模型...")
            VADDetector._model, _ = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                trust_repo=True
            )
            VADDetector._model.eval()
            print("Silero VAD 模型加载完成")

        self._model = VADDetector._model

    def _reset_state(self):
        """重置检测器状态"""
        self._h = None
        self._c = None
        self._current_speech: List[Tuple[float, float]] = []
        self._temp_start: Optional[float] = None
        self._silence_start: Optional[float] = None

    def reset(self):
        """重置检测器状态"""
        self._reset_state()

    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """
        检测音频块是否包含语音

        Args:
            audio_chunk: 音频数据 (float32, 16kHz)

        Returns:
            是否包含语音
        """
        import torch

        if audio_chunk.dtype != np.float32:
            audio_chunk = audio_chunk.astype(np.float32)

        # Silero VAD 需要 512 样本（16kHz）或 256 样本（8kHz）
        chunk_size = 512 if self._sample_rate == 16000 else 256

        if len(audio_chunk) < chunk_size:
            return False

        # 分块检测，取最大概率
        max_prob = 0.0
        for i in range(0, len(audio_chunk) - chunk_size + 1, chunk_size):
            chunk = audio_chunk[i:i + chunk_size]
            audio_tensor = torch.from_numpy(chunk)

            with torch.no_grad():
                prob = self._model(audio_tensor, self._sample_rate).item()
                max_prob = max(max_prob, prob)

        return max_prob >= self._threshold

    def get_speech_prob(self, audio_chunk: np.ndarray) -> float:
        """
        获取语音概率

        Args:
            audio_chunk: 音频数据 (float32, 16kHz)

        Returns:
            语音概率 (0-1)
        """
        import torch

        if audio_chunk.dtype != np.float32:
            audio_chunk = audio_chunk.astype(np.float32)

        chunk_size = 512 if self._sample_rate == 16000 else 256

        if len(audio_chunk) < chunk_size:
            return 0.0

        # 分块检测，取最大概率
        max_prob = 0.0
        for i in range(0, len(audio_chunk) - chunk_size + 1, chunk_size):
            chunk = audio_chunk[i:i + chunk_size]
            audio_tensor = torch.from_numpy(chunk)

            with torch.no_grad():
                prob = self._model(audio_tensor, self._sample_rate).item()
                max_prob = max(max_prob, prob)

        return max_prob

    def process_chunk(
        self,
        audio_chunk: np.ndarray,
        chunk_offset_ms: float = 0
    ) -> List[Tuple[float, float]]:
        """
        处理音频块并返回检测到的语音段

        Args:
            audio_chunk: 音频数据 (float32, 16kHz)
            chunk_offset_ms: 当前块在整个音频中的偏移（毫秒）

        Returns:
            语音段列表 [(start_ms, end_ms), ...]
        """
        import torch

        if audio_chunk.dtype != np.float32:
            audio_chunk = audio_chunk.astype(np.float32)

        # Silero VAD 需要 512 样本（16kHz）或 256 样本（8kHz）
        vad_chunk_size = 512 if self._sample_rate == 16000 else 256

        if len(audio_chunk) < vad_chunk_size:
            return self._current_speech.copy()

        # 分块检测，取最大概率
        max_prob = 0.0
        for i in range(0, len(audio_chunk) - vad_chunk_size + 1, vad_chunk_size):
            chunk = audio_chunk[i:i + vad_chunk_size]
            audio_tensor = torch.from_numpy(chunk)

            with torch.no_grad():
                prob = self._model(audio_tensor, self._sample_rate).item()
                max_prob = max(max_prob, prob)

        is_speech = max_prob >= self._threshold

        current_time_ms = chunk_offset_ms

        if is_speech:
            if self._temp_start is None:
                # 语音开始
                self._temp_start = current_time_ms
            self._silence_start = None
        else:
            if self._temp_start is not None:
                # 可能是语音结束
                if self._silence_start is None:
                    self._silence_start = current_time_ms
                elif current_time_ms - self._silence_start >= self._min_silence_ms:
                    # 确认语音段结束
                    end_time = self._silence_start + self._speech_pad_ms
                    start_time = max(0, self._temp_start - self._speech_pad_ms)
                    self._current_speech.append((start_time, end_time))
                    self._temp_start = None
                    self._silence_start = None

        return self._current_speech.copy()

    def get_current_speech_segments(self) -> List[Tuple[float, float]]:
        """获取当前已检测到的语音段"""
        return self._current_speech.copy()

    def finalize(self) -> List[Tuple[float, float]]:
        """
        结束检测，返回最终的语音段列表

        Returns:
            语音段列表 [(start_ms, end_ms), ...]
        """
        if self._temp_start is not None:
            # 如果还有未结束的语音段，添加到最后
            end_time = self._silence_start if self._silence_start else None
            start_time = max(0, self._temp_start - self._speech_pad_ms)
            self._current_speech.append((start_time, end_time))

        return self._current_speech.copy()


def detect_speech_segments(
    audio: np.ndarray,
    sample_rate: int = 16000,
    threshold: float = 0.5,
    min_silence_ms: int = 500,
    speech_pad_ms: int = 200,
) -> List[Tuple[float, float]]:
    """
    检测音频中的语音段（便捷函数）

    Args:
        audio: 音频数据 (float32)
        sample_rate: 采样率
        threshold: 检测阈值
        min_silence_ms: 最小静音时长
        speech_pad_ms: 语音段填充

    Returns:
        语音段列表 [(start_s, end_s), ...]
    """
    vad = VADDetector(
        sample_rate=sample_rate,
        threshold=threshold,
        min_silence_ms=min_silence_ms,
        speech_pad_ms=speech_pad_ms,
    )

    # 分块处理（Silero VAD 推荐 512 或 1024 样本）
    chunk_size = 512 if sample_rate == 16000 else 256
    segments = []

    for i in range(0, len(audio), chunk_size):
        chunk = audio[i:i + chunk_size]
        if len(chunk) < chunk_size:
            break
        offset_ms = i / sample_rate * 1000
        vad.process_chunk(chunk, offset_ms)

    # 获取最终结果
    segments_ms = vad.finalize()

    # 转换为秒
    segments = [(s / 1000, e / 1000 if e else None) for s, e in segments_ms]

    return segments