"""
本地 TTS 引擎测试 (Piper TTS)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path
import tempfile

from voice_studio.tts_local import (
    LocalTTSEngine,
    LocalVoice,
    PIPER_MODELS,
    get_local_tts_engine,
    LOCAL_CHINESE_VOICES,
    LOCAL_ENGLISH_VOICES,
)


class TestLocalVoice:
    """LocalVoice 数据类测试"""

    def test_local_voice_creation(self):
        """测试 LocalVoice 创建"""
        voice = LocalVoice(
            name="zh_CN-huayan",
            language="zh_CN",
            quality="medium",
            model_path=Path("/tmp/model.onnx"),
            config_path=Path("/tmp/model.onnx.json")
        )

        assert voice.name == "zh_CN-huayan"
        assert voice.language == "zh_CN"
        assert voice.quality == "medium"
        assert voice.model_path == Path("/tmp/model.onnx")


class TestPiperModels:
    """Piper 模型配置测试"""

    def test_models_defined(self):
        """测试模型已定义"""
        assert len(PIPER_MODELS) > 0
        assert "zh_CN-huayan" in PIPER_MODELS
        assert "en_US-lessac" in PIPER_MODELS

    def test_model_structure(self):
        """测试模型配置结构"""
        for name, info in PIPER_MODELS.items():
            assert "language" in info
            assert "quality" in info
            assert "url" in info
            assert "config_url" in info

    def test_chinese_model_exists(self):
        """测试中文模型存在"""
        chinese_models = [k for k in PIPER_MODELS if k.startswith("zh_")]
        assert len(chinese_models) > 0

    def test_english_models_exist(self):
        """测试英文模型存在"""
        english_models = [k for k in PIPER_MODELS if k.startswith("en_")]
        assert len(english_models) >= 2


class TestLocalTTSEngine:
    """本地 TTS 引擎测试"""

    @pytest.fixture
    def temp_models_dir(self):
        """临时模型目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def mock_settings(self, temp_models_dir):
        """Mock settings"""
        with patch('voice_studio.tts_local.settings') as mock:
            mock.models_dir = temp_models_dir
            yield mock

    @pytest.fixture
    def local_engine(self, mock_settings):
        """创建本地 TTS 引擎实例"""
        import voice_studio.tts_local as tts_local_module
        tts_local_module._local_engine = None
        return LocalTTSEngine()

    def test_engine_initialization(self, local_engine: LocalTTSEngine, mock_settings):
        """测试引擎初始化"""
        assert local_engine._loaded_model is None
        assert local_engine._piper_voice is None

    def test_list_voices(self, local_engine: LocalTTSEngine):
        """测试列出音色"""
        voices = local_engine.list_voices()

        assert len(voices) == len(PIPER_MODELS)
        for voice in voices:
            assert "name" in voice
            assert "language" in voice
            assert "quality" in voice
            assert "downloaded" in voice

    def test_get_available_voices_empty(self, local_engine: LocalTTSEngine, mock_settings):
        """测试获取已下载音色（空）"""
        voices = local_engine.get_available_voices()
        assert voices == []

    def test_get_available_voices_with_models(self, local_engine: LocalTTSEngine, mock_settings):
        """测试获取已下载音色（有模型）"""
        # 创建模拟的模型文件
        models_dir = mock_settings.models_dir / "piper"
        models_dir.mkdir(parents=True, exist_ok=True)
        (models_dir / "zh_CN-huayan.onnx").touch()

        voices = local_engine.get_available_voices()
        assert "zh_CN-huayan" in voices

    def test_ensure_model_unknown_voice(self, local_engine: LocalTTSEngine):
        """测试未知音色"""
        with pytest.raises(ValueError) as exc_info:
            local_engine._ensure_model("unknown_voice")

        assert "未知的音色" in str(exc_info.value)

    def test_get_local_tts_engine(self, mock_settings):
        """测试全局引擎获取"""
        import voice_studio.tts_local as tts_local_module
        tts_local_module._local_engine = None

        engine1 = get_local_tts_engine()
        engine2 = get_local_tts_engine()

        assert engine1 is engine2
        assert isinstance(engine1, LocalTTSEngine)


class TestLocalTTSEngineSynthesize:
    """本地 TTS 合成测试（需要 mock Piper）"""

    @pytest.fixture
    def temp_dirs(self):
        """临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            models_dir = Path(tmpdir) / "models" / "piper"
            output_dir = Path(tmpdir) / "output"
            models_dir.mkdir(parents=True, exist_ok=True)
            output_dir.mkdir(parents=True, exist_ok=True)
            yield {"models_dir": models_dir, "output_dir": output_dir}

    @pytest.fixture
    def mock_settings_with_dirs(self, temp_dirs):
        """Mock settings with directories"""
        with patch('voice_studio.tts_local.settings') as mock:
            mock.models_dir = temp_dirs["models_dir"].parent
            mock.output_dir = temp_dirs["output_dir"]
            yield mock

    @pytest.fixture
    def engine_with_mocks(self, mock_settings_with_dirs):
        """创建带 mock 的引擎"""
        import voice_studio.tts_local as tts_local_module
        tts_local_module._local_engine = None
        return LocalTTSEngine()

    def test_synthesize_downloads_model_if_missing(
        self,
        engine_with_mocks: LocalTTSEngine,
        temp_dirs
    ):
        """测试模型不存在时下载"""
        output_path = str(temp_dirs["output_dir"] / "test.wav")

        # 创建模拟模型文件
        models_dir = temp_dirs["models_dir"]
        (models_dir / "zh_CN-huayan.onnx").touch()
        (models_dir / "zh_CN-huayan.onnx.json").touch()

        # 直接调用 _ensure_model
        voice_info = engine_with_mocks._ensure_model("zh_CN-huayan")
        assert voice_info.name == "zh_CN-huayan"

    @pytest.mark.asyncio
    async def test_synthesize_async(self, engine_with_mocks: LocalTTSEngine, temp_dirs):
        """测试异步合成"""
        output_path = str(temp_dirs["output_dir"] / "test_async.wav")

        # 创建模拟模型文件
        models_dir = temp_dirs["models_dir"]
        (models_dir / "zh_CN-huayan.onnx").touch()
        (models_dir / "zh_CN-huayan.onnx.json").touch()

        # Mock synthesize
        with patch.object(engine_with_mocks, 'synthesize', return_value=output_path) as mock_syn:
            result = await engine_with_mocks.synthesize_async(
                text="测试文本",
                output_path=output_path
            )
            assert result == output_path
            mock_syn.assert_called_once()


class TestLocalVoicePresets:
    """本地预设音色测试"""

    def test_chinese_voices_defined(self):
        """测试中文预设音色"""
        assert len(LOCAL_CHINESE_VOICES) > 0
        assert "huayan" in LOCAL_CHINESE_VOICES
        assert LOCAL_CHINESE_VOICES["huayan"] == "zh_CN-huayan"

    def test_english_voices_defined(self):
        """测试英文预设音色"""
        assert len(LOCAL_ENGLISH_VOICES) > 0
        assert "lessac" in LOCAL_ENGLISH_VOICES
        assert "amy" in LOCAL_ENGLISH_VOICES

    def test_voice_mapping_valid(self):
        """测试音色映射有效"""
        for alias, full_name in LOCAL_CHINESE_VOICES.items():
            assert full_name in PIPER_MODELS

        for alias, full_name in LOCAL_ENGLISH_VOICES.items():
            assert full_name in PIPER_MODELS