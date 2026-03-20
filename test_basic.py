"""
Voice Studio 基础功能测试
"""
import sys
from pathlib import Path

# 添加 src 到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


def test_config():
    """测试配置模块"""
    from voice_studio.config import settings
    print("✓ 配置模块正常")
    print(f"  数据目录: {settings.data_dir}")
    print(f"  输出目录: {settings.output_dir}")


def test_tts():
    """测试 TTS 模块"""
    import asyncio
    from voice_studio.tts import get_tts_engine, CHINESE_VOICES
    from voice_studio.config import settings

    print("✓ TTS 模块正常")
    print(f"  预设音色数: {len(CHINESE_VOICES)}")

    # 测试语音合成
    async def synthesize():
        engine = get_tts_engine()
        output = str(settings.output_dir / "test_hello.mp3")
        await engine.synthesize(
            text="你好，这是 Voice Studio 测试语音。",
            output_path=output
        )
        return output

    output_path = asyncio.run(synthesize())
    print(f"  测试语音已生成: {output_path}")


def test_stt():
    """测试 STT 模块"""
    try:
        import torch
        from voice_studio.stt import get_stt_engine
        print("✓ STT 模块正常")
        print(f"  PyTorch 版本: {torch.__version__}")
    except Exception as e:
        print(f"✗ STT 模块加载失败: {e}")
        print("  请确保已正确安装 PyTorch")


def test_api():
    """测试 API 模块"""
    from voice_studio.api import app
    print("✓ API 模块正常")
    print(f"  路由数量: {len(app.routes)}")


def main():
    print("=" * 50)
    print("Voice Studio 功能测试")
    print("=" * 50)

    test_config()
    test_tts()
    test_stt()
    test_api()

    print("=" * 50)
    print("测试完成")


if __name__ == "__main__":
    main()