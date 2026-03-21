"""
悬浮话筒配置
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import json


@dataclass
class FloatingMicConfig:
    """悬浮话筒配置"""

    # API配置
    ws_url: str = "ws://localhost:8765/api/v1/stt/stream"
    api_base_url: str = "http://localhost:8765"  # HTTP API 基础地址

    # 转写模式: "streaming" 实时流式, "batch" 录音后转写
    transcription_mode: str = "batch"

    # 窗口配置
    window_size: int = 64  # 悬浮窗大小
    window_opacity: float = 0.95  # 透明度

    # 音频配置
    sample_rate: int = 16000
    channels: int = 1
    audio_chunk_ms: int = 100  # 音频块大小(毫秒)

    # 行为配置
    auto_copy: bool = True  # 自动复制到剪贴板
    show_notification: bool = True  # 显示通知

    # 位置记忆
    position_x: Optional[int] = None
    position_y: Optional[int] = None

    # 语言
    language: Optional[str] = None  # None表示自动检测

    @classmethod
    def load(cls) -> "FloatingMicConfig":
        """从文件加载配置"""
        config_path = cls._get_config_path()
        if config_path.exists():
            try:
                with open(config_path, encoding="utf-8") as f:
                    data = json.load(f)
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            except (json.JSONDecodeError, TypeError):
                pass
        return cls()

    def save(self) -> None:
        """保存配置到文件"""
        config_path = self._get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.__dict__, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _get_config_path() -> Path:
        """获取配置文件路径"""
        return Path.home() / ".voicestudio" / "floating_mic.json"