"""
配置管理模块
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Literal


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

    # 存储路径
    data_dir: Path = Path.home() / ".voicestudio"
    models_dir: Path = Path.home() / ".voicestudio" / "models"
    output_dir: Path = Path.home() / ".voicestudio" / "output"

    class Config:
        env_prefix = "VS_"
        env_file = ".env"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()