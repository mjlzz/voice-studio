"""
STT (Speech-to-Text) 语音转文字引擎
基于 faster-whisper 实现
"""
import time
from typing import Optional
from pathlib import Path

from faster_whisper import WhisperModel
from pydantic import BaseModel

from .config import settings


class TranscribeResult(BaseModel):
    """转写结果"""
    language: str
    language_prob: float
    duration: float
    process_time: float
    rtf: float
    segments: list
    text: str = ""  # 完整文本


class Segment(BaseModel):
    """语音片段"""
    id: int
    start: float
    end: float
    text: str
    words: list = []


class Word(BaseModel):
    """词级时间戳"""
    word: str
    start: float
    end: float
    probability: float


class STTEngine:
    """STT 引擎 - 基于 faster-whisper"""

    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._model is None:
            self._load_model()

    def _load_model(self):
        """加载 Whisper 模型"""
        print(f"加载 Whisper 模型: {settings.whisper_model} ({settings.whisper_device})...")
        self._model = WhisperModel(
            settings.whisper_model,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
            cpu_threads=4,
            num_workers=1
        )
        print("Whisper 模型加载完成")

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        word_timestamps: bool = True,
        beam_size: int = 3
    ) -> TranscribeResult:
        """
        转写音频文件

        Args:
            audio_path: 音频文件路径
            language: 语言代码 (None=自动检测)
            word_timestamps: 是否返回词级时间戳
            beam_size: beam search 大小

        Returns:
            TranscribeResult: 转写结果
        """
        t0 = time.time()

        segments_raw, info = self._model.transcribe(
            audio_path,
            language=language,
            task="transcribe",
            beam_size=beam_size,
            word_timestamps=word_timestamps,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=200,
                threshold=0.5,
            ),
            condition_on_previous_text=False,
            no_speech_threshold=0.6,
            log_prob_threshold=-1.0,
            compression_ratio_threshold=2.4,
        )

        segments = []
        for seg in segments_raw:
            segment_dict = {
                "id": seg.id,
                "start": round(seg.start, 3),
                "end": round(seg.end, 3),
                "text": seg.text.strip(),
                "words": []
            }

            if word_timestamps and seg.words:
                for w in seg.words:
                    segment_dict["words"].append({
                        "word": w.word.strip(),
                        "start": round(w.start, 3),
                        "end": round(w.end, 3),
                        "probability": round(w.probability, 3)
                    })

            segments.append(segment_dict)

        elapsed = time.time() - t0
        audio_duration = segments[-1]["end"] if segments else 0

        # 拼接完整文本
        full_text = " ".join(seg["text"] for seg in segments)

        return TranscribeResult(
            language=info.language,
            language_prob=round(info.language_probability, 3),
            duration=round(audio_duration, 3),
            process_time=round(elapsed, 3),
            rtf=round(elapsed / audio_duration, 3) if audio_duration else 0,
            segments=segments,
            text=full_text
        )


# 全局引擎实例
_engine: Optional[STTEngine] = None


def get_stt_engine() -> STTEngine:
    """获取 STT 引擎实例"""
    global _engine
    if _engine is None:
        _engine = STTEngine()
    return _engine