"""
配置管理模块
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal, List


class Settings(BaseSettings):
    """应用配置"""

    # 服务配置
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True

    # STT 配置
    stt_engine: Literal["local", "cloud"] = "local"
    whisper_model: str = "base"  # tiny, base, small, medium
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"

    # TTS 配置
    tts_engine: Literal["local", "cloud"] = "local"
    default_voice: str = "zh-CN-XiaoxiaoNeural"

    # 中英混合 TTS 配置 (基于 ONNX 模型)
    mixed_tts_enabled: bool = True
    mixed_tts_model: Path = Path("models/model-steps-6.onnx")
    mixed_tts_vocoder: Path = Path("models/vocos-16khz-univ.onnx")
    mixed_tts_vocab: Path = Path("models/vocab_tts.txt")

    # 存储路径
    data_dir: Path = Path.home() / ".voicestudio"
    models_dir: Path = Path.home() / ".voicestudio" / "models"
    output_dir: Path = Path.home() / ".voicestudio" / "output"

    # 安全配置
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_audio_extensions: List[str] = [".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm"]
    allowed_mime_types: List[str] = [
        "audio/mpeg", "audio/mp3",
        "audio/wav", "audio/x-wav", "audio/wave",
        "audio/mp4", "audio/x-m4a", "audio/m4a",
        "audio/ogg", "audio/x-ogg",
        "audio/flac", "audio/x-flac",
        "audio/webm",
        "video/webm",  # 有些浏览器上传音频时使用 video/webm
    ]

    # 视频支持配置
    enable_video_stt: bool = True
    max_video_file_size: int = 500 * 1024 * 1024  # 500MB
    allowed_video_extensions: List[str] = [".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv", ".m4v"]
    allowed_video_mime_types: List[str] = [
        "video/mp4", "video/x-m4v",
        "video/x-matroska",
        "video/quicktime",
        "video/x-msvideo",
        "video/x-flv",
        "video/x-ms-wmv",
    ]
    ffmpeg_path: str = ""  # 空则自动检测
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:8000", "http://127.0.0.1:5173", "http://127.0.0.1:8000"]

    # 输入验证
    max_text_length: int = 5000  # TTS 文本最大长度

    # 速率限制
    rate_limit_stt: str = "10/minute"  # STT 接口限制
    rate_limit_tts: str = "30/minute"  # TTS 接口限制

    # 文本转换
    chinese_text_convert: Literal["none", "t2s", "s2t"] = "t2s"  # 中文繁简转换

    model_config = SettingsConfigDict(
        env_prefix="VS_",
        env_file=".env",
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()