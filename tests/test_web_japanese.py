"""
测试 Web UI 日语支持
"""
import re

def test_voice_selector_vue():
    """测试 VoiceSelector.vue 是否包含日语支持"""
    print("=" * 50)
    print("测试 VoiceSelector.vue 日语支持")
    print("=" * 50)
    
    with open('web/src/components/tts/VoiceSelector.vue', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查语言选项
    checks = [
        ("日语选项", r"value: 'ja'"),
        ("日文标签", r"'日文'|Japanese"),
        ("日语筛选逻辑", r"language.value === 'ja'"),
        ("japanese预设", r"lang === 'ja' \? 'japanese'"),
    ]
    
    for name, pattern in checks:
        if re.search(pattern, content):
            print(f"✅ {name}: 通过")
        else:
            print(f"❌ {name}: 未找到 (模式: {pattern})")
            return False
    
    return True

def test_api_japanese_voices():
    """测试 API 是否返回日语音色"""
    print("\n" + "=" * 50)
    print("测试 API 日语音色")
    print("=" * 50)
    
    with open('src/voice_studio/api.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ("JAPANESE_VOICES 导入", r"JAPANESE_VOICES"),
        ("japanese 键", r'"japanese": JAPANESE_VOICES'),
    ]
    
    for name, pattern in checks:
        if re.search(pattern, content):
            print(f"✅ {name}: 通过")
        else:
            print(f"❌ {name}: 未找到 (模式: {pattern})")
            return False
    
    return True

def main():
    """主函数"""
    print("\n" + "=" * 50)
    print("Voice Studio Web UI 日语支持测试")
    print("=" * 50)
    
    results = []
    results.append(("VoiceSelector.vue", test_voice_selector_vue()))
    results.append(("API 日语音色", test_api_japanese_voices()))
    
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

if __name__ == "__main__":
    import sys
    sys.exit(main())
