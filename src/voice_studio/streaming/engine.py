"""
流式语音转文字引擎
支持实时音频流转写
"""
import time
import threading
from typing import Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

from faster_whisper import WhisperModel

from .buffer import AudioRingBuffer
from .vad import VADDetector
from ..config import settings
from ..text_converter import convert_chinese_text


class TranscriptionType(Enum):
    """转写结果类型"""
    PARTIAL = "partial"  # 部分结果（正在说话）
    FINAL = "final"      # 最终结果（语音段结束）


@dataclass
class TranscriptionChunk:
    """转写结果块"""
    type: TranscriptionType
    text: str
    language: str = ""
    confidence: float = 0.0
    start_time: float = 0.0  # 音频开始时间（秒）
    end_time: float = 0.0    # 音频结束时间（秒）
    timestamp: float = field(default_factory=time.time)  # 结果生成时间


class StreamingSTTEngine:
    """
    流式语音转文字引擎

    特点：
    - 实时接收音频流
    - VAD 检测语音活动
    - 自动分段转写
    - 支持 partial 和 final 结果
    """

    _instance = None
    _model = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        model_size: Optional[str] = None,
        device: Optional[str] = None,
        compute_type: Optional[str] = None,
        vad_threshold: float = 0.5,
        min_silence_ms: int = 500,
        max_buffer_ms: int = 30000,
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ):
        """
        初始化流式 STT 引擎

        Args:
            model_size: 模型大小 (tiny/base/small/medium)
            device: 推理设备 (cpu/cuda)
            compute_type: 计算类型 (int8/float16/float32)
            vad_threshold: VAD 检测阈值
            min_silence_ms: 最小静音时长（用于分句）
            max_buffer_ms: 最大音频缓冲时长
            sample_rate: 采样率
            language: 语言代码 (None=自动检测, zh=中文, en=英文, yue=粤语)
        """
        self._model_size = model_size or settings.whisper_model
        self._device = device or settings.whisper_device
        self._compute_type = compute_type or settings.whisper_compute_type
        self._vad_threshold = vad_threshold
        self._min_silence_ms = min_silence_ms
        self._max_buffer_ms = max_buffer_ms
        self._sample_rate = sample_rate
        self._language = language

        # 组件
        self._buffer: Optional[AudioRingBuffer] = None
        self._vad: Optional[VADDetector] = None

        # 状态
        self._is_speech = False
        self._speech_start_time: Optional[float] = None
        self._silence_start_time: Optional[float] = None
        self._last_transcribe_time: float = 0
        self._total_audio_time: float = 0

        # 回调
        self._on_result: Optional[Callable[[TranscriptionChunk], None]] = None

        # 加载模型
        self._load_model()

    def _load_model(self):
        """加载 Whisper 模型"""
        with StreamingSTTEngine._lock:
            if StreamingSTTEngine._model is None:
                print(f"加载 Whisper 模型: {self._model_size} ({self._device})...")
                StreamingSTTEngine._model = WhisperModel(
                    self._model_size,
                    device=self._device,
                    compute_type=self._compute_type,
                    cpu_threads=4,
                    num_workers=1
                )
                print("Whisper 模型加载完成")
            self._model = StreamingSTTEngine._model

    def start(self, on_result: Optional[Callable[[TranscriptionChunk], None]] = None):
        """
        开始流式转写会话

        Args:
            on_result: 结果回调函数
        """
        self._buffer = AudioRingBuffer(
            max_duration_ms=self._max_buffer_ms,
            sample_rate=self._sample_rate
        )
        self._vad = VADDetector(
            sample_rate=self._sample_rate,
            threshold=self._vad_threshold,
            min_silence_ms=self._min_silence_ms,
        )
        self._on_result = on_result

        # 重置状态
        self._is_speech = False
        self._speech_start_time = None
        self._silence_start_time = None
        self._last_transcribe_time = 0
        self._total_audio_time = 0

    def stop(self):
        """停止流式转写会话"""
        # 处理剩余缓冲区
        if self._buffer and self._buffer.data_size > 0:
            self._transcribe_buffer(is_final=True)

        if self._buffer:
            self._buffer.clear()
        if self._vad:
            self._vad.reset()

    def process_audio(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000
    ) -> Optional[TranscriptionChunk]:
        """
        处理音频块

        Args:
            audio: 音频数据 (float32 或 int16)
            sample_rate: 采样率

        Returns:
            转写结果（如果有）
        """
        if self._buffer is None:
            return None

        # 转换格式
        if audio.dtype == np.int16:
            audio = audio.astype(np.float32) / 32768.0
        elif audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        # 重采样（如果需要）
        if sample_rate != self._sample_rate:
            # 简单重采样（实际应用中应使用更高质量的重采样）
            ratio = self._sample_rate / sample_rate
            new_len = int(len(audio) * ratio)
            audio = np.interp(
                np.linspace(0, len(audio), new_len),
                np.arange(len(audio)),
                audio
            ).astype(np.float32)

        # 写入缓冲区
        self._buffer.write(audio)

        # 更新音频时间
        chunk_duration = len(audio) / self._sample_rate
        self._total_audio_time += chunk_duration

        # VAD 检测
        is_speech = self._vad.is_speech(audio) if len(audio) >= 512 else self._is_speech

        result = None

        if is_speech:
            if not self._is_speech:
                # 语音开始
                self._is_speech = True
                self._speech_start_time = self._total_audio_time - chunk_duration
                self._silence_start_time = None
            else:
                # 持续说话 - 可能需要实时反馈
                current_duration = self._total_audio_time - (self._speech_start_time or 0)

                # 每隔一定时间进行一次 partial 转写
                if (current_duration > 2.0 and
                    self._total_audio_time - self._last_transcribe_time > 1.0):
                    result = self._transcribe_buffer(is_final=False)
                    self._last_transcribe_time = self._total_audio_time
        else:
            if self._is_speech:
                # 可能是语音结束
                if self._silence_start_time is None:
                    self._silence_start_time = self._total_audio_time
                elif (self._total_audio_time - self._silence_start_time >
                      self._min_silence_ms / 1000):
                    # 确认语音段结束
                    result = self._transcribe_buffer(is_final=True)
                    self._is_speech = False
                    self._speech_start_time = None
                    self._silence_start_time = None
                    self._last_transcribe_time = self._total_audio_time

        return result

    def _transcribe_buffer(self, is_final: bool = False) -> Optional[TranscriptionChunk]:
        """
        转写缓冲区内容

        Args:
            is_final: 是否为最终结果

        Returns:
            转写结果
        """
        if self._buffer is None or self._buffer.is_empty():
            return None

        # 获取音频数据
        audio = self._buffer.read_all()

        if len(audio) < self._sample_rate * 0.3:  # 少于 0.3 秒不处理
            return None

        t0 = time.time()

        try:
            # 使用 Whisper 转写
            segments, info = self._model.transcribe(
                audio,
                language=self._language,
                task="transcribe",
                beam_size=3,
                word_timestamps=False,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=self._min_silence_ms,
                    speech_pad_ms=200,
                    threshold=self._vad_threshold,
                ),
                condition_on_previous_text=False,
            )

            # 收集文本
            texts = []
            for seg in segments:
                text = seg.text.strip()
                if text:
                    texts.append(convert_chinese_text(text, settings.chinese_text_convert))

            if not texts:
                return None

            full_text = " ".join(texts)

            elapsed = time.time() - t0

            # 清空缓冲区（对于 final 结果）
            if is_final:
                self._buffer.clear()

            return TranscriptionChunk(
                type=TranscriptionType.FINAL if is_final else TranscriptionType.PARTIAL,
                text=full_text,
                language=info.language,
                confidence=info.language_probability,
                start_time=self._speech_start_time or 0,
                end_time=self._total_audio_time,
            )

        except Exception as e:
            print(f"转写错误: {e}")
            return None

    def get_partial_result(self) -> Optional[TranscriptionChunk]:
        """
        获取当前正在转写的部分结果

        Returns:
            部分转写结果
        """
        if not self._is_speech or self._buffer is None:
            return None

        return self._transcribe_buffer(is_final=False)

    def force_finalize(self) -> Optional[TranscriptionChunk]:
        """
        强制结束当前语音段并返回结果

        Returns:
            最终转写结果
        """
        result = self._transcribe_buffer(is_final=True)
        self._is_speech = False
        self._speech_start_time = None
        self._silence_start_time = None
        return result

    def reset(self):
        """重置引擎状态"""
        if self._buffer:
            self._buffer.clear()
        if self._vad:
            self._vad.reset()

        self._is_speech = False
        self._speech_start_time = None
        self._silence_start_time = None
        self._last_transcribe_time = 0
        self._total_audio_time = 0

    @property
    def is_speech(self) -> bool:
        """当前是否在说话"""
        return self._is_speech

    @property
    def total_audio_time(self) -> float:
        """总音频时长（秒）"""
        return self._total_audio_time