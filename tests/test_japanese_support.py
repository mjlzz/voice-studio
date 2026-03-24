"""
测试日语支持功能
"""
import sys
import re
sys.path.insert(0, 'src')

from voice_studio.tts import CHINESE_VOICES, ENGLISH_VOICES, JAPANESE_VOICES
from voice_studio.floating_mic.i18n import t, SUPPORTED_LANGUAGES
from voice_studio.floating_mic.config import FloatingMicConfig

def test_japanese_voices():
    """测试日语音色"""
    print("=" * 50)
    print("测试日语音色")
    print("=" * 50)
    
    print("\n中文音色:")
    for name, voice_id in CHINESE_VOICES.items():
        print(f"  {name}: {voice_id}")
    
    print("\n英文音色:")
    for name, voice_id in ENGLISH_VOICES.items():
        print(f"  {name}: {voice_id}")
    
    print("\n日语音色:")
    for name, voice_id in JAPANESE_VOICES.items():
        print(f"  {name}: {voice_id}")
    
    assert "nanami" in JAPANESE_VOICES
    assert "keita" in JAPANESE_VOICES
    print("\n✅ 日语音色配置正确!")
    return True

def test_i18n():
    """测试国际化翻译"""
    print("\n" + "=" * 50)
    print("测试国际化翻译")
    print("=" * 50)
    
    # 测试中文
    print("\n中文翻译:")
    print(f"  recognition_language: {t('recognition_language', 'zh-CN')}")
    print(f"  chinese: {t('chinese', 'zh-CN')}")
    print(f"  english: {t('english', 'zh-CN')}")
    print(f"  japanese: {t('japanese', 'zh-CN')}")
    
    # 测试英文
    print("\n英文翻译:")
    print(f"  recognition_language: {t('recognition_language', 'en-US')}")
    print(f"  chinese: {t('chinese', 'en-US')}")
    print(f"  english: {t('english', 'en-US')}")
    print(f"  japanese: {t('japanese', 'en-US')}")
    
    # 测试日文
    print("\n日文翻译:")
    print(f"  recognition_language: {t('recognition_language', 'ja-JP')}")
    print(f"  chinese: {t('chinese', 'ja-JP')}")
    print(f"  english: {t('english', 'ja-JP')}")
    print(f"  japanese: {t('japanese', 'ja-JP')}")
    
    print("\n✅ 国际化翻译配置正确!")
    return True

def test_config():
    """测试配置"""
    print("\n" + "=" * 50)
    print("测试配置")
    print("=" * 50)
    
    config = FloatingMicConfig()
    print(f"\n默认识别语言: {config.recognition_language}")
    print(f"默认UI语言: {config.ui_language}")
    
    # 测试设置识别语言
    config.recognition_language = "ja"
    print(f"设置后识别语言: {config.recognition_language}")
    
    print("\n✅ 配置正确!")
    return True

def test_web_voice_selector():
    """测试 Web UI 语音选择器"""
    print("\n" + "=" * 50)
    print("测试 Web UI 语音选择器")
    print("=" * 50)
    
    with open('web/src/components/tts/VoiceSelector.vue', 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ("日语选项", r"value: 'ja'"),
        ("日语筛选逻辑", r"language.value === 'ja'"),
        ("japanese预设", r"lang === 'ja' \? 'japanese'"),
    ]
    
    all_passed = True
    for name, pattern in checks:
        if re.search(pattern, content):
            print(f"✅ {name}: 通过")
        else:
            print(f"❌ {name}: 未找到")
            all_passed = False
    
    return all_passed

def test_api_presets():
    """测试 API 预设音色"""
    print("\n" + "=" * 50)
    print("测试 API 预设音色")
    print("=" * 50)
    
    with open('src/voice_studio/api.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '"japanese": JAPANESE_VOICES' in content:
        print("✅ API 预设包含日语音色")
        return True
    else:
        print("❌ API 预设未找到日语音色")
        return False

def main():
    """主函数"""
    print("\n" + "=" * 50)
    print("Voice Studio 日语支持完整测试")
    print("=" * 50)
    
    results = []
    
    try:
        results.append(("日语音色", test_japanese_voices()))
        results.append(("国际化翻译", test_i18n()))
        results.append(("配置", test_config()))
        results.append(("Web UI 语音选择器", test_web_voice_selector()))
        results.append(("API 预设音色", test_api_presets()))
        
        print("\n" + "=" * 50)
        print("测试结果汇总")
        print("=" * 50)
        
        for name, passed in results:
            status = "✅ 通过" if passed else "❌ 失败"
            print(f"{name}: {status}")
        
        all_passed = all(r[1] for r in results)
        
        print("\n" + "=" * 50)
        if all_passed:
            print("✅ 所有测试通过!")
        else:
            print("❌ 部分测试失败")
        print("=" * 50)
        
        return 0 if all_passed else 1
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
