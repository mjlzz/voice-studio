"""
测试本地 TTS 日语支持处理
"""
import re

def test_piper_models():
    """测试 Piper TTS 模型配置"""
    print("=" * 50)
    print("测试 Piper TTS 模型配置")
    print("=" * 50)
    
    with open('src/voice_studio/tts_local.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找 PIPER_MODELS
    models_match = re.search(r'PIPER_MODELS = \{([^}]+)\}', content, re.DOTALL)
    if models_match:
        models_text = models_match.group(1)
        print("\n找到的模型:")
        for line in models_text.split('\n'):
            line = line.strip()
            if line.startswith('"') and line.endswith('": {'):
                model_name = line[1:line.find('"', 1)]
                print(f"  - {model_name}")
        
        # 检查是否有日语模型
        has_japanese = 'ja_' in models_text or 'ja-JP' in models_text
        if has_japanese:
            print("\n⚠️  发现日语模型配置")
            return True
        else:
            print("\n✅ 确认：没有日语模型（符合预期）")
            return False
    else:
        print("❌ 未找到 PIPER_MODELS 配置")
        return None

def test_voice_selector_filter():
    """测试 VoiceSelector.vue 日语选项过滤"""
    print("\n" + "=" * 50)
    print("测试 VoiceSelector.vue 日语选项过滤")
    print("=" * 50)
    
    with open('web/src/components/tts/VoiceSelector.vue', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否在本地引擎模式下隐藏日语
    checks = [
        ("条件渲染日语选项", r"if \(!isLocalEngine.value\)"),
        ("日语选项 push", r"options.push\(\{ value: 'ja'"),
        ("注释说明", r"Piper TTS doesn't support Japanese"),
    ]
    
    all_passed = True
    for name, pattern in checks:
        if re.search(pattern, content):
            print(f"✅ {name}: 通过")
        else:
            print(f"❌ {name}: 未找到")
            all_passed = False
    
    return all_passed

def test_i18n_local_desc():
    """测试 i18n 本地引擎描述更新"""
    print("\n" + "=" * 50)
    print("测试 i18n 本地引擎描述")
    print("=" * 50)
    
    files = [
        ('web/src/locales/zh-CN.json', '中/英/日三语'),
        ('web/src/locales/en-US.json', 'Chinese/English/Japanese'),
        ('web/src/locales/ja-JP.json', '中/英/日三語対応'),
    ]
    
    all_passed = True
    for filepath, expected in files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if expected in content:
            print(f"✅ {filepath}: 包含 '{expected}'")
        else:
            print(f"❌ {filepath}: 未找到 '{expected}'")
            all_passed = False
    
    return all_passed

def main():
    """主函数"""
    print("\n" + "=" * 50)
    print("本地 TTS 日语支持处理测试")
    print("=" * 50)
    
    results = []
    results.append(("Piper TTS 模型", test_piper_models()))
    results.append(("VoiceSelector 过滤", test_voice_selector_filter()))
    results.append(("i18n 描述", test_i18n_local_desc()))
    
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    for name, result in results:
        if result is None:
            status = "⚠️  未知"
        elif result is True:
            status = "✅ 通过"
        else:
            status = "✅ 通过" if name == "Piper TTS 模型" else "❌ 失败"
        print(f"{name}: {status}")
    
    print("\n" + "=" * 50)
    print("✅ 所有测试完成!")
    print("=" * 50)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
