"""
配置模块测试
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile

from voice_studio.config import Settings


class TestSettings:
    """配置类测试"""

    def test_default_values(self):
        """测试默认值"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, 'home', return_value=Path(tmpdir)):
                settings = Settings()

                assert settings.host == "127.0.0.1"
                assert settings.port == 8000
                assert settings.debug is True
                assert settings.stt_engine == "local"
                assert settings.tts_engine == "local"
                assert settings.whisper_model == "base"
                assert settings.default_voice == "zh-CN-XiaoxiaoNeural"

    def test_max_file_size_default(self):
        """测试默认文件大小限制"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, 'home', return_value=Path(tmpdir)):
                settings = Settings()
                assert settings.max_file_size == 50 * 1024 * 1024  # 50MB

    def test_allowed_extensions(self):
        """测试允许的扩展名"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, 'home', return_value=Path(tmpdir)):
                settings = Settings()
                assert ".mp3" in settings.allowed_audio_extensions
                assert ".wav" in settings.allowed_audio_extensions
                assert ".exe" not in settings.allowed_audio_extensions

    def test_cors_origins_default(self):
        """测试默认 CORS 源"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, 'home', return_value=Path(tmpdir)):
                settings = Settings()
                assert "http://localhost:5173" in settings.cors_origins
                assert "http://localhost:8000" in settings.cors_origins

    def test_max_text_length_default(self):
        """测试默认文本长度限制"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, 'home', return_value=Path(tmpdir)):
                settings = Settings()
                assert settings.max_text_length == 5000

    def test_rate_limits_default(self):
        """测试默认速率限制"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, 'home', return_value=Path(tmpdir)):
                settings = Settings()
                assert settings.rate_limit_stt == "10/minute"
                assert settings.rate_limit_tts == "30/minute"

    def test_directories_created(self):
        """测试目录自动创建"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir) / "test_config"

            with patch.object(Path, 'home', return_value=base_path):
                settings = Settings()

                assert settings.data_dir.exists()
                assert settings.models_dir.exists()
                assert settings.output_dir.exists()

    def test_env_prefix(self):
        """测试环境变量前缀"""
        assert Settings.model_config["env_prefix"] == "VS_"

    def test_custom_values(self):
        """测试自定义值"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, 'home', return_value=Path(tmpdir)):
                settings = Settings(
                    host="0.0.0.0",
                    port=9000,
                    debug=False,
                    whisper_model="medium"
                )

                assert settings.host == "0.0.0.0"
                assert settings.port == 9000
                assert settings.debug is False
                assert settings.whisper_model == "medium"

    def test_allowed_mime_types(self):
        """测试允许的 MIME 类型"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, 'home', return_value=Path(tmpdir)):
                settings = Settings()

                assert "audio/mpeg" in settings.allowed_mime_types
                assert "audio/wav" in settings.allowed_mime_types
                assert "video/webm" in settings.allowed_mime_types  # 允许某些浏览器的行为

    def test_stt_engine_validation(self):
        """测试 STT 引擎验证"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, 'home', return_value=Path(tmpdir)):
                # 有效值
                settings = Settings(stt_engine="local")
                assert settings.stt_engine == "local"

                settings = Settings(stt_engine="cloud")
                assert settings.stt_engine == "cloud"

    def test_tts_engine_validation(self):
        """测试 TTS 引擎验证"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, 'home', return_value=Path(tmpdir)):
                settings = Settings(tts_engine="local")
                assert settings.tts_engine == "local"

                settings = Settings(tts_engine="cloud")
                assert settings.tts_engine == "cloud"


class TestSettingsEnvironmentVariables:
    """环境变量测试"""

    def test_env_var_override(self, monkeypatch):
        """测试环境变量覆盖"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, 'home', return_value=Path(tmpdir)):
                monkeypatch.setenv("VS_HOST", "0.0.0.0")
                monkeypatch.setenv("VS_PORT", "9000")
                monkeypatch.setenv("VS_DEBUG", "false")
                monkeypatch.setenv("VS_WHISPER_MODEL", "medium")

                settings = Settings()

                assert settings.host == "0.0.0.0"
                assert settings.port == 9000
                assert settings.debug is False
                assert settings.whisper_model == "medium"

    def test_env_var_max_file_size(self, monkeypatch):
        """测试文件大小限制环境变量"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, 'home', return_value=Path(tmpdir)):
                monkeypatch.setenv("VS_MAX_FILE_SIZE", "104857600")  # 100MB

                settings = Settings()
                assert settings.max_file_size == 104857600

    def test_env_var_cors_origins(self, monkeypatch):
        """测试 CORS 源环境变量"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, 'home', return_value=Path(tmpdir)):
                monkeypatch.setenv("VS_CORS_ORIGINS", '["http://example.com"]')

                settings = Settings()
                assert "http://example.com" in settings.cors_origins


class TestSettingsValidation:
    """配置验证测试"""

    def test_port_range(self):
        """测试端口范围"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, 'home', return_value=Path(tmpdir)):
                # 有效端口
                settings = Settings(port=8080)
                assert settings.port == 8080

                # 边界值
                settings = Settings(port=1)
                assert settings.port == 1

                settings = Settings(port=65535)
                assert settings.port == 65535

    def test_whisper_model_values(self):
        """测试 Whisper 模型值"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, 'home', return_value=Path(tmpdir)):
                for model in ["tiny", "base", "small", "medium"]:
                    settings = Settings(whisper_model=model)
                    assert settings.whisper_model == model

    def test_whisper_device_default(self):
        """测试 Whisper 设备默认值"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, 'home', return_value=Path(tmpdir)):
                settings = Settings()
                assert settings.whisper_device == "cpu"

    def test_compute_type_default(self):
        """测试计算类型默认值"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, 'home', return_value=Path(tmpdir)):
                settings = Settings()
                assert settings.whisper_compute_type == "int8"