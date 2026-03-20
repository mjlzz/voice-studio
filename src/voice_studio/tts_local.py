"""
本地 TTS (Text-to-Speech) 文字转语音引擎
基于 Piper TTS 实现 (离线、CPU优化)
"""
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass

from .config import settings


@dataclass
class LocalVoice:
    """本地语音音色"""
    name: str          # 模型名称，如 "zh_CN-huayan"
    language: str      # 语言代码，如 "zh_CN"
    quality: str       # 音质，如 "low", "medium", "high"
    model_path: Path   # 模型文件路径
    config_path: Path  # 配置文件路径


# 预设模型配置
PIPER_MODELS = {
    # 中文模型
    "zh_CN-huayan": {
        "language": "zh_CN",
        "quality": "medium",
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx.json",
    },
    # 英文模型
    "en_US-lessac": {
        "language": "en_US",
        "quality": "medium",
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
    },
    "en_US-amy": {
        "language": "en_US",
        "quality": "medium",
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json",
    },
}


class LocalTTSEngine:
    """本地 TTS 引擎 - 基于 Piper TTS"""

    def __init__(self):
        self._models_dir = settings.models_dir / "piper"
        self._models_dir.mkdir(parents=True, exist_ok=True)
        self._loaded_model: Optional[str] = None
        self._piper_voice = None

    def _download_file(self, url: str, dest: Path, description: str = "文件") -> None:
        """下载文件"""
        print(f"正在下载{description}: {url}")
        try:
            urllib.request.urlretrieve(url, dest)
            print(f"下载完成: {dest}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"下载失败: {e}")

    def _ensure_model(self, voice_name: str) -> LocalVoice:
        """确保模型已下载，返回模型信息"""
        if voice_name not in PIPER_MODELS:
            raise ValueError(f"未知的音色: {voice_name}，可用: {list(PIPER_MODELS.keys())}")

        model_info = PIPER_MODELS[voice_name]
        model_path = self._models_dir / f"{voice_name}.onnx"
        config_path = self._models_dir / f"{voice_name}.onnx.json"

        # 下载模型（如果不存在）
        if not model_path.exists():
            self._download_file(model_info["url"], model_path, "模型文件")

        # 下载配置（如果不存在）
        if not config_path.exists():
            self._download_file(model_info["config_url"], config_path, "配置文件")

        return LocalVoice(
            name=voice_name,
            language=model_info["language"],
            quality=model_info["quality"],
            model_path=model_path,
            config_path=config_path
        )

    def synthesize(
        self,
        text: str,
        output_path: str,
        voice: Optional[str] = None,
        noise_scale: float = 0.667,
        length_scale: float = 1.0,
    ) -> str:
        """
        合成语音

        Args:
            text: 要合成的文本
            output_path: 输出文件路径 (WAV格式)
            voice: 音色名称 (默认 zh_CN-huayan)
            noise_scale: 噪声比例 (影响随机性)
            length_scale: 长度比例 (影响语速，越小越快)

        Returns:
            str: 输出文件路径
        """
        from piper import PiperVoice
        from piper.config import SynthesisConfig

        voice_name = voice or "zh_CN-huayan"

        # 确保模型已下载
        voice_info = self._ensure_model(voice_name)

        # 加载模型（如果需要）
        if self._loaded_model != voice_name:
            self._piper_voice = PiperVoice.load(
                str(voice_info.model_path)
            )
            self._loaded_model = voice_name

        # 配置合成参数
        syn_config = SynthesisConfig(
            noise_scale=noise_scale,
            length_scale=length_scale,
        )

        # 合成语音
        import soundfile as sf
        import numpy as np

        # 收集所有音频块
        audio_chunks = []
        for chunk in self._piper_voice.synthesize(text, syn_config=syn_config):
            audio_chunks.append(chunk.audio_int16_array)

        # 合并音频
        audio_data = np.concatenate(audio_chunks)

        # 保存为 WAV
        sf.write(output_path, audio_data, samplerate=22050)

        return output_path

    async def synthesize_async(
        self,
        text: str,
        output_path: str,
        voice: Optional[str] = None,
        noise_scale: float = 0.667,
        length_scale: float = 1.0,
    ) -> str:
        """异步合成语音（兼容现有接口）"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.synthesize(text, output_path, voice, noise_scale, length_scale)
        )

    def list_voices(self) -> List[Dict]:
        """列出可用音色"""
        voices = []
        for name, info in PIPER_MODELS.items():
            model_path = self._models_dir / f"{name}.onnx"
            voices.append({
                "name": name,
                "language": info["language"],
                "quality": info["quality"],
                "downloaded": model_path.exists()
            })
        return voices

    def get_available_voices(self) -> List[str]:
        """获取已下载的音色列表"""
        return [
            name for name, info in PIPER_MODELS.items()
            if (self._models_dir / f"{name}.onnx").exists()
        ]


# 全局引擎实例
_local_engine: Optional[LocalTTSEngine] = None


def get_local_tts_engine() -> LocalTTSEngine:
    """获取本地 TTS 引擎实例"""
    global _local_engine
    if _local_engine is None:
        _local_engine = LocalTTSEngine()
    return _local_engine


# 常用中文音色别名
LOCAL_CHINESE_VOICES = {
    "huayan": "zh_CN-huayan",  # 华燕 - 女声
}

# 常用英文音色别名
LOCAL_ENGLISH_VOICES = {
    "lessac": "en_US-lessac",  # Lessac - 女声，自然
    "amy": "en_US-amy",        # Amy - 女声
}