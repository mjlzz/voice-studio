"""
本地 TTS 引擎测试
"""
import pytest
from pathlib import Path
import tempfile

from voice_studio.tts_local import get_local_tts_engine, PIPER_MODELS


class TestLocalTTSEngine:
    """本地 TTS 引擎测试"""

    def test_list_voices(self):
        """测试列出音色"""
        engine = get_local_tts_engine()
        voices = engine.list_voices()

        assert len(voices) > 0
        assert any(v["language"].startswith("zh") for v in voices)
        assert any(v["language"].startswith("en") for v in voices)

    def test_voice_info(self):
        """测试音色信息"""
        engine = get_local_tts_engine()
        voices = engine.list_voices()

        for voice in voices:
            assert "name" in voice
            assert "language" in voice
            assert "quality" in voice
            assert "downloaded" in voice

    def test_available_voices(self):
        """测试获取已下载音色"""
        engine = get_local_tts_engine()
        available = engine.get_available_voices()
        # 首次运行可能没有下载，所以只检查返回类型
        assert isinstance(available, list)

    @pytest.mark.skipif(
        not Path.home().joinpath(".voicestudio/models/piper/en_US-lessac.onnx").exists(),
        reason="模型未下载"
    )
    def test_synthesize_english(self):
        """测试英文合成（需要模型已下载）"""
        engine = get_local_tts_engine()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            output_path = f.name

        try:
            result = engine.synthesize(
                text="Hello, this is a test.",
                output_path=output_path,
                voice="en_US-lessac"
            )

            assert Path(result).exists()
            assert Path(result).stat().st_size > 0
        finally:
            if Path(output_path).exists():
                Path(output_path).unlink()

    @pytest.mark.skipif(
        not Path.home().joinpath(".voicestudio/models/piper/zh_CN-huayan.onnx").exists(),
        reason="模型未下载"
    )
    def test_synthesize_chinese(self):
        """测试中文合成（需要模型已下载）"""
        engine = get_local_tts_engine()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            output_path = f.name

        try:
            result = engine.synthesize(
                text="你好，这是一个测试。",
                output_path=output_path,
                voice="zh_CN-huayan"
            )

            assert Path(result).exists()
            assert Path(result).stat().st_size > 0
        finally:
            if Path(output_path).exists():
                Path(output_path).unlink()


class TestPiperModels:
    """Piper 模型配置测试"""

    def test_models_config(self):
        """测试模型配置"""
        assert "zh_CN-huayan" in PIPER_MODELS
        assert "en_US-lessac" in PIPER_MODELS

        for name, config in PIPER_MODELS.items():
            assert "language" in config
            assert "quality" in config
            assert "url" in config
            assert "config_url" in config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])