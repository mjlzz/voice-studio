"""
文本转换模块测试
"""
import pytest

from voice_studio.text_converter import convert_chinese_text, get_converter


class TestTextConverter:
    """文本转换测试"""

    def test_traditional_to_simplified(self):
        """测试繁体转简体"""
        text = "繁體中文測試"
        result = convert_chinese_text(text, "t2s")
        assert result == "繁体中文测试"

    def test_simplified_to_traditional(self):
        """测试简体转繁体"""
        text = "简体中文测试"
        result = convert_chinese_text(text, "s2t")
        assert result == "簡體中文測試"

    def test_none_mode(self):
        """测试不转换模式"""
        text = "繁體中文"
        result = convert_chinese_text(text, "none")
        assert result == text

    def test_empty_text(self):
        """测试空文本"""
        assert convert_chinese_text("", "t2s") == ""
        assert convert_chinese_text(None, "t2s") is None

    def test_mixed_text(self):
        """测试混合文本（中文+英文+数字）"""
        text = "這是繁體和English混合123"
        result = convert_chinese_text(text, "t2s")
        assert result == "这是繁体和English混合123"

    def test_converter_cache(self):
        """测试转换器缓存"""
        c1 = get_converter("t2s")
        c2 = get_converter("t2s")
        assert c1 is c2  # 应该是同一个实例

    def test_already_simplified(self):
        """测试已经是简体的文本"""
        text = "已经是简体"
        result = convert_chinese_text(text, "t2s")
        assert result == text

    def test_english_only(self):
        """测试纯英文文本"""
        text = "Hello World"
        result = convert_chinese_text(text, "t2s")
        assert result == text

    def test_special_characters(self):
        """测试特殊字符"""
        text = "繁體！@#￥%"
        result = convert_chinese_text(text, "t2s")
        # opencc 会转换中文标点
        assert "繁体" in result