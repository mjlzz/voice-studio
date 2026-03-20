"""
Voice Studio 测试配置
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from dataclasses import dataclass
from typing import List, Optional

from fastapi.testclient import TestClient


@dataclass
class MockSegment:
    """模拟转写片段"""
    start: float
    end: float
    text: str
    words: Optional[List] = None


@dataclass
class MockTranscribeResult:
    """模拟转写结果"""
    language: str
    language_prob: float
    duration: float
    process_time: float
    rtf: float
    segments: List[MockSegment]
    text: str


@dataclass
class MockVoice:
    """模拟音色"""
    name: str
    short_name: str
    gender: str
    locale: str


@pytest.fixture
def mock_stt_engine():
    """Mock STT 引擎"""
    with patch('voice_studio.stt.get_stt_engine') as mock_get_engine:
        engine = Mock()
        engine.transcribe.return_value = MockTranscribeResult(
            language="zh",
            language_prob=0.99,
            duration=5.0,
            process_time=1.0,
            rtf=0.2,
            segments=[
                MockSegment(start=0.0, end=2.0, text="你好", words=[]),
                MockSegment(start=2.0, end=5.0, text="这是一个测试", words=[]),
            ],
            text="你好这是一个测试"
        )
        mock_get_engine.return_value = engine
        yield engine


@pytest.fixture
def mock_tts_engine():
    """Mock 云端 TTS 引擎"""
    with patch('voice_studio.tts.get_tts_engine') as mock_get_engine:
        engine = Mock()
        engine.synthesize = AsyncMock()
        engine.list_voices = AsyncMock(return_value=[
            MockVoice(
                name="zh-CN-XiaoxiaoNeural",
                short_name="Xiaoxiao",
                gender="Female",
                locale="zh-CN"
            ),
            MockVoice(
                name="en-US-JennyNeural",
                short_name="Jenny",
                gender="Female",
                locale="en-US"
            ),
        ])
        mock_get_engine.return_value = engine
        yield engine


@pytest.fixture
def mock_local_tts_engine():
    """Mock 本地 TTS 引擎"""
    with patch('voice_studio.tts_local.get_local_tts_engine') as mock_get_engine:
        engine = Mock()
        engine.synthesize_async = AsyncMock()
        engine.list_voices.return_value = [
            {"id": "zh_CN-huayan", "name": "华燕", "language": "zh"},
            {"id": "en_US-lessac", "name": "Lessac", "language": "en"},
        ]
        engine.get_available_voices.return_value = ["zh_CN-huayan", "en_US-lessac"]
        mock_get_engine.return_value = engine
        yield engine


@pytest.fixture
def temp_output_dir():
    """临时输出目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def client(mock_stt_engine, mock_tts_engine, mock_local_tts_engine):
    """测试客户端"""
    from voice_studio.api import app
    return TestClient(app)


@pytest.fixture
def sample_audio_bytes():
    """模拟音频文件字节（WAV 头）"""
    # 最小的有效 WAV 文件头
    import struct
    # RIFF header
    riff = b'RIFF'
    wave = b'WAVE'
    fmt = b'fmt '
    data = b'data'

    # WAV format (PCM, mono, 16-bit, 16000 Hz)
    n_channels = 1
    sample_rate = 16000
    bits_per_sample = 16
    byte_rate = sample_rate * n_channels * bits_per_sample // 8
    block_align = n_channels * bits_per_sample // 8

    # Create minimal WAV
    audio_data = b'\x00\x00' * 16000  # 1 second of silence

    wav = (
        riff + struct.pack('<I', 36 + len(audio_data)) + wave +
        fmt + struct.pack('<I', 16) +  # fmt chunk size
        struct.pack('<HHIIHH', 1, n_channels, sample_rate, byte_rate, block_align, bits_per_sample) +
        data + struct.pack('<I', len(audio_data)) + audio_data
    )
    return wav