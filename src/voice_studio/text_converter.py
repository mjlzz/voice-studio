"""
文本转换工具模块
提供繁简转换等功能
"""
from functools import lru_cache
from typing import Optional

import opencc


@lru_cache(maxsize=1)
def get_converter(mode: str = "t2s") -> Optional[opencc.OpenCC]:
    """
    获取转换器实例（单例缓存）

    Args:
        mode: 转换模式
            - "t2s": 繁体转简体
            - "s2t": 简体转繁体
            - "none": 不转换

    Returns:
        OpenCC 转换器实例，mode为"none"时返回None
    """
    if mode == "none":
        return None
    return opencc.OpenCC(mode)


def convert_chinese_text(text: str, mode: str = "t2s") -> str:
    """
    转换中文文本

    Args:
        text: 原始文本
        mode: 转换模式
            - "t2s": 繁体转简体（默认）
            - "s2t": 简体转繁体
            - "none": 不转换

    Returns:
        转换后的文本
    """
    if not text or mode == "none":
        return text

    converter = get_converter(mode)
    if converter is None:
        return text

    return converter.convert(text)