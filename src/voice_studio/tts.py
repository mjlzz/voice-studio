"""
TTS (Text-to-Speech) 文字转语音引擎
基于 edge-tts 实现 (Microsoft Edge 在线 TTS)
"""
import asyncio
from typing import Optional, List
from pathlib import Path
from dataclasses import dataclass

import edge_tts

from .config import settings


@dataclass
class Voice:
    """语音音色"""
    name: str
    short_name: str
    gender: str
    locale: str
    language: str


class TTSEngine:
    """TTS 引擎 - 基于 edge-tts"""

    _voices_cache: Optional[List[Voice]] = None

    async def synthesize(
        self,
        text: str,
        output_path: str,
        voice: Optional[str] = None,
        rate: str = "+0%",
        volume: str = "+0%"
    ) -> str:
        """
        合成语音

        Args:
            text: 要合成的文本
            output_path: 输出文件路径
            voice: 音色名称 (默认使用配置中的 default_voice)
            rate: 语速调节 (-50% to +100%)
            volume: 音量调节 (-50% to +100%)

        Returns:
            str: 输出文件路径
        """
        voice_name = voice or settings.default_voice

        communicate = edge_tts.Communicate(
            text,
            voice_name,
            rate=rate,
            volume=volume
        )

        await communicate.save(output_path)
        return output_path

    async def list_voices(self, language: Optional[str] = None) -> List[Voice]:
        """
        获取可用的音色列表

        Args:
            language: 筛选语言 (如 "zh", "en")

        Returns:
            List[Voice]: 音色列表
        """
        if self._voices_cache is None:
            voices_data = await edge_tts.list_voices()
            self._voices_cache = [
                Voice(
                    name=v["Name"],
                    short_name=v["ShortName"],
                    gender=v["Gender"],
                    locale=v["Locale"],
                    language=v["Locale"].split("-")[0]
                )
                for v in voices_data
            ]

        if language:
            return [v for v in self._voices_cache if v.language == language]

        return self._voices_cache

    def get_chinese_voices(self) -> List[Voice]:
        """获取中文音色列表 (同步版本)"""
        return asyncio.run(self.list_voices("zh"))


# 全局引擎实例
_engine: Optional[TTSEngine] = None


def get_tts_engine() -> TTSEngine:
    """获取 TTS 引擎实例"""
    global _engine
    if _engine is None:
        _engine = TTSEngine()
    return _engine


# 常用中文音色
CHINESE_VOICES = {
    "xiaoxiao": "zh-CN-XiaoxiaoNeural",      # 晓晓 - 女声，自然
    "yunxi": "zh-CN-YunxiNeural",            # 云希 - 男声，年轻
    "yunjian": "zh-CN-YunjianNeural",        # 云健 - 男声，新闻播报
    "xiaoyi": "zh-CN-XiaoyiNeural",          # 晓伊 - 女声，温柔
    "yunxia": "zh-CN-YunxiaNeural",          # 云夏 - 男声，童声
    "xiaochen": "zh-CN-XiaochenNeural",      # 晓辰 - 女声，新闻
}

# 常用英文音色
ENGLISH_VOICES = {
    "jenny": "en-US-JennyNeural",            # Jenny - 女声，自然
    "guy": "en-US-GuyNeural",                # Guy - 男声，自然
    "aria": "en-US-AriaNeural",              # Aria - 女声，情感丰富
}