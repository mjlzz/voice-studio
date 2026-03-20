"""
云端 TTS 引擎测试 (edge-tts)
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import tempfile
from pathlib import Path

from voice_studio.tts import TTSEngine, Voice, get_tts_engine, CHINESE_VOICES, ENGLISH_VOICES


class TestVoice:
    """Voice 数据类测试"""

    def test_voice_creation(self):
        """测试 Voice 创建"""
        voice = Voice(
            name="zh-CN-XiaoxiaoNeural",
            short_name="Xiaoxiao",
            gender="Female",
            locale="zh-CN",
            language="zh"
        )

        assert voice.name == "zh-CN-XiaoxiaoNeural"
        assert voice.short_name == "Xiaoxiao"
        assert voice.gender == "Female"
        assert voice.locale == "zh-CN"
        assert voice.language == "zh"


class TestTTSEngine:
    """TTS 引擎测试"""

    @pytest.fixture
    def mock_edge_tts(self):
        """Mock edge-tts 模块"""
        with patch('voice_studio.tts.edge_tts') as mock:
            # Mock Communicate
            mock_communicate = AsyncMock()
            mock.Communicate.return_value = mock_communicate
            mock_communicate.save = AsyncMock()

            # Mock list_voices
            mock.list_voices = AsyncMock(return_value=[
                {
                    "Name": "zh-CN-XiaoxiaoNeural",
                    "ShortName": "Xiaoxiao",
                    "Gender": "Female",
                    "Locale": "zh-CN"
                },
                {
                    "Name": "en-US-JennyNeural",
                    "ShortName": "Jenny",
                    "Gender": "Female",
                    "Locale": "en-US"
                },
                {
                    "Name": "zh-CN-YunxiNeural",
                    "ShortName": "Yunxi",
                    "Gender": "Male",
                    "Locale": "zh-CN"
                },
            ])

            yield mock

    @pytest.fixture
    def tts_engine(self, mock_edge_tts):
        """创建 TTS 引擎实例"""
        # 重置实例
        import voice_studio.tts as tts_module
        tts_module._engine = None
        return TTSEngine()

    @pytest.mark.asyncio
    async def test_synthesize_success(self, tts_engine: TTSEngine, mock_edge_tts):
        """测试正常合成"""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            output_path = f.name

        try:
            result = await tts_engine.synthesize(
                text="你好世界",
                output_path=output_path,
                voice="zh-CN-XiaoxiaoNeural"
            )

            assert result == output_path
            mock_edge_tts.Communicate.assert_called_once()

        finally:
            Path(output_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_synthesize_with_default_voice(self, tts_engine: TTSEngine, mock_edge_tts):
        """测试使用默认音色"""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            output_path = f.name

        try:
            await tts_engine.synthesize(
                text="测试文本",
                output_path=output_path
            )

            call_args = mock_edge_tts.Communicate.call_args
            # 第二个参数应该是 voice
            assert call_args[0][1] is not None  # voice 参数

        finally:
            Path(output_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_synthesize_with_rate_and_volume(self, tts_engine: TTSEngine, mock_edge_tts):
        """测试语速和音量调节"""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            output_path = f.name

        try:
            await tts_engine.synthesize(
                text="测试",
                output_path=output_path,
                voice="zh-CN-XiaoxiaoNeural",
                rate="+50%",
                volume="-20%"
            )

            call_kwargs = mock_edge_tts.Communicate.call_args[1]
            assert call_kwargs["rate"] == "+50%"
            assert call_kwargs["volume"] == "-20%"

        finally:
            Path(output_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_list_voices_all(self, tts_engine: TTSEngine, mock_edge_tts):
        """测试列出所有音色"""
        voices = await tts_engine.list_voices()

        assert len(voices) == 3
        assert isinstance(voices[0], Voice)
        assert voices[0].name == "zh-CN-XiaoxiaoNeural"

    @pytest.mark.asyncio
    async def test_list_voices_by_language(self, tts_engine: TTSEngine, mock_edge_tts):
        """测试按语言筛选音色"""
        voices = await tts_engine.list_voices(language="zh")

        assert len(voices) == 2
        for voice in voices:
            assert voice.language == "zh"

    @pytest.mark.asyncio
    async def test_list_voices_caching(self, tts_engine: TTSEngine, mock_edge_tts):
        """测试音色列表缓存"""
        # 第一次调用
        voices1 = await tts_engine.list_voices()

        # 第二次调用应该使用缓存
        voices2 = await tts_engine.list_voices()

        # list_voices 只应该被调用一次
        assert mock_edge_tts.list_voices.call_count == 1
        assert voices1 == voices2

    def test_get_chinese_voices(self, tts_engine: TTSEngine, mock_edge_tts):
        """测试获取中文音色（同步版本）"""
        voices = tts_engine.get_chinese_voices()

        assert len(voices) == 2
        for voice in voices:
            assert voice.language == "zh"

    def test_get_tts_engine(self, mock_edge_tts):
        """测试全局引擎获取"""
        import voice_studio.tts as tts_module
        tts_module._engine = None

        engine1 = get_tts_engine()
        engine2 = get_tts_engine()

        assert engine1 is engine2
        assert isinstance(engine1, TTSEngine)


class TestVoicePresets:
    """预设音色测试"""

    def test_chinese_voices_defined(self):
        """测试中文预设音色"""
        assert len(CHINESE_VOICES) > 0
        assert "xiaoxiao" in CHINESE_VOICES
        assert CHINESE_VOICES["xiaoxiao"] == "zh-CN-XiaoxiaoNeural"

    def test_english_voices_defined(self):
        """测试英文预设音色"""
        assert len(ENGLISH_VOICES) > 0
        assert "jenny" in ENGLISH_VOICES
        assert ENGLISH_VOICES["jenny"] == "en-US-JennyNeural"

    def test_voice_format(self):
        """测试音色名称格式"""
        for name, voice_id in CHINESE_VOICES.items():
            assert voice_id.startswith("zh-CN-")
            assert voice_id.endswith("Neural")

        for name, voice_id in ENGLISH_VOICES.items():
            assert voice_id.startswith("en-US-")
            assert voice_id.endswith("Neural")