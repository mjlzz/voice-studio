"""
STT 引擎测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass
from typing import List, Optional

from voice_studio.stt import STTEngine, TranscribeResult, Segment, Word, get_stt_engine


@dataclass
class MockWord:
    """模拟词级时间戳"""
    word: str
    start: float
    end: float
    probability: float


@dataclass
class MockSegment:
    """模拟语音片段"""
    id: int
    start: float
    end: float
    text: str
    words: List[MockWord]


@dataclass
class MockTranscriptionInfo:
    """模拟转写信息"""
    language: str
    language_probability: float
    duration: float


class TestSTTEngine:
    """STT 引擎测试"""

    @pytest.fixture
    def mock_whisper_model(self):
        """Mock Whisper 模型"""
        with patch('voice_studio.stt.WhisperModel') as mock_model_class:
            mock_model = Mock()
            mock_model_class.return_value = mock_model

            # 模拟转写结果
            mock_segment1 = MockSegment(
                id=0,
                start=0.0,
                end=2.5,
                text="你好世界",
                words=[
                    MockWord(word="你好", start=0.0, end=1.0, probability=0.95),
                    MockWord(word="世界", start=1.2, end=2.5, probability=0.92),
                ]
            )
            mock_segment2 = MockSegment(
                id=1,
                start=2.5,
                end=5.0,
                text="这是一个测试",
                words=[
                    MockWord(word="这是", start=2.5, end=3.5, probability=0.88),
                    MockWord(word="一个", start=3.5, end=4.0, probability=0.90),
                    MockWord(word="测试", start=4.0, end=5.0, probability=0.93),
                ]
            )

            mock_info = MockTranscriptionInfo(
                language="zh",
                language_probability=0.98,
                duration=5.0
            )

            mock_model.transcribe.return_value = ([mock_segment1, mock_segment2], mock_info)

            yield mock_model

    @pytest.fixture
    def stt_engine(self, mock_whisper_model):
        """创建 STT 引擎实例"""
        # 重置单例
        STTEngine._instance = None
        STTEngine._model = None
        return STTEngine()

    def test_transcribe_success(self, stt_engine: STTEngine, mock_whisper_model):
        """测试正常转写"""
        result = stt_engine.transcribe("test.wav")

        assert isinstance(result, TranscribeResult)
        assert result.language == "zh"
        assert result.language_prob == 0.98
        assert len(result.segments) == 2
        assert "你好世界" in result.text
        assert "这是一个测试" in result.text

    def test_transcribe_with_word_timestamps(self, stt_engine: STTEngine, mock_whisper_model):
        """测试词级时间戳"""
        result = stt_engine.transcribe("test.wav", word_timestamps=True)

        assert len(result.segments) > 0
        first_segment = result.segments[0]
        assert len(first_segment["words"]) == 2
        assert first_segment["words"][0]["word"] == "你好"

    def test_transcribe_with_language(self, stt_engine: STTEngine, mock_whisper_model):
        """测试指定语言"""
        result = stt_engine.transcribe("test.wav", language="en")

        # 验证 transcribe 被正确调用
        mock_whisper_model.transcribe.assert_called_once()
        call_kwargs = mock_whisper_model.transcribe.call_args[1]
        assert call_kwargs["language"] == "en"

    def test_transcribe_rtf_calculation(self, stt_engine: STTEngine, mock_whisper_model):
        """测试 RTF 计算"""
        result = stt_engine.transcribe("test.wav")

        assert result.rtf >= 0
        assert result.process_time >= 0  # Mock 时可能为 0

    def test_transcribe_beam_size(self, stt_engine: STTEngine, mock_whisper_model):
        """测试 beam_size 参数"""
        result = stt_engine.transcribe("test.wav", beam_size=5)

        call_kwargs = mock_whisper_model.transcribe.call_args[1]
        assert call_kwargs["beam_size"] == 5

    def test_singleton_pattern(self, mock_whisper_model):
        """测试单例模式"""
        STTEngine._instance = None
        STTEngine._model = None

        engine1 = STTEngine()
        engine2 = STTEngine()

        assert engine1 is engine2

    def test_get_stt_engine(self, mock_whisper_model):
        """测试全局引擎获取"""
        import voice_studio.stt as stt_module
        stt_module._engine = None
        STTEngine._instance = None
        STTEngine._model = None

        engine = get_stt_engine()
        assert isinstance(engine, STTEngine)

        # 第二次调用应返回同一实例
        engine2 = get_stt_engine()
        assert engine is engine2

    def test_transcribe_empty_audio(self, stt_engine: STTEngine, mock_whisper_model):
        """测试空音频转写"""
        # 模拟空音频
        mock_whisper_model.transcribe.return_value = ([], MockTranscriptionInfo(
            language="zh",
            language_probability=0.5,
            duration=0.0
        ))

        result = stt_engine.transcribe("empty.wav")

        assert result.text == ""
        assert result.duration == 0
        assert result.rtf == 0


class TestTranscribeResult:
    """转写结果模型测试"""

    def test_model_creation(self):
        """测试模型创建"""
        result = TranscribeResult(
            language="zh",
            language_prob=0.95,
            duration=10.5,
            process_time=2.1,
            rtf=0.2,
            segments=[],
            text="测试文本"
        )

        assert result.language == "zh"
        assert result.duration == 10.5
        assert result.text == "测试文本"

    def test_model_with_segments(self):
        """测试包含片段的结果"""
        segments = [
            {
                "id": 0,
                "start": 0.0,
                "end": 2.0,
                "text": "第一段",
                "words": []
            }
        ]

        result = TranscribeResult(
            language="zh",
            language_prob=0.95,
            duration=2.0,
            process_time=0.5,
            rtf=0.25,
            segments=segments,
            text="第一段"
        )

        assert len(result.segments) == 1
        assert result.segments[0]["text"] == "第一段"


class TestSegment:
    """语音片段模型测试"""

    def test_segment_creation(self):
        """测试片段创建"""
        segment = Segment(
            id=0,
            start=0.0,
            end=5.0,
            text="测试片段",
            words=[]
        )

        assert segment.id == 0
        assert segment.start == 0.0
        assert segment.end == 5.0
        assert segment.text == "测试片段"

    def test_segment_with_words(self):
        """测试包含词的片段"""
        words = [
            {"word": "测试", "start": 0.0, "end": 0.5, "probability": 0.9},
            {"word": "片段", "start": 0.5, "end": 1.0, "probability": 0.85}
        ]

        segment = Segment(
            id=0,
            start=0.0,
            end=1.0,
            text="测试片段",
            words=words
        )

        assert len(segment.words) == 2


class TestWord:
    """词级时间戳模型测试"""

    def test_word_creation(self):
        """测试词创建"""
        word = Word(
            word="测试",
            start=0.0,
            end=0.5,
            probability=0.95
        )

        assert word.word == "测试"
        assert word.start == 0.0
        assert word.end == 0.5
        assert word.probability == 0.95